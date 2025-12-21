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
"""Schema validation for formula engine calculation rules.

This module provides validation functions for JSON schemas used by the
FormulaEngine to ensure they have the correct structure before execution.
"""

from __future__ import annotations

from typing import Any, Type


class ValidationError(Exception):
    """Exception for validation errors in schema or data.

    Python 3.11+ enhancement: Can use add_note() to append contextual information.
    """

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
