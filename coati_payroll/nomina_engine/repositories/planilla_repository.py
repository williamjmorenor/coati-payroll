# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Repository for Planilla operations."""

from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import joinedload

from coati_payroll.model import Planilla, PlanillaEmpleado, PlanillaIngreso, PlanillaDeduccion, PlanillaPrestacion
from .base_repository import BaseRepository


class PlanillaRepository(BaseRepository[Planilla]):
    """Repository for Planilla operations."""

    def get_by_id(self, planilla_id: str) -> Optional[Planilla]:
        """Get planilla with all necessary relationships loaded."""
        from sqlalchemy import select

        return (
            self.session.execute(
                select(Planilla)
                .options(
                    joinedload(Planilla.tipo_planilla),
                    joinedload(Planilla.moneda),
                    joinedload(Planilla.planilla_empleados).joinedload(PlanillaEmpleado.empleado),
                    joinedload(Planilla.planilla_percepciones).joinedload(PlanillaIngreso.percepcion),
                    joinedload(Planilla.planilla_deducciones).joinedload(PlanillaDeduccion.deduccion),
                    joinedload(Planilla.planilla_prestaciones).joinedload(PlanillaPrestacion.prestacion),
                )
                .filter(Planilla.id == planilla_id)
            )
            .unique()
            .scalar_one_or_none()
        )

    def save(self, planilla: Planilla) -> Planilla:
        """Save planilla."""
        self.session.add(planilla)
        return planilla
