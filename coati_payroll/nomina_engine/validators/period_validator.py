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
"""Validator for payroll period."""

from __future__ import annotations


from ..domain.payroll_context import PayrollContext
from ..results.validation_result import ValidationResult
from ..validators.base_validator import BaseValidator


class PeriodValidator(BaseValidator):
    """Validates payroll period."""

    def validate(self, context: PayrollContext) -> ValidationResult:
        """Validate period."""
        result = ValidationResult()

        if context.periodo_inicio > context.periodo_fin:
            result.add_error(
                f"Período inválido: inicio ({context.periodo_inicio}) posterior a fin ({context.periodo_fin})"
            )

        dias_periodo = (context.periodo_fin - context.periodo_inicio).days + 1
        if dias_periodo <= 0:
            result.add_error("El período debe tener al menos un día.")
        elif dias_periodo > 366:
            result.add_error(
                f"Período excesivamente largo: {dias_periodo} días. Los períodos no deben exceder 366 días."
            )

        return result
