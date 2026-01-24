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
"""Conditional step implementation."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from ..ast.expression_evaluator import ExpressionEvaluator
from ..ast.safe_operators import COMPARISON_OPERATORS
from ..ast.type_converter import to_decimal
from ..exceptions import CalculationError
from .base_step import Step

if TYPE_CHECKING:
    from ..execution.execution_context import ExecutionContext


class ConditionalStep(Step):
    """Step for conditional logic (if/else)."""

    def execute(self, context: "ExecutionContext") -> Decimal:
        """Execute conditional step.

        Args:
            context: Execution context

        Returns:
            Result of selected branch as Decimal
        """
        condition = self.config.get("condition", {})
        if_true = self.config.get("if_true", "0")
        if_false = self.config.get("if_false", "0")

        # Evaluate condition
        condition_result = self._evaluate_condition(condition, context)

        # Select expression based on condition
        selected_value = if_true if condition_result else if_false

        # Evaluate selected expression
        evaluator = ExpressionEvaluator(variables=context.variables, trace_callback=context.trace_callback)
        return evaluator.evaluate(str(selected_value))

    def _evaluate_condition(self, condition: dict[str, Any], context: "ExecutionContext") -> bool:
        """Evaluate a conditional expression.

        Args:
            condition: Dictionary with 'left', 'operator', 'right' keys
            context: Execution context

        Returns:
            Boolean result of the condition

        Raises:
            CalculationError: If condition is invalid
        """
        if not isinstance(condition, dict):
            raise CalculationError("Condition must be a dictionary")

        left = condition.get("left")
        op = condition.get("operator")
        right = condition.get("right")

        if op not in COMPARISON_OPERATORS:
            raise CalculationError(f"Invalid comparison operator: {op}")

        # Resolve variable references
        left_val = self._resolve_value(left, context)
        right_val = self._resolve_value(right, context)
        result = COMPARISON_OPERATORS[op](left_val, right_val)

        if context.trace_callback:
            from coati_payroll.i18n import _

            context.trace_callback(
                _("Condición evaluada: %(left)s %(op)s %(right)s -> %(res)s")
                % {"left": left_val, "op": op, "right": right_val, "res": result}
            )

        return result

    def _resolve_value(self, value: Any, context: "ExecutionContext") -> Decimal:
        """Resolve a value that might be a variable reference.

        Args:
            value: Value or variable name to resolve
            context: Execution context

        Returns:
            Decimal value
        """
        if isinstance(value, str) and value in context.variables:
            resolved = context.variables[value]
            if context.trace_callback:
                from coati_payroll.i18n import _

                context.trace_callback(
                    _("Resolviendo variable '%(name)s' => %(value)s") % {"name": value, "value": resolved}
                )
            return resolved

        resolved_literal = to_decimal(value)
        if context.trace_callback:
            from coati_payroll.i18n import _

            context.trace_callback(
                _("Resolviendo valor literal '%(raw)s' => %(value)s") % {"raw": value, "value": resolved_literal}
            )
        return resolved_literal
