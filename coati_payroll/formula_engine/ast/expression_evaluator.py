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
"""Expression evaluator using AST visitor pattern."""

from __future__ import annotations

import ast
from decimal import Decimal
from typing import Callable

from coati_payroll.i18n import _
from coati_payroll.log import TRACE_LEVEL_NUM, is_trace_enabled, log

from ..exceptions import CalculationError
from .ast_visitor import SafeASTVisitor
from .safe_operators import ALLOWED_AST_TYPES
from .type_converter import to_decimal


class ExpressionEvaluator:
    """Evaluates mathematical expressions safely using AST."""

    def __init__(self, variables: dict[str, Decimal], trace_callback: Callable[[str], None] | None = None):
        """Initialize expression evaluator.

        Args:
            variables: Dictionary of variable names to Decimal values
            trace_callback: Optional callback for trace logging
        """
        self.variables = variables
        self.trace_callback = trace_callback or self._default_trace

    def _default_trace(self, message: str) -> None:
        """Default trace callback."""
        if is_trace_enabled():
            try:
                log.log(TRACE_LEVEL_NUM, message)
            except Exception:
                pass

    def evaluate(self, expression: str) -> Decimal:
        """Safely evaluate a mathematical expression using AST.

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

        self.trace_callback(_("Evaluando expresión: '%(expr)s'") % {"expr": expression})

        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode="eval")
            # Validate that the AST only contains safe operations
            self._validate_ast_security(tree.body)
            # Evaluate the AST using visitor pattern
            visitor = SafeASTVisitor(self.variables)
            result = visitor.visit(tree.body)
            final_result = to_decimal(result)
            self.trace_callback(
                _("Resultado expresión '%(expr)s' => %(res)s") % {"expr": expression, "res": final_result}
            )
            return final_result
        except SyntaxError as e:
            raise CalculationError(f"Invalid expression syntax: {e}") from e
        except ZeroDivisionError:
            return Decimal("0")
        except Exception as e:
            raise CalculationError(f"Error evaluating expression '{expression}': {e}") from e

    def _validate_ast_security(self, node: ast.AST) -> None:
        """Validate that an AST node only contains safe operations.

        Args:
            node: AST node to validate

        Raises:
            CalculationError: If unsafe operations are detected
        """
        # Validate all nodes in the tree in a single pass
        for child in ast.walk(node):
            if not isinstance(child, ALLOWED_AST_TYPES):
                raise CalculationError(
                    f"Unsafe operation detected: {child.__class__.__name__}. "
                    "Only basic arithmetic and safe functions are allowed."
                )
            # Validate function calls
            if isinstance(child, ast.Call):
                if not isinstance(child.func, ast.Name):
                    raise CalculationError("Only named functions are allowed")
                from .safe_operators import SAFE_FUNCTIONS

                if child.func.id not in SAFE_FUNCTIONS:
                    raise CalculationError(
                        f"Function '{child.func.id}' is not allowed. "
                        f"Allowed functions: {', '.join(SAFE_FUNCTIONS.keys())}"
                    )
