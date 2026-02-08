# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
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
from ..exceptions import CalculationError


class VariableStore:
    """Manages variables during formula execution."""

    def __init__(self):
        """Initialize variable store."""
        self.variables: dict[str, Decimal] = {}
        self.results: dict[str, Any] = {}

    def set(self, name: str, value: Decimal, result: Any | None = None) -> None:
        """Set a variable value.

        Args:
            name: Variable name
            value: Variable value
            result: Optional raw result for audit purposes
        """
        if not isinstance(value, Decimal):
            raise CalculationError(f"Variable '{name}' must be Decimal, got {type(value).__name__}")
        self.variables[name] = value
        self.results[name] = result if result is not None else value

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
