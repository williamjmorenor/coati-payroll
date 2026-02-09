# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Safe operators and functions for expression evaluation.

This module defines the ONLY operators and functions allowed in formula expressions.
It implements a whitelist-based security model to prevent arbitrary code execution.

Security Guarantees:
- Only mathematical operations are allowed (no I/O, no imports, no system calls)
- No access to Python builtins beyond explicitly whitelisted functions
- No attribute access or dynamic code execution
- All operations are deterministic and side-effect free
- Expression complexity is bounded to prevent DoS attacks

Allowed Operations:
- Arithmetic: +, -, *, /, //, %, **
- Functions: min, max, abs, round
- Variables: Only pre-defined variables from the execution context
- Constants: Numeric literals only

Prohibited Operations:
- File I/O, network access, system calls
- Import statements, eval, exec, compile
- Attribute access (__getattr__, __setattr__, etc.)
- Lambda functions, list comprehensions
- Class definitions, decorators
- Any Python builtin not explicitly whitelisted
"""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
import ast
import operator
from typing import Any, Callable

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #

# <-------------------- Constantes Locales --------------------> #
MAX_EXPRESSION_LENGTH = 1000
MAX_AST_DEPTH = 50
MAX_FUNCTION_ARGS = 20


def _calculate_ast_depth(node: ast.AST) -> int:
    """Calculate maximum depth of an AST tree."""
    max_depth = 0
    stack: list[tuple[ast.AST, int]] = [(node, 0)]
    while stack:
        current, depth = stack.pop()
        max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(current):
            stack.append((child, depth + 1))
    return max_depth


def validate_expression_complexity(tree: ast.AST, expression: str | None = None) -> None:
    """Validate expression complexity limits for length and AST depth."""
    if expression is not None:
        if not isinstance(expression, str):
            raise ValueError("Expression must be a string.")
        if len(expression) > MAX_EXPRESSION_LENGTH:
            raise ValueError(
                f"Expression too long ({len(expression)} characters). "
                f"Maximum allowed: {MAX_EXPRESSION_LENGTH} characters. "
                "This limit prevents denial-of-service attacks."
            )

    max_depth = _calculate_ast_depth(tree)
    if max_depth > MAX_AST_DEPTH:
        raise ValueError(
            f"Expression too complex: AST depth ({max_depth}) exceeds maximum ({MAX_AST_DEPTH}). "
            "Simplify the expression by breaking it into multiple steps. "
            "This limit prevents stack overflow attacks."
        )


def validate_safe_function_call(func_name: str, args: list[Any]) -> None:
    """Validate that a function call is safe.

    Args:
        func_name: Name of the function being called
        args: Arguments passed to the function

    Raises:
        ValueError: If the function call is unsafe
    """
    if func_name not in SAFE_FUNCTIONS:
        raise ValueError(
            f"Function '{func_name}' is not in the whitelist. Allowed functions: {', '.join(SAFE_FUNCTIONS.keys())}"
        )

    if len(args) > MAX_FUNCTION_ARGS:
        raise ValueError(
            f"Too many arguments ({len(args)}) for function '{func_name}'. Maximum allowed: {MAX_FUNCTION_ARGS}"
        )

    if func_name == "round" and len(args) > 2:
        raise ValueError("round() accepts at most 2 arguments")

    if func_name in ("min", "max") and len(args) < 1:
        raise ValueError(f"{func_name}() requires at least 1 argument")


# Safe operators for expression evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Safe comparison operators for conditional evaluation
COMPARISON_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

# Safe functions for calculations - WHITELIST ONLY
# These are the ONLY functions allowed in formula expressions.
# Adding functions here requires security review.
SAFE_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
}

# Allowed AST node types for security validation - WHITELIST ONLY
# These are the ONLY AST node types allowed in parsed expressions.
# Any other node type will be rejected as a security violation.
# This prevents code injection, attribute access, imports, etc.
ALLOWED_AST_TYPES: tuple[type[ast.AST], ...] = (
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
