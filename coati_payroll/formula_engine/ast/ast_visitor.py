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
"""AST Visitor pattern for safe expression evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

import ast

from ..exceptions import CalculationError
from .safe_operators import SAFE_FUNCTIONS, SAFE_OPERATORS
from .type_converter import to_decimal


class ASTVisitor(ABC):
    """Visitor pattern base class for AST traversal."""

    @abstractmethod
    def visit(self, node: ast.AST) -> Decimal:
        """Visit and evaluate an AST node."""
        pass


class SafeASTVisitor(ASTVisitor):
    """Safe visitor for evaluating mathematical expressions."""

    def __init__(self, variables: dict[str, Decimal]):
        """Initialize visitor with variable context.

        Args:
            variables: Dictionary of variable names to Decimal values
        """
        self.variables = variables

    def visit(self, node: ast.AST) -> Decimal:
        """Visit and evaluate an AST node.

        Args:
            node: AST node to evaluate

        Returns:
            Decimal result of evaluation

        Raises:
            CalculationError: If evaluation fails
        """
        method_name = f"visit_{node.__class__.__name__.lower()}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: ast.AST) -> Decimal:
        """Handle unsupported node types."""
        raise CalculationError(f"Unsupported AST node: {type(node).__name__}")

    def visit_constant(self, node: ast.Constant) -> Decimal:
        """Visit a constant node."""
        return to_decimal(node.value)

    def visit_name(self, node: ast.Name) -> Decimal:
        """Visit a variable name node."""
        if node.id not in self.variables:
            raise CalculationError(f"Undefined variable: {node.id}")
        return self.variables[node.id]

    def visit_binop(self, node: ast.BinOp) -> Decimal:
        """Visit a binary operation node."""
        left = self.visit(node.left)
        right = self.visit(node.right)

        op_type = type(node.op)
        op_func = SAFE_OPERATORS.get(op_type)
        if not op_func:
            raise CalculationError(f"Unsafe operator: {op_type.__name__}")

        # Handle division by zero
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            return Decimal("0")

        try:
            result = op_func(left, right)
            return to_decimal(result)
        except Exception as e:
            raise CalculationError(f"Error in binary operation: {e}") from e

    def visit_unaryop(self, node: ast.UnaryOp) -> Decimal:
        """Visit a unary operation node."""
        operand = self.visit(node.operand)

        op_type = type(node.op)
        if op_type == ast.UAdd:
            return to_decimal(+operand)
        elif op_type == ast.USub:
            return to_decimal(-operand)
        else:
            raise CalculationError(f"Unsafe unary operator: {op_type.__name__}")

    def visit_call(self, node: ast.Call) -> Decimal:
        """Visit a function call node."""
        if not isinstance(node.func, ast.Name):
            raise CalculationError("Only named functions are allowed")

        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise CalculationError(
                f"Function '{func_name}' is not allowed. " f"Allowed functions: {', '.join(SAFE_FUNCTIONS.keys())}"
            )

        # Evaluate arguments
        args = [self.visit(arg) for arg in node.args]

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
