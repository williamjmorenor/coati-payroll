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
"""Schema validation for formula engine."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from typing import Any

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.schema_validator import validate_schema
from ..exceptions import ValidationError


class SchemaValidator:
    """Validates formula engine schemas."""

    def validate(self, schema: dict[str, Any]) -> None:
        """Validate a calculation schema.

        Args:
            schema: JSON schema to validate

        Raises:
            ValidationError: If schema is invalid
        """
        validate_schema(schema, error_class=ValidationError)
