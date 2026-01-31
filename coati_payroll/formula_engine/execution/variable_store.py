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
"""Variable store for formula execution."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from decimal import Decimal
from typing import Any

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #


class VariableStore:
    """Manages variables during formula execution."""

    def __init__(self):
        """Initialize variable store."""
        self.variables: dict[str, Decimal] = {}
        self.results: dict[str, Any] = {}

    def set(self, name: str, value: Decimal | Any) -> None:
        """Set a variable value.

        Args:
            name: Variable name
            value: Variable value
        """
        if isinstance(value, Decimal):
            self.variables[name] = value
        else:
            # For complex types like tax lookup results
            self.variables[name] = value.get("tax", Decimal("0")) if isinstance(value, dict) else Decimal("0")
        self.results[name] = value

    def get(self, name: str, default: Decimal = Decimal("0")) -> Decimal:
        """Get a variable value.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value
        """
        return self.variables.get(name, default)

    def clear(self) -> None:
        """Clear all variables and results."""
        self.variables.clear()
        self.results.clear()
