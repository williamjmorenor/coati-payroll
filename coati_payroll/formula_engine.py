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

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
import ast
import operator
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.enums import StepType
from coati_payroll.formula_engine.data_sources import AVAILABLE_DATA_SOURCES
from coati_payroll.formula_engine_examples import EXAMPLE_IR_NICARAGUA_SCHEMA
from coati_payroll.i18n import _
from coati_payroll.log import TRACE_LEVEL_NUM, is_trace_enabled, log
from coati_payroll.schema_validator import validate_schema
from coati_payroll.schema_validator import ValidationError as _BaseValidationError

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


# ValidationError moved to schema_validator.py to avoid circular imports
# Create a subclass that inherits from FormulaEngineError for backward compatibility
class ValidationError(_BaseValidationError, FormulaEngineError):
    """Exception for validation errors in schema or data.

    Inherits from both the base ValidationError (for schema_validator) and
    FormulaEngineError (for backward compatibility with existing error handling).

    Python 3.11+ enhancement: Can use add_note() to append contextual information.
    """

    pass


__all__ = [
    "FormulaEngine",
    "FormulaEngineError",
    "TaxEngineError",
    "ValidationError",
    "CalculationError",
    "EXAMPLE_IR_NICARAGUA_SCHEMA",
    "get_available_sources_for_ui",
]


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

    def __init__(self, schema: dict[str, Any], strict_mode: bool = False):
        """Initialize the formula engine with a calculation schema.

        Args:
            schema: JSON schema defining the calculation rules
            strict_mode: If True, warnings are treated as errors. Default: False

        Raises:
            ValidationError: If schema is invalid
        """
        self.schema = schema
        self.variables: dict[str, Decimal] = {}
        self.results: dict[str, Any] = {}
        self.strict_mode = strict_mode
        validate_schema(self.schema, error_class=ValidationError)
        # Validate tax tables for critical integrity issues
        warnings = self._validate_all_tax_tables()
        # Handle warnings
        if warnings:
            if strict_mode:
                raise ValidationError(
                    f"Advertencias en tablas de impuestos (modo estricto activado): {', '.join(warnings)}"
                )
            else:
                for warning in warnings:
                    log.warning(f"Validación de tabla de impuestos: {warning}")

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
        match node:
            case ast.Constant(value=value):
                return to_decimal(value)

            case ast.Name(id=var_name):
                if var_name not in self.variables:
                    raise CalculationError(f"Undefined variable: {var_name}")
                return self.variables[var_name]

            case ast.BinOp():
                return self._eval_binary_op(node)

            case ast.UnaryOp():
                return self._eval_unary_op(node)

            case ast.Call():
                return self._eval_function_call(node)

            case _:
                raise CalculationError(f"Unsupported AST node: {type(node).__name__}")

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
        match op_type:
            case ast.Add:
                return to_decimal(left + right)

            case ast.Sub:
                return to_decimal(left - right)

            case ast.Mult:
                return to_decimal(left * right)

            case ast.Div:
                if right == 0:
                    return Decimal("0")  # Safe division by zero handling
                return to_decimal(left / right)

            case ast.FloorDiv:
                if right == 0:
                    return Decimal("0")
                return to_decimal(left // right)

            case ast.Mod:
                if right == 0:
                    return Decimal("0")
                return to_decimal(left % right)

            case ast.Pow:
                return to_decimal(left**right)

            case _:
                raise ValueError(f"Unsupported operator: {op_type}")

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
        match op_type:
            case ast.UAdd:
                return to_decimal(+operand)

            case ast.USub:
                return to_decimal(-operand)

            case _:
                raise ValueError(f"Unsupported unary operator: {op_type}")

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

    def _validate_tax_table(self, table_name: str, table: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
        """Validate a tax table for critical integrity issues.

        This method validates that:
        1. The table is ordered by min values (ascending)
        2. Brackets do not overlap
        3. There are no significant gaps between brackets (with tolerance for small gaps)
        4. Fixed and over values are valid

        Args:
            table_name: Name of the tax table being validated
            table: List of tax bracket dictionaries

        Returns:
            Tuple of (errors, warnings) lists. Errors are critical and should raise exceptions.
            Warnings are non-critical issues that should be logged.

        Raises:
            ValidationError: If table has critical errors (ordering, overlap, structure issues)
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not table:
            raise ValidationError(
                f"La tabla de impuestos '{table_name}' está vacía. " "Debe contener al menos un tramo."
            )

        # Validate each bracket structure
        for i, bracket in enumerate(table):
            if not isinstance(bracket, dict):
                raise ValidationError(f"El tramo {i} de la tabla '{table_name}' debe ser un diccionario")

            min_val = bracket.get("min")
            max_val = bracket.get("max")

            if min_val is None:
                raise ValidationError(f"El tramo {i} de la tabla '{table_name}' debe tener un valor 'min'")

            try:
                min_decimal = to_decimal(min_val)
            except ValidationError as e:
                raise ValidationError(
                    f"El valor 'min' del tramo {i} de la tabla '{table_name}' es inválido: {e}"
                ) from e

            if max_val is not None:
                try:
                    max_decimal = to_decimal(max_val)
                    if max_decimal < min_decimal:
                        raise ValidationError(
                            f"El tramo {i} de la tabla '{table_name}' tiene 'max' ({max_val}) "
                            f"menor que 'min' ({min_val}). El límite superior debe ser mayor o igual al inferior."
                        )
                except ValidationError as e:
                    raise ValidationError(
                        f"El valor 'max' del tramo {i} de la tabla '{table_name}' es inválido: {e}"
                    ) from e

            # Validate fixed and over values
            fixed = bracket.get("fixed", 0)
            over = bracket.get("over", 0)

            try:
                fixed_decimal = to_decimal(fixed)
                over_decimal = to_decimal(over)

                if fixed_decimal < 0:
                    errors.append(
                        f"El tramo {i} de la tabla '{table_name}' tiene 'fixed' negativo ({fixed}). "
                        "El valor 'fixed' no puede ser negativo."
                    )

                if over_decimal < 0:
                    errors.append(
                        f"El tramo {i} de la tabla '{table_name}' tiene 'over' negativo ({over}). "
                        "El valor 'over' no puede ser negativo."
                    )

                if over_decimal > min_decimal:
                    errors.append(
                        f"El tramo {i} de la tabla '{table_name}' tiene 'over' ({over}) mayor que 'min' ({min_val}). "
                        "El valor 'over' debe ser menor o igual a 'min'."
                    )
            except ValidationError as e:
                errors.append(f"Valores inválidos en tramo {i} de tabla '{table_name}': {e}")

        # Validate ordering and overlaps
        for i in range(len(table) - 1):
            current = table[i]
            next_bracket = table[i + 1]

            current_min = to_decimal(current.get("min", 0))
            current_max = current.get("max")
            next_min = to_decimal(next_bracket.get("min", 0))

            # Check ordering: next bracket's min should be >= current bracket's min
            if next_min < current_min:
                raise ValidationError(
                    f"La tabla de impuestos '{table_name}' no está ordenada. "
                    f"El tramo {i + 1} tiene 'min'={next_min} que es menor que el 'min'={current_min} "
                    f"del tramo {i}. Los tramos deben estar ordenados de menor a mayor."
                )

            # Check for overlaps and gaps
            if current_max is not None:
                current_max_decimal = to_decimal(current_max)

                # Check for overlap or gap
                if current_max_decimal > next_min:
                    # Overlap detected: current bracket extends beyond next bracket's start
                    overlap_start = next_min
                    overlap_end = current_max_decimal
                    raise ValidationError(
                        f"La tabla de impuestos '{table_name}' tiene tramos solapados. "
                        f"Los tramos {i} y {i + 1} se solapan en el rango [{overlap_start}, {overlap_end}]. "
                        f"El tramo {i} termina en {current_max_decimal} y el tramo {i + 1} comienza en {next_min}. "
                        "Los tramos no deben solaparse."
                    )
                elif current_max_decimal < next_min:
                    # Check for significant gap: allow small tolerance for rounding/formatting
                    gap_size = next_min - current_max_decimal
                    tolerance = Decimal("0.01")  # Allow 1 cent gap for rounding

                    if gap_size > tolerance:
                        warnings.append(
                            f"La tabla de impuestos '{table_name}' tiene un gap significativo entre "
                            f"los tramos {i} y {i + 1}. "
                            f"El tramo {i} termina en {current_max_decimal} y el tramo {i + 1} comienza en {next_min}. "
                            f"Hay un gap de {gap_size} que no está cubierto por ningún tramo."
                        )
                # else: current_max_decimal == next_min is acceptable (continuous brackets)
            else:
                # Current bracket is open-ended, but there's a next bracket - this is an error
                raise ValidationError(
                    f"La tabla de impuestos '{table_name}' tiene un tramo abierto (sin 'max') en la posición {i}, "
                    f"pero hay tramos adicionales después. El tramo abierto debe ser el último de la tabla."
                )

        # Validate that only the last bracket can be open-ended
        for i in range(len(table) - 1):
            if table[i].get("max") is None:
                raise ValidationError(
                    f"La tabla de impuestos '{table_name}' tiene un tramo abierto (sin 'max') en la posición {i}, "
                    "pero no es el último tramo. Solo el último tramo puede ser abierto."
                )

        # Raise errors if any critical errors found
        if errors:
            raise ValidationError(f"Errores críticos en la tabla de impuestos '{table_name}': {'; '.join(errors)}")

        return errors, warnings

    def _validate_all_tax_tables(self) -> list[str]:
        """Validate all tax tables in the schema.

        Returns:
            List of warning messages (non-critical issues)

        Raises:
            ValidationError: If any tax table has critical validation errors
        """
        tax_tables = self.schema.get("tax_tables", {})
        if not isinstance(tax_tables, dict):
            raise ValidationError("'tax_tables' debe ser un diccionario")

        all_warnings: list[str] = []

        for table_name, table in tax_tables.items():
            if not isinstance(table, list):
                raise ValidationError(f"La tabla de impuestos '{table_name}' debe ser una lista de tramos")

            errors, warnings = self._validate_tax_table(table_name, table)
            all_warnings.extend(warnings)

        return all_warnings

    def _lookup_tax_table(
        self,
        table_name: str,
        input_value: Decimal,
    ) -> dict[str, Decimal]:
        """Look up tax bracket in a tax table.

        This method uses defensive coding to handle edge cases even if validation
        passed. It ensures consistent behavior and prevents incorrect calculations.

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

        if not table:
            # Defensive: empty table
            self._trace(
                _("Advertencia: tabla de impuestos '%(table)s' está vacía, devolviendo ceros") % {"table": table_name}
            )
            return {
                "tax": Decimal("0"),
                "rate": Decimal("0"),
                "fixed": Decimal("0"),
                "over": Decimal("0"),
            }

        self._trace(
            _("Buscando tabla de impuestos '%(table)s' con valor %(value)s; brackets=%(count)s")
            % {"table": table_name, "value": input_value, "count": len(table)}
        )

        # Defensive: Sort brackets by min value if not already sorted
        # This handles cases where validation might have been bypassed
        try:
            sorted_table = sorted(
                table,
                key=lambda b: to_decimal(b.get("min", 0)),
            )
            if sorted_table != table:
                self._trace(
                    _("Advertencia: tabla '%(table)s' no estaba ordenada, ordenando automáticamente")
                    % {"table": table_name}
                )
                table = sorted_table
        except Exception as e:
            # If sorting fails, continue with original table but log warning
            self._trace(
                _("Advertencia: no se pudo ordenar la tabla '%(table)s': %(error)s")
                % {"table": table_name, "error": str(e)}
            )

        # Find the applicable bracket
        # Use reverse iteration for open-ended brackets (they should be last)
        # but iterate forward for better performance with sorted tables
        matched_brackets = []
        for i, bracket in enumerate(table):
            try:
                min_val = to_decimal(bracket.get("min", 0))
                max_val = bracket.get("max")

                if max_val is None:
                    # Open-ended bracket (highest tier)
                    if input_value >= min_val:
                        matched_brackets.append((i, bracket, min_val, None))
                else:
                    max_val = to_decimal(max_val)
                    # Defensive: validate bracket range
                    if max_val < min_val:
                        self._trace(
                            _("Advertencia: tramo %(index)s de tabla '%(table)s' tiene max < min, omitiendo")
                            % {"index": i, "table": table_name}
                        )
                        continue

                    if min_val <= input_value <= max_val:
                        matched_brackets.append((i, bracket, min_val, max_val))
            except Exception as e:
                # Defensive: skip invalid brackets
                self._trace(
                    _("Advertencia: error procesando tramo %(index)s de tabla '%(table)s': %(error)s")
                    % {"index": i, "table": table_name, "error": str(e)}
                )
                continue

        # Handle multiple matches (overlaps) - use the first valid match
        # In a properly validated table, there should be only one match
        if matched_brackets:
            if len(matched_brackets) > 1:
                # Multiple brackets match - this indicates an overlap
                # Use the first one but log a warning
                self._trace(
                    _(
                        "ADVERTENCIA CRÍTICA: múltiples tramos coinciden para valor %(value)s en tabla '%(table)s'. "
                        "Esto indica solapamiento. Usando el primer tramo encontrado."
                    )
                    % {"value": input_value, "table": table_name}
                )

            i, bracket, min_val, max_val = matched_brackets[0]
            result = self._calculate_bracket_tax(bracket, input_value)
            if max_val is None:
                self._trace(
                    _("Aplicando tramo abierto desde %(min)s para valor %(value)s -> %(result)s")
                    % {"min": min_val, "value": input_value, "result": result}
                )
            else:
                self._trace(
                    _("Aplicando tramo %(min)s - %(max)s para valor %(value)s -> %(result)s")
                    % {"min": min_val, "max": max_val, "value": input_value, "result": result}
                )
            return result

        # If no bracket found, return zeros
        # This could indicate a gap in the table
        self._trace(
            _(
                "No se encontró tramo para valor %(value)s en tabla '%(table)s', devolviendo ceros. "
                "Esto puede indicar un gap en la configuración de la tabla."
            )
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
