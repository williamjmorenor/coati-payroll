# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 - 2026 BMO Soluciones, S.A.
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
"""Schema validation for formula engine calculation rules.

This module provides validation functions for JSON schemas used by the
FormulaEngine to ensure they have the correct structure before execution.
"""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
import ast
from typing import Any, Type

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.enums import StepType

__all__ = ["ValidationError", "validate_schema", "validate_schema_deep"]


class ValidationError(Exception):
    """Exception for validation errors in schema or data."""

    pass


def validate_schema(schema: dict[str, Any], error_class: Type[Exception] = ValidationError) -> None:
    """Validate the calculation schema structure.

    Args:
        schema: The JSON schema to validate

    Raises:
        ValidationError: If schema is missing required fields or has invalid structure
    """
    if not isinstance(schema, dict):
        raise error_class("Schema must be a dictionary")

    # Check for required sections
    if "steps" not in schema:
        raise error_class("Schema must contain 'steps' section")

    # Validate steps structure
    for i, step in enumerate(schema.get("steps", [])):
        if not isinstance(step, dict):
            raise error_class(f"Step {i} must be a dictionary")
        if "name" not in step:
            raise error_class(f"Step {i} must have a 'name' field")
        if "type" not in step:
            raise error_class(f"Step {i} must have a 'type' field")


def validate_schema_deep(schema: dict[str, Any], error_class: Type[Exception] = ValidationError) -> None:
    """Validate the calculation schema structure including formula safety.

    This performs deeper validation than validate_schema, including checking
    formulas for unsafe operations. Use this for API validation endpoints.

    Args:
        schema: The JSON schema to validate
        error_class: Exception class to raise on error

    Raises:
        ValidationError: If schema is invalid or contains unsafe formulas
    """
    # First do basic validation
    validate_schema(schema, error_class)

    # Get valid step types
    valid_step_types = {step_type.value for step_type in StepType}

    # Then validate step types and formulas for safety
    for i, step in enumerate(schema.get("steps", [])):
        step_type = step.get("type")

        # Validate step type
        if step_type not in valid_step_types:
            raise error_class(
                f"Step {i} has invalid type '{step_type}'. Valid types are: {', '.join(valid_step_types)}"
            )

        # Validate formulas for calculation steps
        if step_type == StepType.CALCULATION:
            formula = step.get("formula", "")
            if formula:
                _validate_formula_safety(formula, error_class)

        # Validate conditional step formulas
        if step_type == StepType.CONDITIONAL:
            if_true = step.get("if_true", "")
            if_false = step.get("if_false", "")
            if if_true:
                _validate_formula_safety(if_true, error_class)
            if if_false:
                _validate_formula_safety(if_false, error_class)


def _validate_formula_safety(formula: str, error_class: Type[Exception] = ValidationError) -> None:
    """Validate that a formula doesn't contain unsafe operations.

    Args:
        formula: Formula string to validate
        error_class: Exception class to raise on error

    Raises:
        ValidationError: If formula contains unsafe operations
    """
    if not formula or not isinstance(formula, str):
        return

    try:
        # Parse the formula into an AST
        tree = ast.parse(formula, mode="eval")

        # Check for unsafe operations
        for node in ast.walk(tree.body):
            # Block dangerous operations
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise error_class("Import statements are not allowed in formulas")

            # Block attribute access (prevents __import__, etc.)
            if isinstance(node, ast.Attribute):
                raise error_class("Attribute access is not allowed in formulas")

            # Block function calls to __import__ and other dangerous builtins
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                dangerous_functions = {
                    "__import__",
                    "eval",
                    "exec",
                    "compile",
                    "open",
                    "input",
                    "__builtins__",
                    "globals",
                    "locals",
                    "vars",
                    "dir",
                    "getattr",
                    "setattr",
                    "delattr",
                    "hasattr",
                }
                if func_name in dangerous_functions:
                    raise error_class(f"Function '{func_name}' is not allowed in formulas")
    except SyntaxError as e:
        raise error_class(f"Invalid formula syntax: {e}") from e
