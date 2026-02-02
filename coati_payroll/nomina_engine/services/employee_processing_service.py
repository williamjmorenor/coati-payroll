# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
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
"""Employee processing service for building calculation variables."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from coati_payroll.model import Empleado, Planilla, AcumuladoAnual
from ..domain.employee_calculation import EmpleadoCalculo
from ..repositories.acumulado_repository import AcumuladoRepository
from ..repositories.config_repository import ConfigRepository


class EmployeeProcessingService:
    """Service for processing employee calculations and building variables."""

    def __init__(
        self,
        config_repository: ConfigRepository,
        acumulado_repository: AcumuladoRepository,
    ):
        self.config_repo = config_repository
        self.acumulado_repo = acumulado_repository

    def build_calculation_variables(
        self,
        emp_calculo: EmpleadoCalculo,
        planilla: Planilla,
        periodo_inicio: date,
        periodo_fin: date,
        fecha_calculo: date,
    ) -> dict[str, Any]:
        """Build the calculation variables for an employee."""
        empleado = emp_calculo.empleado
        tipo_planilla = planilla.tipo_planilla

        config = self.config_repo.get_for_empresa(planilla.empresa_id)

        # Calculate days in period
        dias_periodo = (periodo_fin - periodo_inicio).days + 1

        # Calculate seniority using configuration
        fecha_alta = empleado.fecha_alta or date.today()
        antiguedad_dias = (fecha_calculo - fecha_alta).days
        antiguedad_meses = antiguedad_dias // config.dias_mes_antiguedad
        antiguedad_anios = antiguedad_dias // config.dias_anio_antiguedad

        # Calculate remaining months in fiscal year
        mes_inicio_fiscal = tipo_planilla.mes_inicio_fiscal if tipo_planilla else 1
        meses_restantes = config.meses_anio_financiero - fecha_calculo.month + mes_inicio_fiscal
        if meses_restantes > config.meses_anio_financiero:
            meses_restantes -= config.meses_anio_financiero
        if meses_restantes <= 0:
            meses_restantes = 1

        # Build variables dictionary
        variables = {
            # Employee base data
            "salario_base": emp_calculo.salario_base,
            "salario_mensual": emp_calculo.salario_mensual,
            "tipo_cambio": emp_calculo.tipo_cambio,
            # Period data
            "fecha_calculo": fecha_calculo,
            "periodo_inicio": periodo_inicio,
            "periodo_fin": periodo_fin,
            "dias_periodo": Decimal(str(dias_periodo)),
            # Seniority
            "fecha_alta": fecha_alta,
            "antiguedad_dias": Decimal(str(antiguedad_dias)),
            "antiguedad_meses": Decimal(str(antiguedad_meses)),
            "antiguedad_anios": Decimal(str(antiguedad_anios)),
            # Fiscal calculations
            "meses_restantes": Decimal(str(meses_restantes)),
            "periodos_por_anio": Decimal(
                str(tipo_planilla.periodos_por_anio if tipo_planilla else config.meses_anio_financiero)
            ),
            # Accumulated values (will be populated from AcumuladoAnual)
            "salario_acumulado": Decimal("0.00"),
            "impuesto_acumulado": Decimal("0.00"),
            "ir_retenido_acumulado": Decimal("0.00"),
            "salario_acumulado_mes": Decimal("0.00"),
        }

        # Add employee implementation initial values
        if empleado.salario_acumulado:
            variables["salario_acumulado"] = Decimal(str(empleado.salario_acumulado))
        if empleado.impuesto_acumulado:
            variables["impuesto_acumulado"] = Decimal(str(empleado.impuesto_acumulado))
            variables["ir_retenido_acumulado"] = Decimal(str(empleado.impuesto_acumulado))

        # Add novelties
        for codigo, valor in emp_calculo.novedades.items():
            variables[f"novedad_{codigo}"] = valor

        # Load accumulated annual values
        acumulado = self._get_acumulado_anual(empleado, planilla, fecha_calculo)
        if acumulado:
            variables["salario_acumulado"] += Decimal(str(acumulado.salario_bruto_acumulado or 0))
            variables["impuesto_acumulado"] += Decimal(str(acumulado.impuesto_retenido_acumulado or 0))
            variables["ir_retenido_acumulado"] += Decimal(str(acumulado.impuesto_retenido_acumulado or 0))
            variables["salario_acumulado_mes"] = Decimal(str(acumulado.salario_acumulado_mes or 0))

            # Additional accumulated values for progressive tax calculations
            variables["salario_bruto_acumulado"] = Decimal(str(acumulado.salario_bruto_acumulado or 0))
            variables["salario_gravable_acumulado"] = Decimal(str(acumulado.salario_gravable_acumulado or 0))
            variables["deducciones_antes_impuesto_acumulado"] = Decimal(
                str(acumulado.deducciones_antes_impuesto_acumulado or 0)
            )
            variables["periodos_procesados"] = Decimal(str(acumulado.periodos_procesados or 0))
            variables["meses_trabajados"] = Decimal(str(acumulado.periodos_procesados or 0))

            # Calculate net accumulated salary
            variables["salario_neto_acumulado"] = Decimal(str(acumulado.salario_bruto_acumulado or 0)) - Decimal(
                str(acumulado.deducciones_antes_impuesto_acumulado or 0)
            )

        # Include initial accumulated values from employee
        variables["salario_inicial_acumulado"] = Decimal(str(empleado.salario_acumulado or 0))
        variables["impuesto_inicial_acumulado"] = Decimal(str(empleado.impuesto_acumulado or 0))

        return variables

    def _get_acumulado_anual(
        self, empleado: Empleado, planilla: Planilla, fecha_calculo: date
    ) -> AcumuladoAnual | None:
        """Get accumulated annual values for employee."""
        if not planilla.tipo_planilla:
            return None

        tipo_planilla = planilla.tipo_planilla

        # Calculate fiscal period
        anio = fecha_calculo.year
        mes_inicio = tipo_planilla.mes_inicio_fiscal
        dia_inicio = tipo_planilla.dia_inicio_fiscal

        if fecha_calculo.month < mes_inicio:
            anio -= 1

        periodo_fiscal_inicio = date(anio, mes_inicio, dia_inicio)

        # Look up existing accumulated record
        from sqlalchemy import select
        from coati_payroll.model import db

        acumulado = (
            db.session.execute(
                select(AcumuladoAnual).filter(
                    AcumuladoAnual.empleado_id == empleado.id,
                    AcumuladoAnual.tipo_planilla_id == tipo_planilla.id,
                    AcumuladoAnual.empresa_id == planilla.empresa_id,
                    AcumuladoAnual.periodo_fiscal_inicio == periodo_fiscal_inicio,
                )
            )
            .unique()
            .scalar_one_or_none()
        )

        return acumulado
