# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Formula calculation engine for payroll processing.

This module provides a secure engine for executing JSON-based calculation rules
for perceptions, deductions, taxes, and other payroll calculations. The engine
is country-agnostic and allows complex rule definitions through a structured
JSON schema.

NOTE: Only Percepciones (income) and Deducciones affect the employee's net pay.
Prestaciones are employer costs that do NOT affect employee pay.

The engine supports:
- Variable definitions (inputs from database, static parameters)
- Mathematical calculations with safe expression evaluation using AST
- Conditional logic (if/else)
- Tax/rate table lookups with progressive rates
- Accumulated annual calculations
"""

from __future__ import annotations

import ast
import operator
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from coati_payroll.enums import StepType
from coati_payroll.i18n import _
from coati_payroll.log import TRACE_LEVEL_NUM, is_trace_enabled, log


# Safe operators for expression evaluation
SAFE_OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
}

# Safe comparison operators
COMPARISON_OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

# Safe functions for calculations
SAFE_FUNCTIONS = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
}


class FormulaEngineError(Exception):
    """Base exception for formula engine errors.

    Python 3.11+ enhancement: Supports exception notes via add_note() method.
    """

    pass


# Alias for backward compatibility
TaxEngineError = FormulaEngineError


class ValidationError(FormulaEngineError):
    """Exception for validation errors in schema or data.

    Python 3.11+ enhancement: Can use add_note() to append contextual information.
    """

    pass


class CalculationError(FormulaEngineError):
    """Exception for calculation errors during execution.

    Python 3.11+ enhancement: Supports add_note() for additional context.
    """

    pass


def to_decimal(value: Any) -> Decimal:
    """Safely convert a value to Decimal.

    Args:
        value: Value to convert (int, float, str, Decimal, bool)

    Returns:
        Decimal representation of the value

    Raises:
        ValidationError: If value cannot be converted to Decimal
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    # Handle boolean values explicitly (True -> 1, False -> 0)
    # Must check before int/str conversion since bool is a subclass of int
    if isinstance(value, bool):
        return Decimal("1") if value else Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(f"Cannot convert '{value}' to Decimal: {e}") from e


def safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Safely divide two decimals, handling division by zero.

    Args:
        numerator: The dividend
        denominator: The divisor

    Returns:
        Result of division or 0 if denominator is 0
    """
    if denominator == 0:
        return Decimal("0")
    return numerator / denominator


class FormulaEngine:
    """Engine for executing JSON-based calculation rules for payroll.

    This engine provides a secure way to execute complex calculations for
    perceptions, deductions, taxes, and other payroll formulas defined in
    JSON format. It supports variables, formulas, conditionals, and rate
    table lookups.

    NOTE: Only Percepciones and Deducciones affect employee net pay.
    Prestaciones are employer costs calculated separately.

    Example schema structure:
    {
        "meta": {
            "name": "IR Nicaragua",
            "jurisdiction": "Nicaragua",
            "reference_currency": "NIO",
            "version": "1.0.0"
        },
        "inputs": [
            {"name": "salario_bruto", "type": "decimal", "source": "empleado.salario_base"},
            {"name": "meses_trabajados", "type": "integer", "default": 12}
        ],
        "steps": [
            {
                "name": "calculate_annual",
                "type": "calculation",
                "formula": "salario_bruto * meses_trabajados"
            },
            {
                "name": "tax_lookup",
                "type": "tax_lookup",
                "table": "tabla_ir",
                "input": "calculate_annual",
                "output": "impuesto_anual"
            }
        ],
        "tax_tables": {
            "tabla_ir": [
                {"min": 0, "max": 100000, "rate": 0, "fixed": 0, "over": 0},
                {"min": 100001, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000}
            ]
        },
        "output": "impuesto_mensual"
    }
    """

    def __init__(self, schema: dict[str, Any]):
        """Initialize the formula engine with a calculation schema.

        Args:
            schema: JSON schema defining the calculation rules

        Raises:
            ValidationError: If schema is invalid
        """
        self.schema = schema
        self.variables: dict[str, Decimal] = {}
        self.results: dict[str, Any] = {}
        self._validate_schema()

    # ------------------------------------------------------------------
    # Trace helper uses cached check from log.is_trace_enabled() to avoid
    # recomputing debug/level state on every call.
    # ------------------------------------------------------------------
    def _trace(self, message: str) -> None:
        if is_trace_enabled():
            try:
                log.log(TRACE_LEVEL_NUM, message)
            except Exception:
                pass

    def _validate_schema(self) -> None:
        """Validate the calculation schema structure.

        Raises:
            ValidationError: If schema is missing required fields
        """
        if not isinstance(self.schema, dict):
            raise ValidationError("Schema must be a dictionary")

        # Check for required sections
        if "steps" not in self.schema:
            raise ValidationError("Schema must contain 'steps' section")

        # Validate steps structure
        for i, step in enumerate(self.schema.get("steps", [])):
            if not isinstance(step, dict):
                raise ValidationError(f"Step {i} must be a dictionary")
            if "name" not in step:
                raise ValidationError(f"Step {i} must have a 'name' field")
            if "type" not in step:
                raise ValidationError(f"Step {i} must have a 'type' field")

    def _evaluate_expression(self, expression: str) -> Decimal:
        """Safely evaluate a mathematical expression using AST.

        This method parses and evaluates arithmetic expressions using Python's
        Abstract Syntax Tree (AST) to ensure correct operator precedence and
        security.

        Args:
            expression: Mathematical expression string

        Returns:
            Result of the expression as Decimal

        Raises:
            CalculationError: If expression is invalid or unsafe
        """
        if not expression or not isinstance(expression, str):
            return Decimal("0")

        expression = expression.strip()
        if not expression:
            return Decimal("0")

        self._trace(_("Evaluando expresión: '%(expr)s'") % {"expr": expression})

        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode="eval")
            # Validate that the AST only contains safe operations
            self._validate_ast_security(tree.body)
            # Evaluate the AST
            result = self._eval_ast_node(tree.body)
            final_result = to_decimal(result)
            self._trace(_("Resultado expresión '%(expr)s' => %(res)s") % {"expr": expression, "res": final_result})
            return final_result
        except SyntaxError as e:
            raise CalculationError(f"Invalid expression syntax: {e}") from e
        except ZeroDivisionError:
            return Decimal("0")
        except Exception as e:
            raise CalculationError(f"Error evaluating expression '{expression}': {e}") from e

    def _validate_ast_security(self, node: ast.AST) -> None:
        """Validate that an AST node only contains safe operations.

        This prevents code injection by ensuring only mathematical operations
        and safe function calls are present.

        Args:
            node: AST node to validate

        Raises:
            CalculationError: If unsafe operations are detected
        """
        # Define allowed node types
        allowed_types = (
            ast.Expression,
            ast.Constant,
            ast.Name,
            ast.Load,
            ast.BinOp,
            ast.UnaryOp,
            ast.Call,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.UAdd,
            ast.USub,
        )

        # Validate all nodes in the tree in a single pass
        for child in ast.walk(node):
            if not isinstance(child, allowed_types):
                raise CalculationError(
                    f"Unsafe operation detected: {child.__class__.__name__}. "
                    "Only basic arithmetic and safe functions are allowed."
                )
            # Validate function calls
            if isinstance(child, ast.Call):
                if not isinstance(child.func, ast.Name):
                    raise CalculationError("Only named functions are allowed")
                if child.func.id not in SAFE_FUNCTIONS:
                    raise CalculationError(
                        f"Function '{child.func.id}' is not allowed. "
                        f"Allowed functions: {', '.join(SAFE_FUNCTIONS.keys())}"
                    )

    def _eval_ast_node(self, node: ast.AST) -> Decimal:
        """Evaluate an AST node recursively.

        Args:
            node: AST node to evaluate

        Returns:
            Decimal result of the evaluation

        Raises:
            CalculationError: If evaluation fails
        """
        if isinstance(node, ast.Constant):
            # Python 3.8+ uses ast.Constant for literals
            return to_decimal(node.value)

        if isinstance(node, ast.Name):
            # Variable reference
            var_name = node.id
            if var_name not in self.variables:
                raise CalculationError(f"Undefined variable: {var_name}")
            return self.variables[var_name]

        if isinstance(node, ast.BinOp):
            return self._eval_binary_op(node)

        if isinstance(node, ast.UnaryOp):
            return self._eval_unary_op(node)

        if isinstance(node, ast.Call):
            return self._eval_function_call(node)

        raise CalculationError(f"Unsupported AST node type: {type(node).__name__}")

    def _eval_binary_op(self, node: ast.BinOp) -> Decimal:
        """Evaluate a binary operation node.

        Args:
            node: Binary operation AST node

        Returns:
            Result as Decimal
        """
        left = self._eval_ast_node(node.left)
        right = self._eval_ast_node(node.right)

        op_type = type(node.op)
        if op_type == ast.Add:
            return to_decimal(left + right)
        if op_type == ast.Sub:
            return to_decimal(left - right)
        if op_type == ast.Mult:
            return to_decimal(left * right)
        if op_type == ast.Div:
            if right == 0:
                return Decimal("0")  # Safe division by zero handling
            return to_decimal(left / right)
        if op_type == ast.FloorDiv:
            if right == 0:
                return Decimal("0")
            return to_decimal(left // right)
        if op_type == ast.Mod:
            if right == 0:
                return Decimal("0")
            return to_decimal(left % right)
        if op_type == ast.Pow:
            return to_decimal(left**right)

        raise CalculationError(f"Unsupported binary operator: {op_type.__name__}")

    def _eval_unary_op(self, node: ast.UnaryOp) -> Decimal:
        """Evaluate a unary operation node.

        Args:
            node: Unary operation AST node

        Returns:
            Result as Decimal
        """
        operand = self._eval_ast_node(node.operand)

        op_type = type(node.op)
        if op_type == ast.UAdd:
            return to_decimal(+operand)
        if op_type == ast.USub:
            return to_decimal(-operand)

        raise CalculationError(f"Unsupported unary operator: {op_type.__name__}")

    def _eval_function_call(self, node: ast.Call) -> Decimal:
        """Evaluate a function call node.

        Args:
            node: Function call AST node

        Returns:
            Result as Decimal
        """
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise CalculationError(f"Function '{func_name}' is not allowed")

        # Evaluate arguments
        args = [self._eval_ast_node(arg) for arg in node.args]

        # Call the safe function and maintain Decimal precision
        try:
            # Special handling for round() which needs an integer as second argument
            if func_name == "round" and len(args) > 1:
                result = SAFE_FUNCTIONS[func_name](args[0], int(args[1]))
            else:
                result = SAFE_FUNCTIONS[func_name](*args)
            return to_decimal(result)
        except Exception as e:
            raise CalculationError(f"Error calling {func_name}: {e}") from e

    def _evaluate_condition(self, condition: dict[str, Any]) -> bool:
        """Evaluate a conditional expression.

        Args:
            condition: Dictionary with 'left', 'operator', 'right' keys

        Returns:
            Boolean result of the condition

        Raises:
            CalculationError: If condition is invalid
        """
        if not isinstance(condition, dict):
            raise CalculationError("Condition must be a dictionary")

        left = condition.get("left")
        op = condition.get("operator")
        right = condition.get("right")

        if op not in COMPARISON_OPERATORS:
            raise CalculationError(f"Invalid comparison operator: {op}")

        # Resolve variable references
        left_val = self._resolve_value(left)
        right_val = self._resolve_value(right)
        result = COMPARISON_OPERATORS[op](left_val, right_val)
        self._trace(
            _("Condición evaluada: %(left)s %(op)s %(right)s -> %(res)s")
            % {"left": left_val, "op": op, "right": right_val, "res": result}
        )
        return result

    def _resolve_value(self, value: Any) -> Decimal:
        """Resolve a value that might be a variable reference.

        Args:
            value: Value or variable name to resolve

        Returns:
            Decimal value
        """
        if isinstance(value, str) and value in self.variables:
            resolved = self.variables[value]
            self._trace(_("Resolviendo variable '%(name)s' => %(value)s") % {"name": value, "value": resolved})
            return resolved

        resolved_literal = to_decimal(value)
        self._trace(_("Resolviendo valor literal '%(raw)s' => %(value)s") % {"raw": value, "value": resolved_literal})
        return resolved_literal

    def _lookup_tax_table(
        self,
        table_name: str,
        input_value: Decimal,
    ) -> dict[str, Decimal]:
        """Look up tax bracket in a tax table.

        Args:
            table_name: Name of the tax table in schema
            input_value: Value to look up in the table

        Returns:
            Dictionary with 'tax', 'rate', 'fixed', 'over' values

        Raises:
            CalculationError: If table not found or lookup fails
        """
        tax_tables = self.schema.get("tax_tables", {})
        if table_name not in tax_tables:
            raise CalculationError(f"Tax table '{table_name}' not found")

        table = tax_tables[table_name]
        if not isinstance(table, list):
            raise CalculationError(f"Tax table '{table_name}' must be a list")

        self._trace(
            _("Buscando tabla de impuestos '%(table)s' con valor %(value)s; brackets=%(count)s")
            % {"table": table_name, "value": input_value, "count": len(table)}
        )

        # Find the applicable bracket
        for bracket in table:
            min_val = to_decimal(bracket.get("min", 0))
            max_val = bracket.get("max")

            if max_val is None:
                # Open-ended bracket (highest tier)
                if input_value >= min_val:
                    result = self._calculate_bracket_tax(bracket, input_value)
                    self._trace(
                        _("Aplicando tramo abierto desde %(min)s para valor %(value)s -> %(result)s")
                        % {"min": min_val, "value": input_value, "result": result}
                    )
                    return result
            else:
                max_val = to_decimal(max_val)
                if min_val <= input_value <= max_val:
                    result = self._calculate_bracket_tax(bracket, input_value)
                    self._trace(
                        _("Aplicando tramo %(min)s - %(max)s para valor %(value)s -> %(result)s")
                        % {"min": min_val, "max": max_val, "value": input_value, "result": result}
                    )
                    return result

        # If no bracket found, return zeros
        self._trace(
            _("No se encontró tramo para valor %(value)s en tabla '%(table)s', devolviendo ceros")
            % {"value": input_value, "table": table_name}
        )
        return {
            "tax": Decimal("0"),
            "rate": Decimal("0"),
            "fixed": Decimal("0"),
            "over": Decimal("0"),
        }

    def _calculate_bracket_tax(
        self,
        bracket: dict[str, Any],
        input_value: Decimal,
    ) -> dict[str, Decimal]:
        """Calculate tax for a specific bracket.

        Args:
            bracket: Tax bracket definition
            input_value: Value being taxed

        Returns:
            Dictionary with calculated tax components
        """
        rate = to_decimal(bracket.get("rate", 0))
        fixed = to_decimal(bracket.get("fixed", 0))
        over = to_decimal(bracket.get("over", 0))

        # Calculate tax: fixed + (input_value - over) * rate
        excess = max(input_value - over, Decimal("0"))
        tax = fixed + (excess * rate)

        result = {
            "tax": tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "rate": rate,
            "fixed": fixed,
            "over": over,
        }

        self._trace(
            _("Cálculo de tramo: rate=%(rate)s fixed=%(fixed)s over=%(over)s valor=%(value)s -> %(result)s")
            % {"rate": rate, "fixed": fixed, "over": over, "value": input_value, "result": result}
        )
        return result

    def _execute_step(self, step: dict[str, Any]) -> Any:
        """Execute a single calculation step.

        Args:
            step: Step definition dictionary

        Returns:
            Result of the step execution

        Raises:
            CalculationError: If step execution fails
        """
        step_type = step.get("type")
        step_name = step.get("name")

        self._trace(
            _("Ejecutando paso '%(name)s' tipo=%(type)s variables_disponibles=%(vars)s")
            % {
                "name": step_name,
                "type": step_type,
                "vars": list(self.variables.keys()),
            }
        )

        match step_type:
            case StepType.CALCULATION:
                formula = step.get("formula", "")
                self._trace(
                    _("Paso cálculo '%(name)s': formula='%(formula)s'") % {"name": step_name, "formula": formula}
                )
                result = self._evaluate_expression(formula)
                self.variables[step_name] = result
                self.results[step_name] = result
                self._trace(_("Resultado paso '%(name)s' => %(result)s") % {"name": step_name, "result": result})
                return result

            case StepType.CONDITIONAL:
                condition = step.get("condition", {})
                if_true = step.get("if_true", "0")
                if_false = step.get("if_false", "0")

                condition_result = self._evaluate_condition(condition)
                selected_value = if_true if condition_result else if_false
                result = self._evaluate_expression(str(selected_value))

                self.variables[step_name] = result
                self.results[step_name] = result
                self._trace(
                    _("Paso condicional '%(name)s': condición=%(cond)s -> %(cond_res)s; valor=%(value)s")
                    % {
                        "name": step_name,
                        "cond": condition,
                        "cond_res": condition_result,
                        "value": result,
                    }
                )
                return result

            case StepType.TAX_LOOKUP:
                table_name = step.get("table", "")
                input_var = step.get("input", "")
                input_value = self.variables.get(input_var, Decimal("0"))

                self._trace(
                    _("Paso tax_lookup '%(name)s': tabla=%(table)s input_var=%(input)s valor=%(value)s")
                    % {
                        "name": step_name,
                        "table": table_name,
                        "input": input_var,
                        "value": input_value,
                    }
                )
                tax_result = self._lookup_tax_table(table_name, input_value)
                self.variables[step_name] = tax_result["tax"]
                self.results[step_name] = tax_result
                self._trace(
                    _("Resultado tax_lookup '%(name)s' => %(result)s") % {"name": step_name, "result": tax_result}
                )
                return tax_result

            case StepType.ASSIGNMENT:
                value = step.get("value")
                result = self._resolve_value(value)
                self.variables[step_name] = result
                self.results[step_name] = result
                self._trace(
                    _("Paso asignación '%(name)s': valor=%(value)s resuelto=%(result)s")
                    % {"name": step_name, "value": value, "result": result}
                )
                return result

            case _:
                raise CalculationError(f"Unknown step type: {step_type}")

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute the calculation schema with provided inputs.

        Args:
            inputs: Dictionary of input values

        Returns:
            Dictionary containing all results and the final output

        Raises:
            CalculationError: If execution fails
        """
        # Reset state
        self.variables = {}
        self.results = {}

        meta = self.schema.get("meta", {})
        self._trace(
            _("Iniciando ejecución de esquema '%(name)s' pasos=%(count)s")
            % {"name": meta.get("name", "sin nombre"), "count": len(self.schema.get("steps", []))}
        )

        # Load input definitions and set values
        for input_def in self.schema.get("inputs", []):
            name = input_def.get("name")
            default = input_def.get("default", 0)

            # Use provided input or default
            if name in inputs:
                self.variables[name] = to_decimal(inputs[name])
            else:
                self.variables[name] = to_decimal(default)

            source = "input" if name in inputs else "default"
            self._trace(
                _("Input '%(name)s' cargado desde %(source)s => %(value)s")
                % {"name": name, "source": source, "value": self.variables[name]}
            )

        # Execute each step in order
        for step in self.schema.get("steps", []):
            try:
                self._execute_step(step)
            except Exception as e:
                step_name = step.get("name", "unknown")
                step_type = step.get("type", "unknown")
                error = CalculationError(f"Error in step '{step_name}': {e}")
                # Python 3.11+ feature: add_note() for additional context
                error.add_note(f"Step type: {step_type}")
                error.add_note(f"Available variables: {list(self.variables.keys())}")
                raise error from e

        # Get the final output
        output_name = self.schema.get("output", "")
        final_result = self.variables.get(output_name, Decimal("0"))

        self._trace(_("Resultado final '%(name)s' => %(value)s") % {"name": output_name, "value": final_result})

        return {
            "variables": {k: float(v) for k, v in self.variables.items()},
            "results": {
                k: (
                    float(v)
                    if isinstance(v, Decimal)
                    else ({kk: float(vv) for kk, vv in v.items()} if isinstance(v, dict) else v)
                )
                for k, v in self.results.items()
            },
            "output": float(final_result),
        }


def calculate_with_rule(
    rule_schema: dict[str, Any],
    employee_data: dict[str, Any],
    accumulated_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate using a rule schema with employee and accumulated data.

    This is a convenience function that combines employee data with
    accumulated annual data for payroll calculations.

    Args:
        rule_schema: The JSON calculation schema
        employee_data: Employee-specific data (salary, etc.)
        accumulated_data: Optional accumulated annual data

    Returns:
        Calculation results including the final output
    """
    inputs = {**employee_data}

    if accumulated_data:
        # Add accumulated values with prefix
        for key, value in accumulated_data.items():
            inputs[f"acumulado_{key}"] = value

    engine = FormulaEngine(rule_schema)
    return engine.execute(inputs)


# Alias for backward compatibility
TaxEngine = FormulaEngine


# Example Nicaragua IR schema for reference
EXAMPLE_IR_NICARAGUA_SCHEMA = {
    "meta": {
        "name": "IR Laboral Nicaragua",
        "jurisdiction": "Nicaragua",
        "reference_currency": "NIO",
        "version": "1.0.0",
        "description": "Cálculo del Impuesto sobre la Renta para salarios en Nicaragua. "
        "La moneda de referencia es NIO. El tipo de cambio se aplica si la planilla "
        "está en una moneda diferente.",
    },
    "inputs": [
        {
            "name": "salario_mensual",
            "type": "decimal",
            "source": "empleado.salario_base",
            "description": "Salario mensual bruto",
        },
        {
            "name": "inss_laboral",
            "type": "decimal",
            "source": "calculated",
            "description": "Deducción INSS laboral",
        },
        {
            "name": "meses_restantes",
            "type": "integer",
            "default": 12,
            "description": "Meses restantes en el año fiscal",
        },
        {
            "name": "salario_acumulado",
            "type": "decimal",
            "default": 0,
            "description": "Salario bruto acumulado del año",
        },
        {
            "name": "ir_retenido_acumulado",
            "type": "decimal",
            "default": 0,
            "description": "IR ya retenido en el año",
        },
    ],
    "steps": [
        {
            "name": "salario_neto_mensual",
            "type": "calculation",
            "formula": "salario_mensual - inss_laboral",
            "description": "Salario después de INSS",
        },
        {
            "name": "expectativa_anual",
            "type": "calculation",
            "formula": "salario_neto_mensual * meses_restantes",
            "description": "Proyección de salario restante del año",
        },
        {
            "name": "base_imponible_anual",
            "type": "calculation",
            "formula": "salario_acumulado + expectativa_anual",
            "description": "Base imponible anual total",
        },
        {
            "name": "ir_anual",
            "type": "tax_lookup",
            "table": "tabla_ir_nicaragua",
            "input": "base_imponible_anual",
            "description": "Cálculo IR anual según tabla",
        },
        {
            "name": "ir_pendiente",
            "type": "calculation",
            "formula": "ir_anual - ir_retenido_acumulado",
            "description": "IR pendiente de retener",
        },
        {
            "name": "ir_mensual",
            "type": "calculation",
            "formula": "ir_pendiente / meses_restantes",
            "description": "IR a retener este mes",
        },
    ],
    "tax_tables": {
        "tabla_ir_nicaragua": [
            {"min": 0, "max": 100000, "rate": 0, "fixed": 0, "over": 0},
            {"min": 100000.01, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000},
            {
                "min": 200000.01,
                "max": 350000,
                "rate": 0.20,
                "fixed": 15000,
                "over": 200000,
            },
            {
                "min": 350000.01,
                "max": 500000,
                "rate": 0.25,
                "fixed": 45000,
                "over": 350000,
            },
            {
                "min": 500000.01,
                "max": None,
                "rate": 0.30,
                "fixed": 82500,
                "over": 500000,
            },
        ]
    },
    "output": "ir_mensual",
}


# Available data sources for tax rule inputs
# These define what fields can be accessed from the database when creating rules
AVAILABLE_DATA_SOURCES = {
    "empleado": {
        "label": "Empleado",
        "description": "Datos del registro de empleado",
        "fields": {
            # Identificación
            "primer_nombre": {
                "type": "string",
                "label": "Primer Nombre",
                "description": "Primer nombre del empleado",
            },
            "segundo_nombre": {
                "type": "string",
                "label": "Segundo Nombre",
                "description": "Segundo nombre del empleado",
            },
            "primer_apellido": {
                "type": "string",
                "label": "Primer Apellido",
                "description": "Primer apellido del empleado",
            },
            "segundo_apellido": {
                "type": "string",
                "label": "Segundo Apellido",
                "description": "Segundo apellido del empleado",
            },
            "identificacion_personal": {
                "type": "string",
                "label": "Identificación Personal",
                "description": "Número de cédula o documento de identidad",
            },
            "id_seguridad_social": {
                "type": "string",
                "label": "ID Seguridad Social",
                "description": "Número de seguro social (INSS)",
            },
            "id_fiscal": {
                "type": "string",
                "label": "ID Fiscal",
                "description": "Número de identificación fiscal (RUC/NIT)",
            },
            "genero": {
                "type": "string",
                "label": "Género",
                "description": "Género del empleado",
            },
            "nacionalidad": {
                "type": "string",
                "label": "Nacionalidad",
                "description": "Nacionalidad del empleado",
            },
            "estado_civil": {
                "type": "string",
                "label": "Estado Civil",
                "description": "Estado civil del empleado",
            },
            # Fechas
            "fecha_nacimiento": {
                "type": "date",
                "label": "Fecha de Nacimiento",
                "description": "Fecha de nacimiento del empleado",
            },
            "fecha_alta": {
                "type": "date",
                "label": "Fecha de Ingreso",
                "description": "Fecha de inicio de labores del empleado",
            },
            "fecha_baja": {
                "type": "date",
                "label": "Fecha de Baja",
                "description": "Fecha de terminación de labores",
            },
            "fecha_ultimo_aumento": {
                "type": "date",
                "label": "Fecha Último Aumento",
                "description": "Fecha del último aumento de salario",
            },
            # Información laboral
            "cargo": {
                "type": "string",
                "label": "Cargo",
                "description": "Cargo o puesto del empleado",
            },
            "area": {
                "type": "string",
                "label": "Área",
                "description": "Área o departamento del empleado",
            },
            "centro_costos": {
                "type": "string",
                "label": "Centro de Costos",
                "description": "Centro de costos asignado al empleado",
            },
            "tipo_contrato": {
                "type": "string",
                "label": "Tipo de Contrato",
                "description": "Tipo de contrato (indefinido, temporal, etc.)",
            },
            "activo": {
                "type": "boolean",
                "label": "Empleado Activo",
                "description": "Indica si el empleado está activo",
            },
            # Salario y compensación
            "salario_base": {
                "type": "decimal",
                "label": "Salario Base",
                "description": "Salario mensual base del empleado",
            },
            # Datos bancarios
            "banco": {
                "type": "string",
                "label": "Banco",
                "description": "Nombre del banco para depósito",
            },
            "numero_cuenta_bancaria": {
                "type": "string",
                "label": "Número de Cuenta Bancaria",
                "description": "Número de cuenta para depósito de nómina",
            },
            # Implementation initial fields - for when system starts mid-fiscal-year
            "anio_implementacion_inicial": {
                "type": "integer",
                "label": "Año de Implementación Inicial",
                "description": "Año fiscal cuando se implementó el sistema",
            },
            "mes_ultimo_cierre": {
                "type": "integer",
                "label": "Último Mes Cerrado",
                "description": "Último mes cerrado antes de pasar al sistema",
            },
            "salario_acumulado": {
                "type": "decimal",
                "label": "Salario Acumulado (Implementación)",
                "description": "Suma de salarios del año fiscal antes del sistema",
            },
            "impuesto_acumulado": {
                "type": "decimal",
                "label": "Impuesto Acumulado (Implementación)",
                "description": "Suma de impuestos pagados antes del sistema",
            },
            "ultimos_tres_salarios": {
                "type": "json",
                "label": "Últimos Tres Salarios",
                "description": "JSON con los últimos 3 salarios mensuales previos",
            },
            # Datos adicionales (campos personalizados)
            "datos_adicionales": {
                "type": "json",
                "label": "Datos Adicionales",
                "description": "Campos personalizados definidos para el empleado",
            },
        },
    },
    "nomina": {
        "label": "Nómina / Cálculo",
        "description": "Datos del período de nómina actual",
        "fields": {
            "fecha_calculo": {
                "type": "date",
                "label": "Fecha de Cálculo",
                "description": "Fecha en que se ejecuta/genera la nómina",
            },
            "periodo_inicio": {
                "type": "date",
                "label": "Inicio del Período",
                "description": "Fecha de inicio del período de nómina",
            },
            "periodo_fin": {
                "type": "date",
                "label": "Fin del Período",
                "description": "Fecha de fin del período de nómina",
            },
            "dias_periodo": {
                "type": "integer",
                "label": "Días del Período",
                "description": "Número de días del período de nómina",
            },
            "mes_nomina": {
                "type": "integer",
                "label": "Mes de Nómina",
                "description": "Mes del período de nómina (1-12)",
            },
            "anio_nomina": {
                "type": "integer",
                "label": "Año de Nómina",
                "description": "Año del período de nómina",
            },
            "numero_periodo": {
                "type": "integer",
                "label": "Número de Período",
                "description": "Número de período en el año fiscal (1, 2, 3...)",
            },
            "es_ultimo_periodo_anual": {
                "type": "boolean",
                "label": "Es Último Período del Año",
                "description": "Indica si es el último período del año fiscal",
            },
        },
    },
    "tipo_planilla": {
        "label": "Tipo de Planilla",
        "description": "Configuración del tipo de planilla",
        "fields": {
            "codigo": {
                "type": "string",
                "label": "Código",
                "description": "Código del tipo de planilla",
            },
            "periodicidad": {
                "type": "string",
                "label": "Periodicidad",
                "description": "Frecuencia de pago (mensual, quincenal, semanal)",
            },
            "dias": {
                "type": "integer",
                "label": "Días del Período",
                "description": "Días usados para prorrateos",
            },
            "periodos_por_anio": {
                "type": "integer",
                "label": "Períodos por Año",
                "description": "Número de períodos de pago por año fiscal",
            },
            "mes_inicio_fiscal": {
                "type": "integer",
                "label": "Mes Inicio Fiscal",
                "description": "Mes de inicio del período fiscal (1-12)",
            },
            "dia_inicio_fiscal": {
                "type": "integer",
                "label": "Día Inicio Fiscal",
                "description": "Día de inicio del período fiscal",
            },
            "acumula_anual": {
                "type": "boolean",
                "label": "Acumula Anual",
                "description": "Si acumula valores anuales para cálculos",
            },
        },
    },
    "planilla": {
        "label": "Planilla",
        "description": "Datos de la planilla actual",
        "fields": {
            "nombre": {
                "type": "string",
                "label": "Nombre de Planilla",
                "description": "Nombre de la planilla",
            },
            "periodo_fiscal_inicio": {
                "type": "date",
                "label": "Inicio Período Fiscal",
                "description": "Fecha de inicio del período fiscal de la planilla",
            },
            "periodo_fiscal_fin": {
                "type": "date",
                "label": "Fin Período Fiscal",
                "description": "Fecha de fin del período fiscal de la planilla",
            },
            "prioridad_prestamos": {
                "type": "integer",
                "label": "Prioridad Préstamos",
                "description": "Prioridad de deducción de préstamos",
            },
            "prioridad_adelantos": {
                "type": "integer",
                "label": "Prioridad Adelantos",
                "description": "Prioridad de deducción de adelantos",
            },
        },
    },
    "acumulado_anual": {
        "label": "Acumulados del Período Fiscal",
        "description": "Valores acumulados en el año fiscal actual",
        "fields": {
            "salario_bruto_acumulado": {
                "type": "decimal",
                "label": "Salario Bruto Acumulado",
                "description": "Total de salario bruto en el período fiscal",
            },
            "salario_gravable_acumulado": {
                "type": "decimal",
                "label": "Salario Gravable Acumulado",
                "description": "Total de salario gravable en el período fiscal",
            },
            "deducciones_antes_impuesto_acumulado": {
                "type": "decimal",
                "label": "Deducciones Pre-Impuesto Acumuladas",
                "description": "Total de deducciones antes de impuesto",
            },
            "impuesto_retenido_acumulado": {
                "type": "decimal",
                "label": "Impuesto Retenido Acumulado",
                "description": "Total de impuesto retenido en el período",
            },
            "periodos_procesados": {
                "type": "integer",
                "label": "Períodos Procesados",
                "description": "Número de nóminas procesadas en el período fiscal",
            },
            "total_percepciones_acumulado": {
                "type": "decimal",
                "label": "Total Percepciones Acumulado",
                "description": "Total de percepciones en el período fiscal",
            },
            "total_deducciones_acumulado": {
                "type": "decimal",
                "label": "Total Deducciones Acumulado",
                "description": "Total de deducciones en el período fiscal",
            },
            "total_neto_acumulado": {
                "type": "decimal",
                "label": "Total Neto Acumulado",
                "description": "Total neto pagado en el período fiscal",
            },
            "salario_acumulado_mes": {
                "type": "decimal",
                "label": "Salario Acumulado del Mes",
                "description": "Total de salario bruto acumulado en el mes calendario actual.",
            },
        },
    },
    "prestamos_adelantos": {
        "label": "Préstamos y Adelantos (Automático)",
        "description": "Valores calculados automáticamente desde la tabla Adelanto",
        "fields": {
            "total_cuotas_prestamos": {
                "type": "decimal",
                "label": "Total Cuotas de Préstamos",
                "description": "Suma de cuotas de préstamos activos a descontar",
            },
            "total_adelantos_pendientes": {
                "type": "decimal",
                "label": "Total Adelantos Pendientes",
                "description": "Suma de adelantos salariales pendientes",
            },
            "cantidad_prestamos_activos": {
                "type": "integer",
                "label": "Cantidad de Préstamos Activos",
                "description": "Número de préstamos activos del empleado",
            },
            "saldo_total_prestamos": {
                "type": "decimal",
                "label": "Saldo Total de Préstamos",
                "description": "Saldo pendiente total de todos los préstamos",
            },
        },
    },
    "vacaciones": {
        "label": "Vacaciones",
        "description": "Datos de vacaciones del empleado",
        "fields": {
            "dias_vacaciones_acumulados": {
                "type": "decimal",
                "label": "Días de Vacaciones Acumulados",
                "description": "Días de vacaciones acumulados pendientes de disfrutar",
            },
            "dias_vacaciones_tomados": {
                "type": "decimal",
                "label": "Días de Vacaciones Tomados",
                "description": "Días de vacaciones ya disfrutados",
            },
            "dias_vacaciones_disponibles": {
                "type": "decimal",
                "label": "Días de Vacaciones Disponibles",
                "description": "Días de vacaciones disponibles para disfrutar",
            },
            "provision_vacaciones": {
                "type": "decimal",
                "label": "Provisión de Vacaciones",
                "description": "Monto provisionado para vacaciones",
            },
        },
    },
    "novedad": {
        "label": "Novedades del Período",
        "description": "Valores de novedades registradas para el empleado en el período actual",
        "fields": {
            # A. Compensación Base y Directa
            "horas_extra": {
                "type": "decimal",
                "label": "Horas Extraordinarias",
                "description": "Horas trabajadas más allá de la jornada estándar",
                "codigo_concepto": "HORAS_EXTRA",
                "tipo_valor": "horas",
                "gravable": True,
            },
            "horas_extra_dobles": {
                "type": "decimal",
                "label": "Horas Extra Dobles/Festivas",
                "description": "Horas extra en feriados, domingos o nocturnas",
                "codigo_concepto": "HORAS_EXTRA_DOBLES",
                "tipo_valor": "horas",
                "gravable": True,
            },
            "comisiones": {
                "type": "decimal",
                "label": "Comisiones",
                "description": "Porcentaje sobre ventas o negocios concretados",
                "codigo_concepto": "COMISION",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "bono_objetivos": {
                "type": "decimal",
                "label": "Bono por Objetivos",
                "description": "Pago variable por cumplimiento de metas específicas",
                "codigo_concepto": "BONO_OBJETIVOS",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "bono_anual": {
                "type": "decimal",
                "label": "Bono Anual/Trimestral",
                "description": "Compensación discrecional o por resultados generales",
                "codigo_concepto": "BONO_ANUAL",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "plus_peligrosidad": {
                "type": "decimal",
                "label": "Plus por Peligrosidad/Toxicidad",
                "description": "Adicional por trabajar en entornos de riesgo",
                "codigo_concepto": "PLUS_PELIGROSIDAD",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "plus_nocturno": {
                "type": "decimal",
                "label": "Plus por Trabajo Nocturno",
                "description": "Adicional por laborar en horarios nocturnos",
                "codigo_concepto": "PLUS_NOCTURNO",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "plus_antiguedad": {
                "type": "decimal",
                "label": "Plus por Antigüedad",
                "description": "Compensación por años de servicio",
                "codigo_concepto": "PLUS_ANTIGUEDAD",
                "tipo_valor": "monto",
                "gravable": True,
            },
            # B. Compensaciones en Especie y Beneficios
            "uso_vehiculo": {
                "type": "decimal",
                "label": "Uso de Vehículo de Empresa",
                "description": "Valor del beneficio de vehículo para uso personal",
                "codigo_concepto": "USO_VEHICULO",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "seguro_salud": {
                "type": "decimal",
                "label": "Seguro de Salud Privado",
                "description": "Cobertura médica pagada por la empresa",
                "codigo_concepto": "SEGURO_SALUD",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "aporte_pension": {
                "type": "decimal",
                "label": "Aporte a Pensión/Retiro",
                "description": "Aportaciones de la empresa a fondo de pensión",
                "codigo_concepto": "APORTE_PENSION",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "stock_options": {
                "type": "decimal",
                "label": "Opciones de Acciones",
                "description": "Valor de opciones de compra de acciones",
                "codigo_concepto": "STOCK_OPTIONS",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "subsidio_alimentacion": {
                "type": "decimal",
                "label": "Subsidio de Alimentación",
                "description": "Vales, tarjetas o servicio de comedor",
                "codigo_concepto": "SUBSIDIO_ALIMENTACION",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "subsidio_transporte": {
                "type": "decimal",
                "label": "Subsidio de Transporte",
                "description": "Compensación por gastos de desplazamiento",
                "codigo_concepto": "SUBSIDIO_TRANSPORTE",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "subsidio_guarderia": {
                "type": "decimal",
                "label": "Subsidio de Guardería",
                "description": "Ayuda para costes de cuidado infantil",
                "codigo_concepto": "SUBSIDIO_GUARDERIA",
                "tipo_valor": "monto",
                "gravable": False,
            },
            # C. Compensaciones por Tiempo y Bienestar
            "vacaciones_dias": {
                "type": "decimal",
                "label": "Días de Vacaciones",
                "description": "Días de vacaciones pagadas en el período",
                "codigo_concepto": "VACACIONES",
                "tipo_valor": "dias",
                "gravable": True,
            },
            "pago_festivos": {
                "type": "decimal",
                "label": "Pago por Días Festivos",
                "description": "Compensación por trabajar en días de asueto",
                "codigo_concepto": "PAGO_FESTIVOS",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "aguinaldo": {
                "type": "decimal",
                "label": "Aguinaldo/Gratificación Anual",
                "description": "Pago extra en época específica del año",
                "codigo_concepto": "THIRTEENTH_SALARY",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "participacion_utilidades": {
                "type": "decimal",
                "label": "Participación en Utilidades",
                "description": "Porcentaje de beneficios anuales de la empresa",
                "codigo_concepto": "UTILIDADES",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "permiso_pagado_dias": {
                "type": "decimal",
                "label": "Permisos Pagados (días)",
                "description": "Días de permiso pagado (enfermedad, maternidad, etc.)",
                "codigo_concepto": "PERMISO_PAGADO",
                "tipo_valor": "dias",
                "gravable": True,
            },
            "fondo_ahorro_empresa": {
                "type": "decimal",
                "label": "Aporte Empresa a Fondo de Ahorro",
                "description": "Aporte de la empresa al fondo de ahorro del empleado",
                "codigo_concepto": "FONDO_AHORRO_EMPRESA",
                "tipo_valor": "monto",
                "gravable": False,
            },
            # D. Reembolsos y Dietas
            "viaticos": {
                "type": "decimal",
                "label": "Viáticos",
                "description": "Gastos de alojamiento, comida y transporte en viajes",
                "codigo_concepto": "VIATICO",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "gastos_representacion": {
                "type": "decimal",
                "label": "Gastos de Representación",
                "description": "Costes de entretenimiento y relaciones con clientes",
                "codigo_concepto": "GASTOS_REPRESENTACION",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "reembolso_formacion": {
                "type": "decimal",
                "label": "Reembolso de Formación",
                "description": "Cursos, certificaciones, maestrías, etc.",
                "codigo_concepto": "REEMBOLSO_FORMACION",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "reembolso_medico": {
                "type": "decimal",
                "label": "Reembolso de Gastos Médicos",
                "description": "Tratamientos o medicamentos no cubiertos",
                "codigo_concepto": "REEMBOLSO_MEDICO",
                "tipo_valor": "monto",
                "gravable": False,
            },
            # E. Pagos por Eventos Específicos
            "indemnizacion_despido": {
                "type": "decimal",
                "label": "Indemnización por Despido",
                "description": "Pago por terminación de relación laboral",
                "codigo_concepto": "INDEMNIZACION",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "compensacion_reubicacion": {
                "type": "decimal",
                "label": "Compensación por Reubicación",
                "description": "Ayuda para mudanza o cambio de residencia",
                "codigo_concepto": "COMPENSACION_REUBICACION",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "premio_puntualidad": {
                "type": "decimal",
                "label": "Premio por Puntualidad/Asistencia",
                "description": "Premio por asistencia perfecta o puntualidad",
                "codigo_concepto": "PREMIO_PUNTUALIDAD",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "premio_innovacion": {
                "type": "decimal",
                "label": "Premio por Ideas/Innovación",
                "description": "Reconocimiento por ideas innovadoras",
                "codigo_concepto": "PREMIO_INNOVACION",
                "tipo_valor": "monto",
                "gravable": True,
            },
            "ayuda_fallecimiento": {
                "type": "decimal",
                "label": "Ayuda por Fallecimiento",
                "description": "Apoyo económico en situaciones de luto",
                "codigo_concepto": "AYUDA_FALLECIMIENTO",
                "tipo_valor": "monto",
                "gravable": False,
            },
            # Deducciones comunes
            "dias_ausencia": {
                "type": "decimal",
                "label": "Días de Ausencia",
                "description": "Días de ausencia no justificada a descontar",
                "codigo_concepto": "AUSENCIA",
                "tipo_valor": "dias",
                "gravable": False,
            },
            "dias_incapacidad": {
                "type": "decimal",
                "label": "Días de Incapacidad",
                "description": "Días de incapacidad médica",
                "codigo_concepto": "INCAPACIDAD",
                "tipo_valor": "dias",
                "gravable": False,
            },
            "adelanto_salario": {
                "type": "decimal",
                "label": "Adelanto de Salario",
                "description": "Monto de adelanto de salario a descontar",
                "codigo_concepto": "ADELANTO",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "prestamo_cuota": {
                "type": "decimal",
                "label": "Cuota de Préstamo",
                "description": "Cuota de préstamo a descontar",
                "codigo_concepto": "PRESTAMO",
                "tipo_valor": "monto",
                "gravable": False,
            },
            "fondo_ahorro_empleado": {
                "type": "decimal",
                "label": "Aporte Empleado a Fondo de Ahorro",
                "description": "Aporte del empleado al fondo de ahorro",
                "codigo_concepto": "FONDO_AHORRO_EMPLEADO",
                "tipo_valor": "monto",
                "gravable": False,
            },
        },
    },
    "calculado": {
        "label": "Valores Calculados",
        "fields": {
            "meses_restantes_fiscal": {
                "type": "integer",
                "label": "Meses Restantes en Período Fiscal",
                "description": "Meses que faltan para terminar el período fiscal",
            },
            "periodos_restantes_fiscal": {
                "type": "integer",
                "label": "Períodos Restantes",
                "description": "Períodos de pago restantes en el año fiscal",
            },
            "dias_trabajados_periodo": {
                "type": "integer",
                "label": "Días Trabajados en Período",
                "description": "Días efectivamente trabajados en el período actual",
            },
            "es_primer_periodo_sistema": {
                "type": "boolean",
                "label": "Es Primer Período del Sistema",
                "description": "Indica si es el primer período procesado por el sistema",
            },
            "salario_diario": {
                "type": "decimal",
                "label": "Salario Diario",
                "description": "Salario base dividido entre días del período",
            },
            "salario_hora": {
                "type": "decimal",
                "label": "Salario por Hora",
                "description": "Salario base dividido entre horas laborales del período",
            },
            "antiguedad_dias": {
                "type": "integer",
                "label": "Antigüedad (Días)",
                "description": "Días transcurridos desde la fecha de ingreso",
            },
            "antiguedad_meses": {
                "type": "integer",
                "label": "Antigüedad (Meses)",
                "description": "Meses completos desde la fecha de ingreso",
            },
            "antiguedad_anios": {
                "type": "integer",
                "label": "Antigüedad (Años)",
                "description": "Años completos desde la fecha de ingreso",
            },
            "edad_anios": {
                "type": "integer",
                "label": "Edad (Años)",
                "description": "Edad del empleado en años cumplidos",
            },
            "es_nuevo_ingreso": {
                "type": "boolean",
                "label": "Es Nuevo Ingreso",
                "description": "Indica si el empleado ingresó durante el período actual",
            },
            "dias_proporcional": {
                "type": "integer",
                "label": "Días para Cálculo Proporcional",
                "description": "Días a considerar para prorrateo de nuevo ingreso/baja",
            },
        },
    },
}


# Mapping of novelty codes to their calculation behavior
NOVELTY_CODES = {
    "HORAS_EXTRA": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Horas extra trabajadas",
    },
    "HORAS_EXTRA_DOBLES": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Horas extra dobles (feriados/domingos)",
    },
    "AUSENCIA": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Ausencia no justificada",
    },
    "INCAPACIDAD": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Incapacidad médica",
    },
    "COMISION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Comisiones por ventas",
    },
    "BONIFICACION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Bonificación",
    },
    "VIATICO": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Viáticos",
    },
    "VACACIONES": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Pago de vacaciones",
    },
    "ADELANTO": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Adelanto de salario",
    },
    "PRESTAMO": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Cuota de préstamo",
    },
    # A. Compensación Base y Directa
    "BONO_OBJETIVOS": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Bono por cumplimiento de objetivos",
    },
    "BONO_ANUAL": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Bono anual o trimestral",
    },
    "PLUS_PELIGROSIDAD": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Plus por peligrosidad o toxicidad",
    },
    "PLUS_NOCTURNO": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Plus por trabajo nocturno",
    },
    "PLUS_ANTIGUEDAD": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Plus por antigüedad",
    },
    # B. Compensaciones en Especie y Beneficios
    "USO_VEHICULO": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Uso de vehículo de empresa",
    },
    "SEGURO_SALUD": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Seguro de salud privado",
    },
    "APORTE_PENSION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Aporte patronal a pensión/retiro",
    },
    "STOCK_OPTIONS": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Opciones de compra de acciones",
    },
    "SUBSIDIO_ALIMENTACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Subsidio de alimentación",
    },
    "SUBSIDIO_TRANSPORTE": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Subsidio de transporte",
    },
    "SUBSIDIO_GUARDERIA": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Subsidio de guardería",
    },
    # C. Compensaciones por Tiempo y Bienestar
    "PAGO_FESTIVOS": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Pago por días festivos trabajados",
    },
    "THIRTEENTH_SALARY": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Aguinaldo o gratificación anual",
    },
    "UTILIDADES": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Participación en utilidades",
    },
    "PERMISO_PAGADO": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Permisos pagados (enfermedad, maternidad, etc.)",
    },
    "FONDO_AHORRO_EMPRESA": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Aporte empresa a fondo de ahorro",
    },
    "FONDO_AHORRO_EMPLEADO": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Aporte empleado a fondo de ahorro",
    },
    # D. Reembolsos y Dietas
    "GASTOS_REPRESENTACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Gastos de representación",
    },
    "REEMBOLSO_FORMACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Reembolso de gastos de formación",
    },
    "REEMBOLSO_MEDICO": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Reembolso de gastos médicos",
    },
    # E. Pagos por Eventos Específicos
    "INDEMNIZACION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Indemnización por despido",
    },
    "COMPENSACION_REUBICACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Compensación por reubicación",
    },
    "PREMIO_PUNTUALIDAD": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Premio por puntualidad/asistencia",
    },
    "PREMIO_INNOVACION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Premio por ideas innovadoras",
    },
    "AYUDA_FALLECIMIENTO": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Ayuda por fallecimiento de familiar",
    },
}


def get_available_sources_for_ui() -> list[dict]:
    """Get available data sources formatted for the UI dropdown.

    Returns:
        List of dictionaries with source information for the schema editor
    """
    sources = []
    for category, data in AVAILABLE_DATA_SOURCES.items():
        for field_name, field_info in data["fields"].items():
            sources.append(
                {
                    "value": f"{category}.{field_name}",
                    "label": f"{data['label']} - {field_info['label']}",
                    "type": field_info["type"],
                    "description": field_info["description"],
                    "category": category,
                }
            )
    return sources
