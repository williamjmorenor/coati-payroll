# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Calculation step implementation."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from decimal import Decimal
from typing import TYPE_CHECKING

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from ..ast.expression_evaluator import ExpressionEvaluator
from .base_step import Step

if TYPE_CHECKING:
    from ..execution.execution_context import ExecutionContext


class CalculationStep(Step):
    """Step for executing mathematical calculations."""

    def execute(self, context: "ExecutionContext") -> Decimal:
        """Execute calculation step.

        Args:
            context: Execution context

        Returns:
            Calculated result as Decimal
        """
        formula = self.config.get("formula", "")
        evaluator = ExpressionEvaluator(
            variables=context.variables,
            trace_callback=context.trace_callback,
            strict_mode=context.strict_mode,
        )
        return evaluator.evaluate(formula)
