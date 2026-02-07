# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Salary calculator for payroll processing."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from types import SimpleNamespace

from coati_payroll.model import Planilla, ConfiguracionCalculos
from ..repositories.config_repository import ConfigRepository


class SalaryCalculator:
    """Calculator for salary period calculations."""

    def __init__(self, config_repository: ConfigRepository):
        self.config_repo = config_repository

    def calculate_period_salary(
        self,
        salario_mensual: Decimal,
        planilla: Planilla,
        periodo_inicio: date,
        periodo_fin: date,
        fecha_calculo: date,
        configuracion_snapshot: dict[str, Any] | None = None,
        rounding: bool = True,
    ) -> Decimal:
        """Calculate salary for the pay period based on actual days."""
        if not planilla or not planilla.tipo_planilla:
            return salario_mensual

        if not periodo_fin or not periodo_inicio:
            return salario_mensual

        dias_periodo = (periodo_fin - periodo_inicio).days + 1

        if dias_periodo <= 0:
            from ..validators import ValidationError

            raise ValidationError(f"Período inválido: inicio ({periodo_inicio}) posterior a fin ({periodo_fin})")
        if dias_periodo > 366:
            from ..validators import ValidationError

            raise ValidationError(
                f"Período excesivamente largo: {dias_periodo} días. Los períodos no deben exceder 366 días."
            )

        tipo_planilla = planilla.tipo_planilla
        periodicidad = tipo_planilla.periodicidad.lower() if tipo_planilla.periodicidad else ""

        if periodicidad == "mensual":
            is_first_of_month = periodo_inicio.day == 1
            next_day = periodo_fin + timedelta(days=1)
            is_last_of_month = next_day.day == 1
            same_month = periodo_inicio.year == periodo_fin.year and periodo_inicio.month == periodo_fin.month

            if is_first_of_month and is_last_of_month and same_month:
                return salario_mensual

        elif periodicidad == "quincenal":
            config = self._get_config(planilla.empresa_id, configuracion_snapshot)
            dias_configurados = tipo_planilla.dias or config.dias_quincena
            if dias_periodo == dias_configurados:
                divisor = Decimal(str(config.dias_mes_nomina)) / Decimal(str(config.dias_quincena))
                salario_periodo = salario_mensual / divisor
                if rounding:
                    return salario_periodo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                return salario_periodo

        config = self._get_config(planilla.empresa_id, configuracion_snapshot)
        dias_base = Decimal(str(config.dias_mes_nomina))
        salario_diario = salario_mensual / dias_base
        salario_periodo = salario_diario * Decimal(str(dias_periodo))
        if rounding:
            salario_diario = salario_diario.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            salario_periodo = salario_periodo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return salario_periodo

    def _get_config(self, empresa_id: str, configuracion_snapshot: dict[str, Any] | None) -> Any:
        if configuracion_snapshot:
            return SimpleNamespace(**configuracion_snapshot)

        return self.config_repo.get_for_empresa(empresa_id)

    def calculate_hourly_rate(self, salario_mensual: Decimal, config: ConfiguracionCalculos) -> Decimal:
        """Calculate hourly rate from monthly salary."""
        dias_base = Decimal(str(config.dias_mes_nomina))
        horas_dia = Decimal(str(config.horas_jornada_diaria))
        return (salario_mensual / dias_base / horas_dia).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
