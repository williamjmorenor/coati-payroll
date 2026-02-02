# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Vacation processor for vacation accrual and usage."""

from __future__ import annotations

from coati_payroll.model import Planilla, Empleado, NominaEmpleado
from coati_payroll.log import log
from ..domain.employee_calculation import EmpleadoCalculo


class VacationProcessor:
    """Processor for vacation accrual and usage."""

    def __init__(
        self, planilla: Planilla, periodo_inicio, periodo_fin, usuario: str | None = None, warnings: list[str] = None
    ):
        self.planilla = planilla
        self.periodo_inicio = periodo_inicio
        self.periodo_fin = periodo_fin
        self.usuario = usuario
        self.warnings = warnings or []

    def process_vacations(
        self, empleado: Empleado, emp_calculo: EmpleadoCalculo, nomina_empleado: NominaEmpleado
    ) -> None:
        """Process vacation accrual and usage for an employee."""
        try:
            from coati_payroll.vacation_service import VacationService

            vacation_service = VacationService(
                planilla=self.planilla,
                periodo_inicio=self.periodo_inicio,
                periodo_fin=self.periodo_fin,
            )

            # Accumulate vacation time
            vacation_service.acumular_vacaciones_empleado(
                empleado=empleado,
                nomina_empleado=nomina_empleado,
                usuario=self.usuario,
            )

            # Process vacation novelties (time off taken)
            vacation_service.procesar_novedades_vacaciones(
                empleado=empleado,
                novedades=emp_calculo.novedades,
                usuario=self.usuario,
            )

        except Exception as e:
            log.error(f"Error procesando vacaciones para empleado {empleado.codigo_empleado}: {str(e)}")
            self.warnings.append(
                f"No se pudieron procesar vacaciones para {empleado.primer_nombre} "
                f"{empleado.primer_apellido}: {str(e)}"
            )
