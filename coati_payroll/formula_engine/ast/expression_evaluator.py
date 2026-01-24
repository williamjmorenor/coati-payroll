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
"""Expression evaluator using AST visitor pattern.

This module provides secure evaluation of mathematical expressions from JSON rules.
It implements multiple layers of security:

1. Expression Length Validation: Prevents DoS attacks via extremely long expressions
2. AST Depth Validation: Prevents stack overflow from deeply nested expressions
3. Whitelist-based AST Validation: Only approved node types are allowed
4. Safe Visitor Pattern: No dynamic code execution or attribute access
5. Decimal Precision: All calculations maintain financial precision

Security Model:
- Input expressions are parsed into Abstract Syntax Trees (AST)
- AST is validated against a whitelist of allowed node types
- AST depth is checked to prevent stack overflow
- Evaluation uses explicit visitor pattern (no eval/exec/compile)
- All operations are deterministic and side-effect free

Example Safe Expression:
    'salario_base * 1.15 + max(bono, 1000)'

Example Unsafe Expression (rejected):
    '__import__("os").system("rm -rf /")'
    'open("/etc/passwd").read()'
    '[x for x in range(1000000)]'
"""

from __future__ import annotations

import ast
from decimal import Decimal
from typing import Callable

from coati_payroll.i18n import _
from coati_payroll.log import TRACE_LEVEL_NUM, is_trace_enabled, log

from ..exceptions import CalculationError
from .ast_visitor import SafeASTVisitor
from .safe_operators import ALLOWED_AST_TYPES, MAX_EXPRESSION_LENGTH, MAX_AST_DEPTH
from .type_converter import to_decimal


class ExpressionEvaluator:
    """Evaluates mathematical expressions safely using AST.

    This class provides enterprise-grade secure expression evaluation for
    payroll formulas. It prevents code injection, DoS attacks, and ensures
    all calculations are deterministic and auditable.

    Security Features:
    - Expression length limits (prevents DoS)
    - AST depth limits (prevents stack overflow)
    - Whitelist-based validation (prevents code injection)
    - No dynamic code execution (no eval/exec/compile)
    - Immutable variable context (prevents side effects)
    - Comprehensive error messages for debugging

    Thread Safety:
    This class is thread-safe as long as the variables dictionary is not
    modified during evaluation. Each evaluation creates a new visitor instance.
    """

    def __init__(self, variables: dict[str, Decimal], trace_callback: Callable[[str], None] | None = None):
        """Initialize expression evaluator.

        Args:
            variables: Dictionary of variable names to Decimal values.
                      This dictionary is not modified during evaluation.
            trace_callback: Optional callback for trace logging.
                          Should be thread-safe if used in concurrent contexts.
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

        This method implements multiple layers of security validation:
        1. Input validation (type, length)
        2. Syntax validation (AST parsing)
        3. Security validation (whitelist checking)
        4. Depth validation (stack overflow prevention)
        5. Safe evaluation (visitor pattern)

        Args:
            expression: Mathematical expression string (e.g., 'a + b * 2')

        Returns:
            Result of the expression as Decimal

        Raises:
            CalculationError: If expression is invalid, unsafe, or evaluation fails

        Examples:
            >>> evaluator = ExpressionEvaluator({'x': Decimal('10'), 'y': Decimal('5')})
            >>> evaluator.evaluate('x + y')
            Decimal('15')
            >>> evaluator.evaluate('max(x, y) * 2')
            Decimal('20')
        """
        if not expression or not isinstance(expression, str):
            return Decimal("0")

        expression = expression.strip()
        if not expression:
            return Decimal("0")

        if len(expression) > MAX_EXPRESSION_LENGTH:
            raise CalculationError(
                f"Expression too long ({len(expression)} characters). "
                f"Maximum allowed: {MAX_EXPRESSION_LENGTH} characters. "
                "This limit prevents denial-of-service attacks."
            )

        self.trace_callback(_("Evaluando expresión: '%(expr)s'") % {"expr": expression})

        try:
            tree = ast.parse(expression, mode="eval")

            self._validate_ast_security(tree.body)
            self._validate_ast_depth(tree.body)

            visitor = SafeASTVisitor(self.variables)
            result = visitor.visit(tree.body)
            final_result = to_decimal(result)

            self.trace_callback(
                _("Resultado expresión '%(expr)s' => %(res)s") % {"expr": expression, "res": final_result}
            )
            return final_result
        except SyntaxError as e:
            raise CalculationError(
                f"Invalid expression syntax in '{expression}': {e}. "
                "Check for unmatched parentheses, invalid operators, or typos."
            ) from e
        except ZeroDivisionError:
            return Decimal("0")
        except CalculationError:
            raise
        except Exception as e:
            raise CalculationError(f"Unexpected error evaluating expression '{expression}': {e}") from e

    def _validate_ast_security(self, node: ast.AST) -> None:
        """Validate that an AST node only contains safe operations.

        This method implements a whitelist-based security model. It walks the
        entire AST and verifies that every node is in the allowed list. This
        prevents code injection attacks like:
        - Import statements: __import__('os').system('rm -rf /')
        - Attribute access: obj.__class__.__bases__[0].__subclasses__()
        - List comprehensions: [x for x in range(999999999)]
        - Lambda functions: (lambda: exec('malicious code'))()

        Args:
            node: AST node to validate (typically the root of the expression tree)

        Raises:
            CalculationError: If any unsafe operation is detected
        """
        for child in ast.walk(node):
            if not isinstance(child, ALLOWED_AST_TYPES):
                raise CalculationError(
                    f"Security violation: AST node type '{child.__class__.__name__}' is not allowed. "
                    "Only basic arithmetic operations and whitelisted functions are permitted. "
                    "This restriction prevents code injection and arbitrary code execution."
                )

            if isinstance(child, ast.Call):
                if not isinstance(child.func, ast.Name):
                    raise CalculationError(
                        "Security violation: Only direct named function calls are allowed. "
                        "Attribute access (e.g., obj.method()) and lambda functions are prohibited."
                    )
                from .safe_operators import SAFE_FUNCTIONS

                if child.func.id not in SAFE_FUNCTIONS:
                    raise CalculationError(
                        f"Security violation: Function '{child.func.id}' is not in the whitelist. "
                        f"Allowed functions: {', '.join(sorted(SAFE_FUNCTIONS.keys()))}. "
                        "This restriction prevents execution of arbitrary Python functions."
                    )

    def _validate_ast_depth(self, node: ast.AST, current_depth: int = 0) -> None:
        """Validate that AST depth does not exceed maximum to prevent stack overflow.

        Deeply nested expressions can cause stack overflow during evaluation:
        - Example: ((((((((((x + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1) + 1)

        This validation prevents denial-of-service attacks via deeply nested
        expressions that could exhaust the call stack.

        Args:
            node: AST node to validate
            current_depth: Current depth in the tree (used for recursion)

        Raises:
            CalculationError: If AST depth exceeds maximum allowed
        """
        if current_depth > MAX_AST_DEPTH:
            raise CalculationError(
                f"Expression too complex: AST depth ({current_depth}) exceeds maximum ({MAX_AST_DEPTH}). "
                "Simplify the expression by breaking it into multiple steps. "
                "This limit prevents stack overflow attacks."
            )

        for child in ast.iter_child_nodes(node):
            self._validate_ast_depth(child, current_depth + 1)
