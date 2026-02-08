# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Deduction calculator for payroll processing."""

from __future__ import annotations

from datetime import date
from typing import Any, cast

from coati_payroll.model import Planilla
from ..domain.employee_calculation import EmpleadoCalculo
from ..domain.calculation_items import DeduccionItem
from .concept_calculator import ConceptCalculator
from ..results.warning_collector import WarningCollectorProtocol


class DeductionCalculator:
    """Calculator for deductions (salary subtractions)."""

    def __init__(self, concept_calculator: ConceptCalculator, warnings: WarningCollectorProtocol):
        self.concept_calculator = concept_calculator
        self.warnings = warnings

    def calculate(self, emp_calculo: EmpleadoCalculo, planilla: Planilla, fecha_calculo: date) -> list[DeduccionItem]:
        """Calculate all deductions for an employee, applying priority order."""
        deducciones_pendientes: list[DeduccionItem] = []
        planilla_deducciones = cast(list[Any], planilla.planilla_deducciones)

        for planilla_deduccion in planilla_deducciones:
            if not planilla_deduccion.activo:
                continue

            deduccion = planilla_deduccion.deduccion
            if not deduccion or not deduccion.activo:
                continue

            # Check validity dates
            if deduccion.vigente_desde and deduccion.vigente_desde > fecha_calculo:
                continue
            if deduccion.valido_hasta and deduccion.valido_hasta < fecha_calculo:
                continue

            # Calculate deduction amount
            monto = self.concept_calculator.calculate(
                emp_calculo,
                deduccion.formula_tipo,
                deduccion.monto_default,
                deduccion.porcentaje,
                deduccion.formula,
                planilla_deduccion.monto_predeterminado,
                planilla_deduccion.porcentaje,
                codigo_concepto=deduccion.codigo,
                base_calculo=getattr(deduccion, "base_calculo", None),
                unidad_calculo=getattr(deduccion, "unidad_calculo", None),
            )

            if monto > 0:
                item = DeduccionItem(
                    codigo=deduccion.codigo,
                    nombre=deduccion.nombre,
                    monto=monto,
                    prioridad=planilla_deduccion.prioridad,
                    es_obligatoria=planilla_deduccion.es_obligatoria,
                    deduccion_id=deduccion.id,
                )
                deducciones_pendientes.append(item)

        # Sort by priority (lower number = higher priority)
        deducciones_pendientes.sort(key=lambda x: x.prioridad)

        # Apply deductions in priority order
        saldo_disponible = emp_calculo.salario_bruto
        deducciones_aplicadas = []

        for deduccion in deducciones_pendientes:
            monto_aplicar = min(deduccion.monto, saldo_disponible)

            if monto_aplicar <= 0 and not deduccion.es_obligatoria:
                self.warnings.append(
                    f"Empleado {emp_calculo.empleado.primer_nombre} "
                    f"{emp_calculo.empleado.primer_apellido}: "
                    f"Deducción {deduccion.codigo} omitida por saldo insuficiente."
                )
                continue

            item = DeduccionItem(
                codigo=deduccion.codigo,
                nombre=deduccion.nombre,
                monto=monto_aplicar,
                prioridad=deduccion.prioridad,
                es_obligatoria=deduccion.es_obligatoria,
                deduccion_id=deduccion.deduccion_id,
            )
            deducciones_aplicadas.append(item)
            saldo_disponible -= monto_aplicar

        return deducciones_aplicadas
