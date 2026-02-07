# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Validator for Planilla."""

from __future__ import annotations

from sqlalchemy import or_, and_

from coati_payroll.audit_helpers import obtener_conceptos_en_borrador
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

        # Check for draft concepts and add warnings (not errors - allow test runs)
        self._check_draft_concepts(planilla, result)

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
                            NominaEstado.CALCULANDO,
                            NominaEstado.GENERADO,
                            NominaEstado.APROBADO,
                            NominaEstado.APLICADO,
                            NominaEstado.PAGADO,
                            NominaEstado.ERROR,
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

    def _check_draft_concepts(self, planilla, result: ValidationResult) -> None:
        """Check for draft concepts and add warnings.

        Draft concepts are allowed in payroll runs (for testing), but we warn
        the user to carefully validate results.
        """
        conceptos_borrador = obtener_conceptos_en_borrador(planilla.id)

        if conceptos_borrador["percepciones"]:
            percepciones_nombres = [p.nombre for p in conceptos_borrador["percepciones"]]
            result.add_warning(
                f"ADVERTENCIA: {len(percepciones_nombres)} percepción(es) en estado BORRADOR: "
                f"{', '.join(percepciones_nombres)}. "
                "Valide cuidadosamente los resultados de la nómina."
            )

        if conceptos_borrador["deducciones"]:
            deducciones_nombres = [d.nombre for d in conceptos_borrador["deducciones"]]
            result.add_warning(
                f"ADVERTENCIA: {len(deducciones_nombres)} deducción(es) en estado BORRADOR: "
                f"{', '.join(deducciones_nombres)}. "
                "Valide cuidadosamente los resultados de la nómina."
            )

        if conceptos_borrador["prestaciones"]:
            prestaciones_nombres = [p.nombre for p in conceptos_borrador["prestaciones"]]
            result.add_warning(
                f"ADVERTENCIA: {len(prestaciones_nombres)} prestación(es) en estado BORRADOR: "
                f"{', '.join(prestaciones_nombres)}. "
                "Valide cuidadosamente los resultados de la nómina."
            )
