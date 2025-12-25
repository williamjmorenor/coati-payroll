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
"""Validator for Planilla."""

from __future__ import annotations

from sqlalchemy import or_, and_

from coati_payroll.model import Nomina
from coati_payroll.enums import NominaEstado
from ..domain.payroll_context import PayrollContext
from ..results.validation_result import ValidationResult
from ..validators.base_validator import BaseValidator
from ..repositories.planilla_repository import PlanillaRepository


class PlanillaValidator(BaseValidator):
    """Validates that a planilla is ready for execution."""

    def __init__(self, planilla_repository: PlanillaRepository):
        self.planilla_repo = planilla_repository

    def validate(self, context: PayrollContext) -> ValidationResult:
        """Validate planilla."""
        result = ValidationResult()

        planilla = self.planilla_repo.get_by_id(context.planilla_id)
        if not planilla:
            result.add_error("La planilla no existe.")
            return result

        if not planilla.activo:
            result.add_error("La planilla no está activa.")

        if not planilla.planilla_empleados:
            result.add_error("La planilla no tiene empleados asignados.")

        if not planilla.tipo_planilla:
            result.add_error("La planilla no tiene tipo de planilla configurado.")

        if not planilla.moneda:
            result.add_error("La planilla no tiene moneda configurada.")

        # Validate period not duplicated
        if not self._validate_periodo_no_duplicado(planilla, context):
            result.add_error("El período se solapa con una nómina existente.")

        return result

    def _validate_periodo_no_duplicado(self, planilla, context: PayrollContext) -> bool:
        """Validate that period doesn't overlap with existing nominas."""
        from sqlalchemy import select

        existing = (
            self.planilla_repo.session.execute(
                select(Nomina).filter(
                    Nomina.planilla_id == planilla.id,
                    Nomina.estado.in_(
                        [
                            NominaEstado.GENERADO,
                            NominaEstado.APROBADO,
                            NominaEstado.APLICADO,
                            NominaEstado.PAGADO,
                        ]
                    ),
                    or_(
                        # Existing start falls within our period
                        and_(
                            Nomina.periodo_inicio >= context.periodo_inicio,
                            Nomina.periodo_inicio <= context.periodo_fin,
                        ),
                        # Existing end falls within our period
                        and_(
                            Nomina.periodo_fin >= context.periodo_inicio,
                            Nomina.periodo_fin <= context.periodo_fin,
                        ),
                        # Our period is completely within existing period
                        and_(
                            Nomina.periodo_inicio <= context.periodo_inicio,
                            Nomina.periodo_fin >= context.periodo_fin,
                        ),
                    ),
                )
            )
            .scalars()
            .first()
        )

        return existing is None
