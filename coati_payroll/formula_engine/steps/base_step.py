# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Base step interface for Strategy pattern."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, TYPE_CHECKING

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #

if TYPE_CHECKING:
    from ..execution.execution_context import ExecutionContext


class Step(ABC):
    """Base interface for all step types."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize step.

        Args:
            name: Step name
            config: Step configuration dictionary
        """
        self.name = name
        self.config = config

    @abstractmethod
    def execute(self, context: "ExecutionContext") -> Any:
        """Execute the step and return result.

        Args:
            context: Execution context with variables and tax tables

        Returns:
            Step execution result
        """
        pass

    def get_variable_value(self, result: Any) -> Decimal:
        """Return the Decimal value to store for this step."""
        from ..exceptions import CalculationError

        if not isinstance(result, Decimal):
            raise CalculationError(f"Step '{self.name}' must return Decimal, got {type(result).__name__}")
        return result
