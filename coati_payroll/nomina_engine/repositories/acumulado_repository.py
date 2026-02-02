# SPDX-License-Identifier: Apache-2.0 \r\n # Copyright 2025 - 2026 BMO Soluciones, S.A.
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
            from datetime import date as date_type
            from decimal import Decimal

            periodo_fiscal_fin = date_type(
                periodo_fiscal_inicio.year + 1, periodo_fiscal_inicio.month, periodo_fiscal_inicio.day
            )

            acumulado = AcumuladoAnual(
                empleado_id=empleado.id,
                tipo_planilla_id=tipo_planilla_id,
                empresa_id=empresa_id,
                periodo_fiscal_inicio=periodo_fiscal_inicio,
                periodo_fiscal_fin=periodo_fiscal_fin,
                salario_bruto_acumulado=empleado.salario_acumulado or Decimal("0.00"),
                salario_gravable_acumulado=Decimal("0.00"),
                deducciones_antes_impuesto_acumulado=empleado.impuesto_acumulado or Decimal("0.00"),
                impuesto_retenido_acumulado=Decimal("0.00"),
                periodos_procesados=0,
                salario_acumulado_mes=Decimal("0.00"),
            )
            self.session.add(acumulado)

        return acumulado

    def save(self, acumulado: AcumuladoAnual) -> AcumuladoAnual:
        """Save acumulado."""
        self.session.add(acumulado)
        return acumulado
