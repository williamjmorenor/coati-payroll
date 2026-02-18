# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Repository for AcumuladoAnual operations."""

from __future__ import annotations

from datetime import date
from typing import Optional

from coati_payroll.model import AcumuladoAnual, Empleado
from .base_repository import BaseRepository


class AcumuladoRepository(BaseRepository[AcumuladoAnual]):
    """Repository for AcumuladoAnual operations."""

    def get_by_id(self, acumulado_id: str) -> Optional[AcumuladoAnual]:
        """Get acumulado by ID."""
        return self.session.get(AcumuladoAnual, acumulado_id)

    def get_or_create(
        self,
        empleado: Empleado,
        tipo_planilla_id: str,
        empresa_id: str,
        periodo_fiscal_inicio: date,
    ) -> AcumuladoAnual:
        """Get or create acumulado for employee and fiscal period."""
        from sqlalchemy import select

        acumulado = (
            self.session.execute(
                select(AcumuladoAnual).filter(
                    AcumuladoAnual.empleado_id == empleado.id,
                    AcumuladoAnual.tipo_planilla_id == tipo_planilla_id,
                    AcumuladoAnual.empresa_id == empresa_id,
                    AcumuladoAnual.periodo_fiscal_inicio == periodo_fiscal_inicio,
                )
            )
            .unique()
            .scalar_one_or_none()
        )

        if not acumulado:
            from decimal import Decimal

            periodo_fiscal_fin = date(
                periodo_fiscal_inicio.year + 1, periodo_fiscal_inicio.month, periodo_fiscal_inicio.day
            )

            salario_inicial_acumulado = Decimal("0.00")
            impuesto_retenido_inicial = Decimal("0.00")
            periodos_iniciales = 0

            if self._is_implementation_fiscal_period(empleado, periodo_fiscal_inicio):
                salario_inicial_acumulado = Decimal(str(empleado.salario_acumulado or 0))
                impuesto_retenido_inicial = Decimal(str(empleado.impuesto_acumulado or 0))
                periodos_iniciales = self._calculate_initial_processed_periods(empleado, periodo_fiscal_inicio)

            acumulado = AcumuladoAnual(
                empleado_id=empleado.id,
                tipo_planilla_id=tipo_planilla_id,
                empresa_id=empresa_id,
                periodo_fiscal_inicio=periodo_fiscal_inicio,
                periodo_fiscal_fin=periodo_fiscal_fin,
                salario_bruto_acumulado=salario_inicial_acumulado,
                salario_gravable_acumulado=Decimal("0.00"),
                deducciones_antes_impuesto_acumulado=Decimal("0.00"),
                impuesto_retenido_acumulado=impuesto_retenido_inicial,
                periodos_procesados=periodos_iniciales,
                salario_acumulado_mes=Decimal("0.00"),
            )
            self.session.add(acumulado)

        return acumulado

    def save(self, acumulado: AcumuladoAnual) -> AcumuladoAnual:
        """Save acumulado."""
        self.session.add(acumulado)
        return acumulado

    def _is_implementation_fiscal_period(self, empleado: Empleado, periodo_fiscal_inicio: date) -> bool:
        """Return True when current fiscal period matches employee implementation year."""
        if not empleado.anio_implementacion_inicial:
            return False

        return int(empleado.anio_implementacion_inicial) == int(periodo_fiscal_inicio.year)

    def _calculate_initial_processed_periods(self, empleado: Empleado, periodo_fiscal_inicio: date) -> int:
        """Calculate closed fiscal periods before first payroll execution in the system."""
        if not empleado.mes_ultimo_cierre:
            return 0

        mes_ultimo_cierre = int(empleado.mes_ultimo_cierre)
        if mes_ultimo_cierre < 1 or mes_ultimo_cierre > 12:
            return 0

        anio_cierre = int(empleado.anio_implementacion_inicial or periodo_fiscal_inicio.year)
        ultimo_cierre = date(anio_cierre, mes_ultimo_cierre, 1)
        fiscal_start = date(periodo_fiscal_inicio.year, periodo_fiscal_inicio.month, 1)

        months = (ultimo_cierre.year - fiscal_start.year) * 12 + (ultimo_cierre.month - fiscal_start.month) + 1
        return max(months, 0)
