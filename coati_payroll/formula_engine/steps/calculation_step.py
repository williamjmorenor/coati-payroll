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
        evaluator = ExpressionEvaluator(variables=context.variables, trace_callback=context.trace_callback)
        return evaluator.evaluate(formula)
