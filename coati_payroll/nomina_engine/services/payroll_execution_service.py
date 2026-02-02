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
"""Payroll execution service - main business logic orchestrator."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from coati_payroll.model import db, Planilla, Empleado, Nomina
from coati_payroll.enums import NominaEstado
from coati_payroll.formula_engine import FormulaEngineError
from ..domain.employee_calculation import EmpleadoCalculo
from ..repositories.planilla_repository import PlanillaRepository
from ..repositories.config_repository import ConfigRepository
from ..repositories.exchange_rate_repository import ExchangeRateRepository
from ..repositories.novelty_repository import NoveltyRepository
from ..repositories.acumulado_repository import AcumuladoRepository
from ..validators.planilla_validator import PlanillaValidator
from ..validators.employee_validator import EmployeeValidator
from ..validators import ValidationError, NominaEngineError
from ..calculators.salary_calculator import SalaryCalculator
from ..calculators.exchange_rate_calculator import ExchangeRateCalculator
from ..calculators.concept_calculator import ConceptCalculator
from ..calculators.perception_calculator import PerceptionCalculator
from ..calculators.deduction_calculator import DeductionCalculator
from ..calculators.benefit_calculator import BenefitCalculator
from ..processors.loan_processor import LoanProcessor
from ..processors.accumulation_processor import AccumulationProcessor
from ..processors.vacation_processor import VacationProcessor
from ..processors.novelty_processor import NoveltyProcessor
from ..processors.accounting_processor import AccountingProcessor
from ..services.employee_processing_service import EmployeeProcessingService
from ..services.snapshot_service import SnapshotService
from ..services.accounting_voucher_service import AccountingVoucherService


class PayrollExecutionService:
    """Main service for executing payroll runs."""

    def __init__(self, session):
        self.session = session

        # Initialize repositories
        self.planilla_repo = PlanillaRepository(session)
        self.config_repo = ConfigRepository(session)
        self.exchange_rate_repo = ExchangeRateRepository(session)
        self.novelty_repo = NoveltyRepository(session)
        self.acumulado_repo = AcumuladoRepository(session)

        # Initialize validators
        self.planilla_validator = PlanillaValidator(self.planilla_repo)
        self.employee_validator = EmployeeValidator()

        # Initialize calculators (warnings list will be set later)
        self.salary_calculator = SalaryCalculator(self.config_repo)
        self.exchange_rate_calculator = ExchangeRateCalculator(self.exchange_rate_repo)
        self.concept_calculator = ConceptCalculator(self.config_repo, [])  # warnings set in execute_payroll
        self.perception_calculator = PerceptionCalculator(self.concept_calculator)
        self.deduction_calculator = DeductionCalculator(self.concept_calculator, [])  # warnings set in execute_payroll
        self.benefit_calculator = BenefitCalculator(self.concept_calculator)

        # Initialize processors
        self.novelty_processor = NoveltyProcessor(self.novelty_repo)
        self.accumulation_processor = AccumulationProcessor(self.acumulado_repo)
        self.accounting_processor = AccountingProcessor()

        # Initialize services
        self.employee_processing_service = EmployeeProcessingService(self.config_repo, self.acumulado_repo)
        self.snapshot_service = SnapshotService(session)
        self.accounting_voucher_service = AccountingVoucherService(session)

    def execute_payroll(
        self,
        planilla: Planilla,
        periodo_inicio: date,
        periodo_fin: date,
        fecha_calculo: date,
        usuario: str | None,
    ) -> tuple[Nomina | None, list[EmpleadoCalculo], list[str], list[str]]:
        """Execute a complete payroll run."""
        errors: list[str] = []
        warnings: list[str] = []

        # Update warnings list for calculators (they need shared reference)
        self.concept_calculator.warnings = warnings
        self.deduction_calculator.warnings = warnings

        # Validate planilla
        from ..domain.payroll_context import PayrollContext

        context = PayrollContext(
            planilla_id=planilla.id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_calculo=fecha_calculo,
            usuario=usuario,
        )

        validation_result = self.planilla_validator.validate(context)
        if not validation_result.is_valid:
            errors.extend(validation_result.errors)
            return None, [], errors, warnings

        # Capture configuration snapshots for recalculation consistency
        snapshot = self.snapshot_service.capture_complete_snapshot(planilla, fecha_calculo)

        # Create the Nomina record
        nomina = Nomina(
            planilla_id=planilla.id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            generado_por=usuario,
            estado=NominaEstado.GENERADO,
            total_bruto=Decimal("0.00"),
            total_deducciones=Decimal("0.00"),
            total_neto=Decimal("0.00"),
            fecha_calculo_original=fecha_calculo,
            configuracion_snapshot=snapshot["configuracion"],
            tipos_cambio_snapshot=snapshot["tipos_cambio"],
            catalogos_snapshot=snapshot["catalogos"],
        )
        db.session.add(nomina)
        db.session.flush()

        # Initialize processors that need nomina
        loan_processor = LoanProcessor(nomina, fecha_calculo, periodo_inicio, periodo_fin)
        vacation_processor = VacationProcessor(planilla, periodo_inicio, periodo_fin, usuario, warnings)

        # Update warnings reference for calculators (shared list)
        self.concept_calculator.warnings = warnings
        self.deduction_calculator.warnings = warnings

        # Process each employee
        empleados_calculo: list[EmpleadoCalculo] = []

        for planilla_empleado in planilla.planilla_empleados:
            if not planilla_empleado.activo:
                continue

            empleado = planilla_empleado.empleado
            if not empleado.activo:
                warnings.append(
                    f"Empleado {empleado.primer_nombre} {empleado.primer_apellido} no está activo y será omitido."
                )
                continue

            try:
                emp_calculo = self._process_employee(
                    empleado,
                    planilla,
                    periodo_inicio,
                    periodo_fin,
                    fecha_calculo,
                    nomina,
                    loan_processor,
                    vacation_processor,
                )
                empleados_calculo.append(emp_calculo)
            except (NominaEngineError, FormulaEngineError) as e:
                # Capture all payroll engine and formula errors
                errors.append(
                    f"Error procesando empleado {empleado.primer_nombre} {empleado.primer_apellido}: {str(e)}"
                )
            except Exception as e:
                # Capture any unexpected error to prevent 500 errors
                errors.append(
                    f"Error inesperado procesando empleado {empleado.primer_nombre} {empleado.primer_apellido}: "
                    f"{type(e).__name__}: {str(e)}"
                )

        # Calculate totals
        self._calculate_totals(nomina, empleados_calculo)

        # Update planilla last execution
        planilla.ultima_ejecucion = datetime.now(timezone.utc)

        # Save errors and warnings to log_procesamiento for transparency
        self._save_log_entries(nomina, errors, warnings, empleados_calculo)

        # Generate accounting voucher
        try:
            self.accounting_voucher_service.generate_accounting_voucher(nomina, planilla, fecha_calculo, usuario)
            db.session.flush()
        except Exception as e:
            # Don't fail the payroll if voucher generation fails
            warnings.append(f"Advertencia al generar comprobante contable: {str(e)}")

        return nomina, empleados_calculo, errors, warnings

    def _save_log_entries(
        self,
        nomina: Nomina,
        errors: list[str],
        warnings: list[str],
        empleados_calculo: list[EmpleadoCalculo],
    ) -> None:
        """Save errors, warnings and processing info to nomina.log_procesamiento.

        This ensures all processing issues are visible in the nomina log,
        not just as flash messages.
        """
        log_entries: list[dict[str, Any]] = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Log successful employee processing
        for emp_calculo in empleados_calculo:
            empleado = emp_calculo.empleado
            log_entries.append(
                {
                    "timestamp": timestamp,
                    "empleado": f"{empleado.primer_nombre} {empleado.primer_apellido}",
                    "status": "success",
                    "message": f"Procesado correctamente. Salario neto: {emp_calculo.salario_neto}",
                }
            )

        # Log errors
        for error in errors:
            log_entries.append(
                {
                    "timestamp": timestamp,
                    "empleado": "SISTEMA",
                    "status": "error",
                    "message": error,
                }
            )

        # Log warnings
        for warning in warnings:
            log_entries.append(
                {
                    "timestamp": timestamp,
                    "empleado": "SISTEMA",
                    "status": "warning",
                    "message": warning,
                }
            )

        nomina.log_procesamiento = log_entries

    def _process_employee(
        self,
        empleado: Empleado,
        planilla: Planilla,
        periodo_inicio: date,
        periodo_fin: date,
        fecha_calculo: date,
        nomina: Nomina,
        loan_processor: LoanProcessor,
        vacation_processor: VacationProcessor,
    ) -> EmpleadoCalculo:
        """Process a single employee's payroll."""
        # Validate employee
        employee_validation = self.employee_validator.validate_employee(
            empleado, planilla.empresa_id, periodo_inicio, periodo_fin
        )
        if not employee_validation.is_valid:
            # Include specific validation errors (errors is already a list of strings)
            error_messages = employee_validation.errors
            raise ValidationError(f"Empleado {empleado.codigo_empleado}: {'; '.join(error_messages)}")

        emp_calculo = EmpleadoCalculo(empleado, planilla)

        # Get exchange rate
        emp_calculo.tipo_cambio = self.exchange_rate_calculator.get_exchange_rate(empleado, planilla, fecha_calculo)

        # Apply exchange rate to convert employee salary to planilla currency
        salario_mensual = emp_calculo.salario_base
        if emp_calculo.tipo_cambio != Decimal("1.00"):
            salario_mensual = (salario_mensual * emp_calculo.tipo_cambio).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Calculate salary for the pay period
        emp_calculo.salario_base = self.salary_calculator.calculate_period_salary(
            salario_mensual, planilla, periodo_inicio, periodo_fin, fecha_calculo
        )

        # Store the monthly salary for use in calculations
        emp_calculo.salario_mensual = salario_mensual

        # Load employee novelties
        emp_calculo.novedades = self.novelty_processor.load_novelties(empleado, periodo_inicio, periodo_fin)

        # Build calculation variables
        emp_calculo.variables_calculo = self.employee_processing_service.build_calculation_variables(
            emp_calculo, planilla, periodo_inicio, periodo_fin, fecha_calculo
        )

        # Process perceptions
        percepciones = self.perception_calculator.calculate(emp_calculo, planilla, fecha_calculo)
        emp_calculo.percepciones = percepciones
        emp_calculo.total_percepciones = sum(p.monto for p in percepciones)

        # Calculate gross salary
        emp_calculo.salario_bruto = emp_calculo.salario_base + emp_calculo.total_percepciones

        # Process deductions
        deducciones = self.deduction_calculator.calculate(emp_calculo, planilla, fecha_calculo)
        emp_calculo.deducciones = deducciones
        emp_calculo.total_deducciones = sum(d.monto for d in deducciones)

        # Apply automatic loan/advance deductions
        saldo_disponible = emp_calculo.salario_bruto - emp_calculo.total_deducciones

        loan_deductions = loan_processor.process_loans(
            empleado.id, saldo_disponible, planilla.aplicar_prestamos_automatico, planilla.prioridad_prestamos
        )
        emp_calculo.deducciones.extend(loan_deductions)
        emp_calculo.total_deducciones += sum(d.monto for d in loan_deductions)
        saldo_disponible -= sum(d.monto for d in loan_deductions)

        advance_deductions = loan_processor.process_advances(
            empleado.id, saldo_disponible, planilla.aplicar_adelantos_automatico, planilla.prioridad_adelantos
        )
        emp_calculo.deducciones.extend(advance_deductions)
        emp_calculo.total_deducciones += sum(d.monto for d in advance_deductions)

        # Calculate net salary
        emp_calculo.salario_neto = emp_calculo.salario_bruto - emp_calculo.total_deducciones

        # Ensure net salary is not negative
        # Note: warnings list is shared via loan_processor context, so warnings will be added there
        if emp_calculo.salario_neto < 0:
            emp_calculo.salario_neto = Decimal("0.00")

        # Process employer benefits
        prestaciones = self.benefit_calculator.calculate(emp_calculo, planilla, fecha_calculo)
        emp_calculo.prestaciones = prestaciones
        emp_calculo.total_prestaciones = sum(p.monto for p in prestaciones)

        # Create NominaEmpleado record and update accumulados
        nomina_empleado = self.accounting_processor.create_nomina_empleado(emp_calculo, nomina)

        # Update accumulated annual values
        self.accumulation_processor.update_accumulations(emp_calculo, planilla, periodo_fin, fecha_calculo)

        # Create prestacion accumulation transactions
        self.accounting_processor.create_prestacion_transactions(
            emp_calculo, nomina, planilla, periodo_fin, fecha_calculo
        )

        # Process vacation accrual and usage
        vacation_processor.process_vacations(empleado, emp_calculo, nomina_empleado)

        return emp_calculo

    def _calculate_totals(self, nomina: Nomina, empleados_calculo: list[EmpleadoCalculo]) -> None:
        """Calculate grand totals for the nomina."""
        total_bruto = Decimal("0.00")
        total_deducciones = Decimal("0.00")
        total_neto = Decimal("0.00")

        for emp_calculo in empleados_calculo:
            total_bruto += emp_calculo.salario_bruto
            total_deducciones += emp_calculo.total_deducciones
            total_neto += emp_calculo.salario_neto

        nomina.total_bruto = total_bruto
        nomina.total_deducciones = total_deducciones
        nomina.total_neto = total_neto
