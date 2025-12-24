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
"""Payroll execution engine for processing planillas and generating nominas.

This module provides the engine for executing payroll runs. It takes a configured
Planilla and processes all associated employees, applying perceptions, deductions,
and benefits according to their formulas and priorities.

Key features:
- Processes perceptions (add to gross salary)
- Processes deductions (subtract from net salary) in priority order
- Calculates employer benefits (prestaciones) separately
- Applies automatic loan/advance deductions
- Updates accumulated annual values
- Generates NominaEmpleado and NominaDetalle records
"""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, NamedTuple

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #


# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from coati_payroll.enums import AdelantoEstado, FormulaType, NominaEstado
from coati_payroll.i18n import _
from coati_payroll.model import (
    db,
    Planilla,
    Empleado,
    Nomina,
    NominaEmpleado,
    NominaDetalle,
    NominaNovedad,
    Deduccion,
    Adelanto,
    AdelantoAbono,
    AcumuladoAnual,
    TipoCambio,
    Prestacion,
    PrestacionAcumulada,
    ReglaCalculo,
)
from coati_payroll.formula_engine import FormulaEngine, FormulaEngineError
from coati_payroll.log import TRACE_LEVEL_NUM, is_trace_enabled, log

# Constants for payroll calculations
HORAS_TRABAJO_DIA = Decimal("8.00")  # Standard 8-hour workday for hourly rate calculations


class NominaEngineError(Exception):
    """Base exception for payroll engine errors."""

    pass


class ValidationError(NominaEngineError):
    """Exception for validation errors."""

    pass


class CalculationError(NominaEngineError):
    """Exception for calculation errors."""

    pass


class DeduccionItem(NamedTuple):
    """Represents a deduction to be applied."""

    codigo: str
    nombre: str
    monto: Decimal
    prioridad: int
    es_obligatoria: bool
    deduccion_id: str | None = None
    tipo: str = "deduccion"  # deduccion, prestamo, adelanto


class PercepcionItem(NamedTuple):
    """Represents a perception to be applied."""

    codigo: str
    nombre: str
    monto: Decimal
    orden: int
    gravable: bool
    percepcion_id: str | None = None


class PrestacionItem(NamedTuple):
    """Represents an employer benefit to be calculated."""

    codigo: str
    nombre: str
    monto: Decimal
    orden: int
    prestacion_id: str | None = None


class EmpleadoCalculo:
    """Container for employee calculation data during payroll processing."""

    def __init__(self, empleado: Empleado, planilla: Planilla):
        self.empleado = empleado
        self.planilla = planilla
        self.salario_base = Decimal(str(empleado.salario_base or 0))
        self.salario_mensual = Decimal(str(empleado.salario_base or 0))
        self.percepciones: list[PercepcionItem] = []
        self.deducciones: list[DeduccionItem] = []
        self.prestaciones: list[PrestacionItem] = []
        self.total_percepciones = Decimal("0.00")
        self.total_deducciones = Decimal("0.00")
        self.total_prestaciones = Decimal("0.00")
        self.salario_bruto = Decimal("0.00")
        self.salario_neto = Decimal("0.00")
        self.tipo_cambio = Decimal("1.00")
        self.moneda_origen_id = empleado.moneda_id
        self.novedades: dict[str, Decimal] = {}
        self.variables_calculo: dict[str, Any] = {}


class NominaEngine:
    """Engine for executing payroll runs.

    This engine processes a Planilla configuration and generates a complete
    Nomina with all employee calculations. It handles:

    1. Perceptions (ingresos) - add to gross salary
    2. Deductions (deducciones) - subtract from net salary, in priority order
    3. Benefits (prestaciones) - employer costs, don't affect employee pay
    4. Automatic deductions - loans and advances from Adelanto table
    5. Accumulated annual values - for progressive tax calculations
    """

    def __init__(
        self,
        planilla: Planilla,
        periodo_inicio: date,
        periodo_fin: date,
        fecha_calculo: date | None = None,
        usuario: str | None = None,
    ):
        """Initialize the payroll engine.

        Args:
            planilla: The Planilla to execute
            periodo_inicio: Start date of the payroll period
            periodo_fin: End date of the payroll period
            fecha_calculo: Date of calculation (defaults to today)
            usuario: Username executing the payroll
        """
        self.planilla = planilla
        self.periodo_inicio = periodo_inicio
        self.periodo_fin = periodo_fin
        self.fecha_calculo = fecha_calculo or date.today()
        self.usuario = usuario
        self.nomina: Nomina | None = None
        self.empleados_calculo: list[EmpleadoCalculo] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []

    # ------------------------------------------------------------------
    # Trace helper uses cached check from log.is_trace_enabled() to avoid
    # recomputing debug/level state on every call.
    # ------------------------------------------------------------------
    def _trace(self, message: str) -> None:
        if is_trace_enabled():
            log.log(TRACE_LEVEL_NUM, message)

    def validar_planilla(self) -> bool:
        """Validate that the planilla is ready for execution.

        Returns:
            True if valid, False otherwise
        """
        if not self.planilla.activo:
            self.errors.append("La planilla no está activa.")
            return False

        if not self.planilla.planilla_empleados:
            self.errors.append("La planilla no tiene empleados asignados.")
            return False

        if not self.planilla.tipo_planilla:
            self.errors.append("La planilla no tiene un tipo de planilla configurado.")
            return False

        if not self.planilla.moneda:
            self.errors.append("La planilla no tiene una moneda configurada.")
            return False

        # Validate that there are no overlapping payroll periods already paid
        # CRITICAL: Prevents paying the same days multiple times
        if not self._validar_periodo_no_duplicado():
            return False

        return True

    def _validar_periodo_no_duplicado(self) -> bool:
        """Validate that the payroll period doesn't overlap with existing paid payrolls.

        This is CRITICAL to prevent paying employees twice for the same days.

        Returns:
            True if no overlap exists, False if overlap detected
        """
        # Query for existing nominas for this planilla that overlap with the period
        # An overlap exists if:
        # - Existing nomina's start date is within our period, OR
        # - Existing nomina's end date is within our period, OR
        # - Our period is completely contained within an existing nomina's period
        #
        # We check all active states (GENERADO, APROBADO, APLICADO, PAGADO) but exclude
        # ANULADO (cancelled) and ERROR states since those don't represent actual payments
        existing_nominas = (
            db.session.execute(
                db.select(Nomina).filter(
                    Nomina.planilla_id == self.planilla.id,
                    Nomina.estado.in_(
                        [NominaEstado.GENERADO, NominaEstado.APROBADO, NominaEstado.APLICADO, NominaEstado.PAGADO]
                    ),
                    db.or_(
                        # Existing start falls within our period
                        db.and_(
                            Nomina.periodo_inicio >= self.periodo_inicio, Nomina.periodo_inicio <= self.periodo_fin
                        ),
                        # Existing end falls within our period
                        db.and_(Nomina.periodo_fin >= self.periodo_inicio, Nomina.periodo_fin <= self.periodo_fin),
                        # Our period is completely within existing period
                        db.and_(Nomina.periodo_inicio <= self.periodo_inicio, Nomina.periodo_fin >= self.periodo_fin),
                    ),
                )
            )
            .scalars()
            .all()
        )

        if existing_nominas:
            for nomina in existing_nominas:
                self.errors.append(
                    f"El período {self.periodo_inicio} al {self.periodo_fin} se solapa con "
                    f"una nómina existente (ID: {nomina.id}) del {nomina.periodo_inicio} al "
                    f"{nomina.periodo_fin} en estado {nomina.estado}. "
                    f"No se puede procesar la misma fecha en múltiples nóminas."
                )
            return False

        return True

    def ejecutar(self) -> Nomina | None:
        """Execute the payroll run.

        Returns:
            The generated Nomina record, or None if execution failed
        """
        # Validate planilla
        if not self.validar_planilla():
            return None

        # Create the Nomina record
        self.nomina = Nomina(
            planilla_id=self.planilla.id,
            periodo_inicio=self.periodo_inicio,
            periodo_fin=self.periodo_fin,
            generado_por=self.usuario,
            estado=NominaEstado.GENERADO,
            total_bruto=Decimal("0.00"),
            total_deducciones=Decimal("0.00"),
            total_neto=Decimal("0.00"),
        )
        db.session.add(self.nomina)
        db.session.flush()  # Get the ID

        # Process each employee
        for planilla_empleado in self.planilla.planilla_empleados:
            if not planilla_empleado.activo:
                continue

            empleado = planilla_empleado.empleado
            if not empleado.activo:
                self.warnings.append(
                    f"Empleado {empleado.primer_nombre} {empleado.primer_apellido} " f"no está activo y será omitido."
                )
                continue

            try:
                emp_calculo = self._procesar_empleado(empleado)
                self.empleados_calculo.append(emp_calculo)
            except (NominaEngineError, FormulaEngineError) as e:
                self.errors.append(
                    f"Error procesando empleado {empleado.primer_nombre} " f"{empleado.primer_apellido}: {str(e)}"
                )

        # Calculate totals
        self._calcular_totales()

        # Update planilla last execution
        self.planilla.ultima_ejecucion = datetime.now(timezone.utc)

        # Commit the transaction
        db.session.commit()

        return self.nomina

    def _validar_empleado_para_pago(self, empleado: Empleado) -> tuple[bool, list[str]]:
        """Validate that an employee is eligible for payroll processing.

        CRITICAL validations to prevent incorrect payments.

        Args:
            empleado: Employee to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # 1. Employee must be active
        if not empleado.activo:
            errors.append(f"Empleado {empleado.codigo_empleado} no está activo")

        # 2. Employee must have valid hire date (not in future, not after period)
        if empleado.fecha_alta:
            if empleado.fecha_alta > date.today():
                errors.append(
                    f"Empleado {empleado.codigo_empleado}: fecha de ingreso ({empleado.fecha_alta}) "
                    f"es posterior a la fecha actual"
                )
            if empleado.fecha_alta > self.periodo_fin:
                errors.append(
                    f"Empleado {empleado.codigo_empleado}: fecha de ingreso ({empleado.fecha_alta}) "
                    f"es posterior al período a procesar ({self.periodo_fin})"
                )
        else:
            errors.append(f"Empleado {empleado.codigo_empleado} no tiene fecha de ingreso definida")

        # 3. If employee has termination date, validate it's not before period
        if empleado.fecha_baja:
            if empleado.fecha_baja < self.periodo_inicio:
                errors.append(
                    f"Empleado {empleado.codigo_empleado}: fecha de salida ({empleado.fecha_baja}) "
                    f"es anterior al inicio del período ({self.periodo_inicio})"
                )

        # 4. Employee must have unique identification
        if not empleado.identificacion_personal:
            errors.append(f"Empleado {empleado.codigo_empleado} no tiene identificación personal")

        # 5. Employee must have a valid base salary
        if empleado.salario_base <= Decimal("0.00"):
            errors.append(f"Empleado {empleado.codigo_empleado} tiene salario base inválido ({empleado.salario_base})")

        # 6. Employee must be assigned to active company
        if not empleado.empresa_id:
            errors.append(f"Empleado {empleado.codigo_empleado} no está asignado a ninguna empresa")

        # 7. Employee must belong to the same company as the planilla
        if self.planilla.empresa_id and empleado.empresa_id:
            if empleado.empresa_id != self.planilla.empresa_id:
                errors.append(
                    f"Empleado {empleado.codigo_empleado} pertenece a empresa diferente a la planilla. "
                    f"Empleado empresa_id={empleado.empresa_id}, Planilla empresa_id={self.planilla.empresa_id}"
                )

        # 8. Employee must have currency defined
        if not empleado.moneda_id:
            errors.append(f"Empleado {empleado.codigo_empleado} no tiene moneda definida")

        return (len(errors) == 0, errors)

    def _procesar_empleado(self, empleado: Empleado) -> EmpleadoCalculo:
        """Process a single employee's payroll.

        Args:
            empleado: The employee to process

        Returns:
            EmpleadoCalculo with all calculations
        """
        # CRITICAL: Validate employee before processing
        is_valid, validation_errors = self._validar_empleado_para_pago(empleado)
        if not is_valid:
            for error in validation_errors:
                self.errors.append(error)
            raise ValidationError(f"Empleado {empleado.codigo_empleado} no cumple validaciones requeridas")

        emp_calculo = EmpleadoCalculo(empleado, self.planilla)

        self._trace(
            _("Calculando nómina del empleado %(id)s (%(nombre)s %(apellido)s)")
            % {
                "id": empleado.id,
                "nombre": empleado.primer_nombre,
                "apellido": empleado.primer_apellido,
            }
        )
        self._trace(_("Obteniendo salario base %(salario)s") % {"salario": emp_calculo.salario_base})

        # Get exchange rate if currencies differ
        emp_calculo.tipo_cambio = self._obtener_tipo_cambio(empleado)
        self._trace(_("Aplicando tipo de cambio %(tasa)s") % {"tasa": emp_calculo.tipo_cambio})

        # Apply exchange rate to convert employee salary to planilla currency
        # Only convert when employee currency differs from planilla currency
        salario_mensual = emp_calculo.salario_base
        if emp_calculo.tipo_cambio != Decimal("1.00"):
            salario_mensual = (salario_mensual * emp_calculo.tipo_cambio).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        self._trace(_("Salario mensual convertido: %(salario)s") % {"salario": salario_mensual})

        # Calculate salary for the pay period based on actual days worked
        # The employee's salario_base is always the monthly salary
        # We need to convert it to the actual period salary based on days
        emp_calculo.salario_base = self._calcular_salario_periodo(salario_mensual)
        self._trace(
            _("Salario base del período (%(inicio)s a %(fin)s): %(salario)s")
            % {
                "inicio": self.periodo_inicio,
                "fin": self.periodo_fin,
                "salario": emp_calculo.salario_base,
            }
        )

        # Store the monthly salary for use in calculations (e.g., hourly rate)
        emp_calculo.salario_mensual = salario_mensual

        # Load employee novelties for this period
        emp_calculo.novedades = self._cargar_novedades(empleado)

        # Build calculation variables
        emp_calculo.variables_calculo = self._construir_variables(emp_calculo)

        # Process perceptions (add to gross salary)
        self._procesar_percepciones(emp_calculo)

        self._trace(_("Total percepciones después de cálculo: %(total)s") % {"total": emp_calculo.total_percepciones})

        # Calculate gross salary
        emp_calculo.salario_bruto = emp_calculo.salario_base + emp_calculo.total_percepciones
        self._trace(
            _("Salario bruto = base (%(base)s) + percepciones (%(percepciones)s)")
            % {"base": emp_calculo.salario_base, "percepciones": emp_calculo.total_percepciones}
        )

        # Process deductions (subtract from net salary)
        self._procesar_deducciones(emp_calculo)

        # Apply automatic loan/advance deductions
        self._aplicar_deducciones_automaticas(emp_calculo)

        # Calculate net salary
        emp_calculo.salario_neto = emp_calculo.salario_bruto - emp_calculo.total_deducciones
        self._trace(
            _("Salario neto = bruto (%(bruto)s) - deducciones (%(deducciones)s) = %(neto)s")
            % {
                "bruto": emp_calculo.salario_bruto,
                "deducciones": emp_calculo.total_deducciones,
                "neto": emp_calculo.salario_neto,
            }
        )

        # Ensure net salary is not negative
        if emp_calculo.salario_neto < 0:
            exceso_deducciones = emp_calculo.total_deducciones - emp_calculo.salario_bruto
            self.warnings.append(
                f"Empleado {empleado.primer_nombre} {empleado.primer_apellido}: "
                f"Las deducciones totales ({emp_calculo.total_deducciones}) exceden el salario bruto "
                f"({emp_calculo.salario_bruto}) por {exceso_deducciones}. "
                f"Salario neto ajustado a 0.00. Revise las deducciones para este empleado."
            )
            emp_calculo.salario_neto = Decimal("0.00")

        # Process employer benefits (don't affect employee pay)
        self._procesar_prestaciones(emp_calculo)

        # Create NominaEmpleado record and update accumulados only if nomina exists
        # (When processing in background, nomina records are created externally)
        if self.nomina:
            nomina_empleado = self._crear_nomina_empleado(emp_calculo)
            # Update accumulated annual values
            self._actualizar_acumulados(emp_calculo, nomina_empleado)
            # Create prestacion accumulation transactions
            self._crear_transacciones_prestaciones(emp_calculo, nomina_empleado)
            # Process vacation accrual and usage
            self._procesar_vacaciones(empleado, emp_calculo, nomina_empleado)

        return emp_calculo

    def _calcular_salario_periodo(self, salario_mensual: Decimal) -> Decimal:
        """Calculate the salary for the pay period based on actual days.

        The employee's base salary is always monthly. This method converts it
        to the actual period salary by calculating the daily salary and
        multiplying by the number of days in the current payroll period.

        Formula:
        - Daily salary = Monthly salary / 30 (always use 30-day month)
        - Period salary = Daily salary × actual days in period

        Args:
            salario_mensual: The monthly salary (already in planilla currency)

        Returns:
            The prorated salary for this pay period
        """
        if not self.planilla or not self.planilla.tipo_planilla:
            return salario_mensual

        # Validate period dates
        if not self.periodo_fin or not self.periodo_inicio:
            return salario_mensual

        # Calculate actual days in this pay period
        dias_periodo = (self.periodo_fin - self.periodo_inicio).days + 1

        # CRITICAL VALIDATION: Period days must be positive and reasonable
        if dias_periodo <= 0:
            raise ValidationError(
                f"Período inválido: inicio ({self.periodo_inicio}) posterior a fin ({self.periodo_fin})"
            )
        if dias_periodo > 366:  # More than a year
            raise ValidationError(
                f"Período excesivamente largo: {dias_periodo} días. " f"Los períodos no deben exceder 366 días."
            )

        # Handle salary based on periodicidad (pay frequency)
        tipo_planilla = self.planilla.tipo_planilla
        periodicidad = tipo_planilla.periodicidad.lower() if tipo_planilla.periodicidad else ""

        if periodicidad == "mensual":
            # For monthly payrolls covering a full calendar month, return full salary
            # A full calendar month: starts on 1st day AND ends on last day of same month
            is_first_of_month = self.periodo_inicio.day == 1
            next_day = self.periodo_fin + timedelta(days=1)
            is_last_of_month = next_day.day == 1
            same_month = (
                self.periodo_inicio.year == self.periodo_fin.year
                and self.periodo_inicio.month == self.periodo_fin.month
            )

            if is_first_of_month and is_last_of_month and same_month:
                return salario_mensual

        elif periodicidad == "quincenal":
            # For biweekly payrolls (24 periods/year), salary is monthly / 2
            # when period matches configured days (typically 15)
            dias_configurados = tipo_planilla.dias or 15
            if dias_periodo == dias_configurados:
                return (salario_mensual / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Always use 30 days as the base for salary proration
        # This ensures consistent daily rates regardless of payroll type
        dias_base = Decimal("30")

        # Calculate daily salary
        salario_diario = (salario_mensual / dias_base).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate period salary
        salario_periodo = (salario_diario * Decimal(str(dias_periodo))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return salario_periodo

    def _obtener_tipo_cambio(self, empleado: Empleado) -> Decimal:
        """Get the exchange rate for the employee's salary currency.

        Args:
            empleado: The employee

        Returns:
            Exchange rate (1.0 if same currency or no conversion needed)
        """
        if not empleado.moneda_id:
            return Decimal("1.00")

        if empleado.moneda_id == self.planilla.moneda_id:
            return Decimal("1.00")

        # Look up exchange rate
        tipo_cambio = db.session.execute(
            db.select(TipoCambio)
            .filter(
                TipoCambio.moneda_origen_id == empleado.moneda_id,
                TipoCambio.moneda_destino_id == self.planilla.moneda_id,
                TipoCambio.fecha <= self.fecha_calculo,
            )
            .order_by(TipoCambio.fecha.desc())
        ).scalar()

        if tipo_cambio:
            return Decimal(str(tipo_cambio.tasa))

        raise CalculationError(
            f"No se encontró tipo de cambio para empleado "
            f"{empleado.primer_nombre} {empleado.primer_apellido}. "
            f"Se requiere un tipo de cambio de {empleado.moneda.codigo if empleado.moneda else 'desconocido'} "
            f"a {self.planilla.moneda.codigo if self.planilla.moneda else 'desconocido'}."
        )

    def _cargar_novedades(self, empleado: Empleado) -> dict[str, Decimal]:
        """Load novelties for the employee in this period.

        Novedades are loaded based on:
        1. Employee ID
        2. Date range (fecha_novedad falls within the payroll period)

        This ensures novedades are correctly applied to the period they occur in,
        regardless of which specific nomina execution they were originally
        associated with.

        Note: Each novedad still maintains a relationship (nomina_id) with the
        nomina where it was created for audit trail purposes. However, for
        calculation purposes, we filter by period dates to ensure consistent
        results when recalculating payrolls.

        Args:
            empleado: The employee

        Returns:
            Dictionary of novelty code -> value
        """
        novedades: dict[str, Decimal] = {}

        # Query novelties for this employee within the payroll period dates
        # We filter by fecha_novedad to ensure the novedad falls within the period
        nomina_novedades = (
            db.session.execute(
                db.select(NominaNovedad).filter(
                    NominaNovedad.empleado_id == empleado.id,
                    NominaNovedad.fecha_novedad >= self.periodo_inicio,
                    NominaNovedad.fecha_novedad <= self.periodo_fin,
                )
            )
            .scalars()
            .all()
        )

        for novedad in nomina_novedades:
            codigo = novedad.codigo_concepto
            valor = Decimal(str(novedad.valor_cantidad or 0))
            novedades[codigo] = novedades.get(codigo, Decimal("0")) + valor

        return novedades

    def _construir_variables(self, emp_calculo: EmpleadoCalculo) -> dict[str, Any]:
        """Build the calculation variables for an employee.

        Args:
            emp_calculo: Employee calculation container

        Returns:
            Dictionary of variable name -> value
        """
        empleado = emp_calculo.empleado
        tipo_planilla = self.planilla.tipo_planilla

        # Calculate days in period
        dias_periodo = (self.periodo_fin - self.periodo_inicio).days + 1

        # Calculate seniority
        fecha_alta = empleado.fecha_alta or date.today()
        antiguedad_dias = (self.fecha_calculo - fecha_alta).days
        antiguedad_meses = antiguedad_dias // 30
        antiguedad_anios = antiguedad_dias // 365

        # Calculate remaining months in fiscal year
        mes_inicio_fiscal = tipo_planilla.mes_inicio_fiscal if tipo_planilla else 1
        meses_restantes = 12 - self.fecha_calculo.month + mes_inicio_fiscal
        if meses_restantes > 12:
            meses_restantes -= 12
        if meses_restantes <= 0:
            meses_restantes = 1

        # Build variables dictionary
        variables = {
            # Employee base data
            "salario_base": emp_calculo.salario_base,
            "salario_mensual": emp_calculo.salario_mensual,
            "tipo_cambio": emp_calculo.tipo_cambio,
            # Period data
            "fecha_calculo": self.fecha_calculo,
            "periodo_inicio": self.periodo_inicio,
            "periodo_fin": self.periodo_fin,
            "dias_periodo": Decimal(str(dias_periodo)),
            # Seniority
            "fecha_alta": fecha_alta,
            "antiguedad_dias": Decimal(str(antiguedad_dias)),
            "antiguedad_meses": Decimal(str(antiguedad_meses)),
            "antiguedad_anios": Decimal(str(antiguedad_anios)),
            # Fiscal calculations
            "meses_restantes": Decimal(str(meses_restantes)),
            "periodos_por_anio": Decimal(str(tipo_planilla.periodos_por_anio if tipo_planilla else 12)),
            # Accumulated values (will be populated from AcumuladoAnual)
            "salario_acumulado": Decimal("0.00"),
            "impuesto_acumulado": Decimal("0.00"),
            "ir_retenido_acumulado": Decimal("0.00"),
            "salario_acumulado_mes": Decimal("0.00"),  # Monthly accumulated salary
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
        acumulado = self._obtener_acumulado_anual(empleado)
        if acumulado:
            variables["salario_acumulado"] += Decimal(str(acumulado.salario_bruto_acumulado or 0))
            variables["impuesto_acumulado"] += Decimal(str(acumulado.impuesto_retenido_acumulado or 0))
            variables["ir_retenido_acumulado"] += Decimal(str(acumulado.impuesto_retenido_acumulado or 0))
            variables["salario_acumulado_mes"] = Decimal(str(acumulado.salario_acumulado_mes or 0))

            # Additional accumulated values for progressive tax calculations (e.g., Nicaragua IR)
            variables["salario_bruto_acumulado"] = Decimal(str(acumulado.salario_bruto_acumulado or 0))
            variables["salario_gravable_acumulado"] = Decimal(str(acumulado.salario_gravable_acumulado or 0))
            variables["deducciones_antes_impuesto_acumulado"] = Decimal(
                str(acumulado.deducciones_antes_impuesto_acumulado or 0)
            )
            variables["periodos_procesados"] = Decimal(str(acumulado.periodos_procesados or 0))
            variables["meses_trabajados"] = Decimal(str(acumulado.periodos_procesados or 0))  # Alias for clarity

            # Calculate net accumulated salary (gross - pre-tax deductions like INSS)
            variables["salario_neto_acumulado"] = Decimal(str(acumulado.salario_bruto_acumulado or 0)) - Decimal(
                str(acumulado.deducciones_antes_impuesto_acumulado or 0)
            )

        # Include initial accumulated values from employee (for mid-year implementations)
        # These values represent pre-system salary/tax amounts when implementing mid-fiscal-year
        variables["salario_inicial_acumulado"] = Decimal(str(empleado.salario_acumulado or 0))
        variables["impuesto_inicial_acumulado"] = Decimal(str(empleado.impuesto_acumulado or 0))

        return variables

    def _obtener_acumulado_anual(self, empleado: Empleado) -> AcumuladoAnual | None:
        """Get or create accumulated annual values for employee.

        Args:
            empleado: The employee

        Returns:
            AcumuladoAnual record or None
        """
        if not self.planilla.tipo_planilla:
            return None

        tipo_planilla = self.planilla.tipo_planilla

        # Calculate fiscal period
        anio = self.fecha_calculo.year
        mes_inicio = tipo_planilla.mes_inicio_fiscal
        dia_inicio = tipo_planilla.dia_inicio_fiscal

        if self.fecha_calculo.month < mes_inicio:
            anio -= 1

        periodo_fiscal_inicio = date(anio, mes_inicio, dia_inicio)

        # Look up existing accumulated record
        # IMPORTANT: Filter by empresa_id to keep separate accumulations when employee
        # changes companies, as they are distinct legal entities
        acumulado = db.session.execute(
            db.select(AcumuladoAnual).filter(
                AcumuladoAnual.empleado_id == empleado.id,
                AcumuladoAnual.tipo_planilla_id == tipo_planilla.id,
                AcumuladoAnual.empresa_id == self.planilla.empresa_id,
                AcumuladoAnual.periodo_fiscal_inicio == periodo_fiscal_inicio,
            )
        ).scalar()

        return acumulado

    def _procesar_percepciones(self, emp_calculo: EmpleadoCalculo) -> None:
        """Process perceptions for an employee.

        Args:
            emp_calculo: Employee calculation container
        """
        self._trace(
            _("Procesando percepciones para %(nombre)s %(apellido)s")
            % {
                "nombre": emp_calculo.empleado.primer_nombre,
                "apellido": emp_calculo.empleado.primer_apellido,
            }
        )
        for planilla_percepcion in self.planilla.planilla_percepciones:
            if not planilla_percepcion.activo:
                continue

            percepcion = planilla_percepcion.percepcion
            if not percepcion or not percepcion.activo:
                continue

            # Check validity dates
            if percepcion.vigente_desde and percepcion.vigente_desde > self.fecha_calculo:
                continue
            if percepcion.valido_hasta and percepcion.valido_hasta < self.fecha_calculo:
                continue

            # Calculate perception amount
            monto = self._calcular_concepto(
                emp_calculo,
                percepcion.formula_tipo,
                percepcion.monto_default,
                percepcion.porcentaje,
                percepcion.formula,
                planilla_percepcion.monto_predeterminado,
                planilla_percepcion.porcentaje,
                codigo_concepto=percepcion.codigo,
                base_calculo=getattr(percepcion, "base_calculo", None),
                unidad_calculo=getattr(percepcion, "unidad_calculo", None),
            )

            if monto > 0:
                item = PercepcionItem(
                    codigo=percepcion.codigo,
                    nombre=percepcion.nombre,
                    monto=monto,
                    orden=planilla_percepcion.orden or 0,
                    gravable=percepcion.gravable,
                    percepcion_id=percepcion.id,
                )
                emp_calculo.percepciones.append(item)
                emp_calculo.total_percepciones += monto
                self._trace(
                    _("Calculando percepción %(codigo)s (%(nombre)s) monto=%(monto)s total =%(total)s")
                    % {
                        "codigo": item.codigo,
                        "nombre": item.nombre,
                        "monto": monto,
                        "total": emp_calculo.total_percepciones,
                    }
                )

    def _procesar_deducciones(self, emp_calculo: EmpleadoCalculo) -> None:
        """Process deductions for an employee.

        Args:
            emp_calculo: Employee calculation container
        """
        self._trace(
            _("Procesando deducciones para %(nombre)s %(apellido)s")
            % {
                "nombre": emp_calculo.empleado.primer_nombre,
                "apellido": emp_calculo.empleado.primer_apellido,
            }
        )
        deducciones_pendientes: list[DeduccionItem] = []

        for planilla_deduccion in self.planilla.planilla_deducciones:
            if not planilla_deduccion.activo:
                continue

            deduccion = planilla_deduccion.deduccion
            if not deduccion or not deduccion.activo:
                continue

            # Check validity dates
            if deduccion.vigente_desde and deduccion.vigente_desde > self.fecha_calculo:
                continue
            if deduccion.valido_hasta and deduccion.valido_hasta < self.fecha_calculo:
                continue

            # Calculate deduction amount
            monto = self._calcular_concepto(
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

        for deduccion in deducciones_pendientes:
            monto_aplicar = min(deduccion.monto, saldo_disponible)

            if monto_aplicar <= 0 and not deduccion.es_obligatoria:
                self.warnings.append(
                    f"Empleado {emp_calculo.empleado.primer_nombre} "
                    f"{emp_calculo.empleado.primer_apellido}: "
                    f"Deducción {deduccion.codigo} omitida por saldo insuficiente."
                )
                continue

            # Create new item with adjusted amount
            item = DeduccionItem(
                codigo=deduccion.codigo,
                nombre=deduccion.nombre,
                monto=monto_aplicar,
                prioridad=deduccion.prioridad,
                es_obligatoria=deduccion.es_obligatoria,
                deduccion_id=deduccion.deduccion_id,
            )
            emp_calculo.deducciones.append(item)
            emp_calculo.total_deducciones += monto_aplicar
            saldo_disponible -= monto_aplicar
            self._trace(
                _("Calculando deducción %(codigo)s (%(nombre)s) monto=%(monto)s total =%(total)s saldo =%(saldo)s")
                % {
                    "codigo": item.codigo,
                    "nombre": item.nombre,
                    "monto": monto_aplicar,
                    "total": emp_calculo.total_deducciones,
                    "saldo": saldo_disponible,
                }
            )

    def _aplicar_deducciones_automaticas(self, emp_calculo: EmpleadoCalculo) -> None:
        """Apply automatic loan and advance deductions.

        Args:
            emp_calculo: Employee calculation container
        """
        empleado = emp_calculo.empleado
        saldo_disponible = emp_calculo.salario_bruto - emp_calculo.total_deducciones

        # Get active loans/advances
        adelantos = (
            db.session.execute(
                db.select(Adelanto).filter(
                    Adelanto.empleado_id == empleado.id,
                    Adelanto.estado == AdelantoEstado.APROBADO,
                    Adelanto.saldo_pendiente > 0,
                )
            )
            .scalars()
            .all()
        )

        # Separate loans and advances
        prestamos = [a for a in adelantos if a.deduccion_id]
        adelantos_salariales = [a for a in adelantos if not a.deduccion_id]

        # Apply loans if enabled
        if self.planilla.aplicar_prestamos_automatico:
            for prestamo in prestamos:
                if saldo_disponible <= 0:
                    break

                # Calculate and apply interest if applicable
                self._calcular_interes_prestamo(prestamo)

                monto_cuota = Decimal(str(prestamo.monto_por_cuota or 0))
                if monto_cuota <= 0:
                    continue

                monto_aplicar = min(monto_cuota, saldo_disponible)

                item = DeduccionItem(
                    codigo=f"PRESTAMO_{prestamo.id[:8]}",
                    nombre=f"Cuota préstamo - {prestamo.motivo or 'N/A'}",
                    monto=monto_aplicar,
                    prioridad=self.planilla.prioridad_prestamos,
                    es_obligatoria=False,
                    tipo="prestamo",
                )
                emp_calculo.deducciones.append(item)
                emp_calculo.total_deducciones += monto_aplicar
                saldo_disponible -= monto_aplicar

                # Record the payment (will be committed with the nomina)
                self._registrar_abono_adelanto(prestamo, monto_aplicar)

        # Apply salary advances if enabled
        if self.planilla.aplicar_adelantos_automatico:
            for adelanto in adelantos_salariales:
                if saldo_disponible <= 0:
                    break

                monto_cuota = Decimal(str(adelanto.monto_por_cuota or adelanto.saldo_pendiente))
                monto_aplicar = min(monto_cuota, saldo_disponible)

                item = DeduccionItem(
                    codigo=f"ADELANTO_{adelanto.id[:8]}",
                    nombre=f"Adelanto salarial - {adelanto.motivo or 'N/A'}",
                    monto=monto_aplicar,
                    prioridad=self.planilla.prioridad_adelantos,
                    es_obligatoria=False,
                    tipo="adelanto",
                )
                emp_calculo.deducciones.append(item)
                emp_calculo.total_deducciones += monto_aplicar
                saldo_disponible -= monto_aplicar

                # Record the payment
                self._registrar_abono_adelanto(adelanto, monto_aplicar)

    def _calcular_interes_prestamo(self, prestamo: Adelanto) -> None:
        """Calculate and apply interest for a loan.

        This method calculates interest for the days elapsed since the last
        interest calculation and adds it to the loan balance.

        Args:
            prestamo: The loan to calculate interest for
        """
        from coati_payroll.interes_engine import calcular_interes_periodo
        from coati_payroll.model import InteresAdelanto

        # Only calculate interest if loan has interest rate
        tasa_interes = prestamo.tasa_interes or Decimal("0.0000")
        if tasa_interes <= 0:
            return

        # Only calculate if loan has balance
        if prestamo.saldo_pendiente <= 0:
            return

        # Determine period for interest calculation
        fecha_desde = prestamo.fecha_ultimo_calculo_interes
        if not fecha_desde:
            # First time calculating interest - use approval or disbursement date
            fecha_desde = prestamo.fecha_desembolso or prestamo.fecha_aprobacion

        if not fecha_desde:
            # If still no date, skip interest calculation
            return

        fecha_hasta = self.fecha_calculo

        # Skip if already calculated for this period
        if fecha_desde >= fecha_hasta:
            return

        # Calculate interest for the period
        tipo_interes = prestamo.tipo_interes or "simple"
        interes_calculado, dias = calcular_interes_periodo(
            saldo=prestamo.saldo_pendiente,
            tasa_anual=tasa_interes,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tipo_interes=tipo_interes,
        )

        if interes_calculado <= 0:
            return

        # Record interest in journal
        interes_entrada = InteresAdelanto(
            adelanto_id=prestamo.id,
            nomina_id=self.nomina.id if self.nomina else None,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            dias_transcurridos=dias,
            saldo_base=prestamo.saldo_pendiente,
            tasa_aplicada=tasa_interes,
            interes_calculado=interes_calculado,
            saldo_anterior=prestamo.saldo_pendiente,
            saldo_posterior=prestamo.saldo_pendiente + interes_calculado,
            observaciones=_("Interés calculado por nómina del {inicio} al {fin}").format(
                inicio=self.periodo_inicio, fin=self.periodo_fin
            ),
        )
        db.session.add(interes_entrada)

        # Update loan with interest
        prestamo.saldo_pendiente += interes_calculado
        prestamo.interes_acumulado = (prestamo.interes_acumulado or Decimal("0.00")) + interes_calculado
        prestamo.fecha_ultimo_calculo_interes = fecha_hasta

    def _registrar_abono_adelanto(self, adelanto: Adelanto, monto: Decimal) -> None:
        """Record a payment towards a loan/advance.

        Args:
            adelanto: The loan/advance record
            monto: Amount being paid
        """
        saldo_anterior = Decimal(str(adelanto.saldo_pendiente))
        saldo_posterior = saldo_anterior - monto

        abono = AdelantoAbono(
            adelanto_id=adelanto.id,
            nomina_id=self.nomina.id if self.nomina else None,
            fecha_abono=self.fecha_calculo,
            monto_abonado=monto,
            saldo_anterior=saldo_anterior,
            saldo_posterior=max(saldo_posterior, Decimal("0.00")),
            tipo_abono="nomina",
        )
        db.session.add(abono)

        # Update adelanto balance
        adelanto.saldo_pendiente = max(saldo_posterior, Decimal("0.00"))
        if adelanto.saldo_pendiente <= 0:
            adelanto.estado = AdelantoEstado.PAGADO

    def _procesar_prestaciones(self, emp_calculo: EmpleadoCalculo) -> None:
        """Process employer benefits for an employee.

        Note: Prestaciones do NOT affect employee's net pay.
        They are employer costs calculated separately.

        Args:
            emp_calculo: Employee calculation container
        """
        for planilla_prestacion in self.planilla.planilla_prestaciones:
            if not planilla_prestacion.activo:
                continue

            prestacion = planilla_prestacion.prestacion
            if not prestacion or not prestacion.activo:
                continue

            # Check validity dates
            if prestacion.vigente_desde and prestacion.vigente_desde > self.fecha_calculo:
                continue
            if prestacion.valido_hasta and prestacion.valido_hasta < self.fecha_calculo:
                continue

            # Calculate benefit amount
            monto = self._calcular_concepto(
                emp_calculo,
                prestacion.formula_tipo,
                prestacion.monto_default,
                prestacion.porcentaje,
                prestacion.formula,
                planilla_prestacion.monto_predeterminado,
                planilla_prestacion.porcentaje,
                codigo_concepto=prestacion.codigo,
                base_calculo=getattr(prestacion, "base_calculo", None),
                unidad_calculo=getattr(prestacion, "unidad_calculo", None),
            )

            # Apply ceiling if defined
            if prestacion.tope_aplicacion and monto > Decimal(str(prestacion.tope_aplicacion)):
                monto = Decimal(str(prestacion.tope_aplicacion))

            if monto > 0:
                item = PrestacionItem(
                    codigo=prestacion.codigo,
                    nombre=prestacion.nombre,
                    monto=monto,
                    orden=planilla_prestacion.orden or 0,
                    prestacion_id=prestacion.id,
                )
                emp_calculo.prestaciones.append(item)
                emp_calculo.total_prestaciones += monto

    def _calcular_concepto(
        self,
        emp_calculo: EmpleadoCalculo,
        formula_tipo: str,
        monto_default: Decimal | None,
        porcentaje: Decimal | None,
        formula: dict | None,
        monto_override: Decimal | None,
        porcentaje_override: Decimal | None,
        codigo_concepto: str | None = None,
        base_calculo: str | None = None,
        unidad_calculo: str | None = None,
    ) -> Decimal:
        """Calculate the amount for a perception, deduction, or benefit.

        Args:
            emp_calculo: Employee calculation container
            formula_tipo: Type of formula (fijo, porcentaje_salario, formula, etc.)
            monto_default: Default fixed amount
            porcentaje: Default percentage
            formula: JSON formula definition
            monto_override: Override amount from planilla association
            porcentaje_override: Override percentage from planilla association
            codigo_concepto: Code of the concept (for loading novedades)
            base_calculo: Base for calculation (salario_base, salario_bruto, etc.)
            unidad_calculo: Unit of calculation (horas, dias, etc.)

        Returns:
            Calculated amount (always >= 0)
        """
        # Use overrides if provided
        if monto_override:
            monto_calculado = Decimal(str(monto_override))
        elif porcentaje_override:
            monto_calculado = (emp_calculo.salario_base * Decimal(str(porcentaje_override)) / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            match formula_tipo:
                case FormulaType.FIJO:
                    monto_calculado = Decimal(str(monto_default or 0))

                case FormulaType.PORCENTAJE_SALARIO | FormulaType.PORCENTAJE:
                    if porcentaje:
                        monto_calculado = (
                            emp_calculo.salario_base * Decimal(str(porcentaje)) / Decimal("100")
                        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    else:
                        monto_calculado = Decimal("0.00")

                case FormulaType.PORCENTAJE_BRUTO:
                    if porcentaje:
                        monto_calculado = (
                            emp_calculo.salario_bruto * Decimal(str(porcentaje)) / Decimal("100")
                        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    else:
                        monto_calculado = Decimal("0.00")

                case FormulaType.HORAS:
                    # Calculate based on hours from novedades
                    # Formula: (base_salary / dias_base / horas_dia) * percentage * hours
                    if not codigo_concepto or codigo_concepto not in emp_calculo.novedades:
                        monto_calculado = Decimal("0.00")
                    else:
                        horas = emp_calculo.novedades[codigo_concepto]
                        if horas <= 0:
                            monto_calculado = Decimal("0.00")
                        else:
                            # Determine base for calculation
                            if base_calculo == "salario_bruto":
                                base = emp_calculo.salario_bruto
                            else:
                                # Use monthly salary for hourly rate calculation
                                # salario_mensual is the full monthly salary before period proration
                                base = emp_calculo.salario_mensual

                            # Calculate hourly rate
                            # Always use 30 days/month, 8 hours/day (HORAS_TRABAJO_DIA constant)
                            dias_base = Decimal("30")
                            tasa_hora = (base / dias_base / HORAS_TRABAJO_DIA).quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )

                            # Apply percentage (e.g., 100% for normal overtime, 200% for special)
                            if porcentaje:
                                tasa_hora = (tasa_hora * Decimal(str(porcentaje)) / Decimal("100")).quantize(
                                    Decimal("0.01"), rounding=ROUND_HALF_UP
                                )

                            # Calculate total for hours
                            monto_calculado = (tasa_hora * horas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                case FormulaType.DIAS:
                    # Calculate based on days from novedades
                    # Formula: (base_salary / dias_base) * percentage * days
                    if not codigo_concepto or codigo_concepto not in emp_calculo.novedades:
                        monto_calculado = Decimal("0.00")
                    else:
                        dias = emp_calculo.novedades[codigo_concepto]
                        if dias <= 0:
                            monto_calculado = Decimal("0.00")
                        else:
                            # Determine base for calculation
                            if base_calculo == "salario_bruto":
                                base = emp_calculo.salario_bruto
                            else:
                                # Use monthly salary for daily rate calculation
                                # salario_mensual is the full monthly salary before period proration
                                base = emp_calculo.salario_mensual

                            # Calculate daily rate - always use 30-day month
                            dias_base = Decimal("30")
                            tasa_dia = (base / dias_base).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                            # Apply percentage
                            if porcentaje:
                                tasa_dia = (tasa_dia * Decimal(str(porcentaje)) / Decimal("100")).quantize(
                                    Decimal("0.01"), rounding=ROUND_HALF_UP
                                )

                            # Calculate total for days
                            monto_calculado = (tasa_dia * dias).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                case FormulaType.FORMULA:
                    if formula and isinstance(formula, dict):
                        try:
                            # Merge variables with formula inputs
                            inputs = {**emp_calculo.variables_calculo}
                            inputs["salario_bruto"] = emp_calculo.salario_bruto
                            inputs["total_percepciones"] = emp_calculo.total_percepciones
                            inputs["total_deducciones"] = emp_calculo.total_deducciones

                            # Calculate before-tax deductions already processed in this period
                            deducciones_antes_impuesto_periodo = Decimal("0.00")
                            for ded in emp_calculo.deducciones:
                                if ded.deduccion_id:
                                    ded_obj = db.session.get(Deduccion, ded.deduccion_id)
                                    if ded_obj and ded_obj.antes_impuesto:
                                        deducciones_antes_impuesto_periodo += ded.monto
                            inputs["deducciones_antes_impuesto_periodo"] = deducciones_antes_impuesto_periodo
                            inputs["inss_periodo"] = deducciones_antes_impuesto_periodo

                            engine = FormulaEngine(formula)
                            result = engine.execute(inputs)
                            monto_calculado = Decimal(str(result.get("output", 0))).quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )
                        except FormulaEngineError as e:
                            self.warnings.append(f"Error en fórmula: {str(e)}")
                            monto_calculado = Decimal("0.00")
                    else:
                        monto_calculado = Decimal("0.00")

                case FormulaType.REGLA_CALCULO:
                    # Find the ReglaCalculo linked to this deduction
                    regla = db.session.execute(
                        db.select(ReglaCalculo)
                        .filter_by(deduccion_id=codigo_concepto)
                        .filter(ReglaCalculo.activo.is_(True))
                    ).scalar_one_or_none()
                    if not regla:
                        # Try finding by deduccion_id matching deduccion's id
                        deduccion_obj = db.session.execute(
                            db.select(Deduccion).filter_by(codigo=codigo_concepto)
                        ).scalar_one_or_none()
                        if deduccion_obj:
                            regla = db.session.execute(
                                db.select(ReglaCalculo)
                                .filter_by(deduccion_id=deduccion_obj.id)
                                .filter(ReglaCalculo.activo.is_(True))
                            ).scalar_one_or_none()

                    if regla and regla.esquema_json:
                        try:
                            # Prepare inputs for formula engine
                            inputs = {**emp_calculo.variables_calculo}
                            inputs["salario_bruto"] = emp_calculo.salario_bruto
                            inputs["total_percepciones"] = emp_calculo.total_percepciones
                            inputs["total_deducciones"] = emp_calculo.total_deducciones

                            # Calculate before-tax deductions already processed
                            deducciones_antes_impuesto_periodo = Decimal("0.00")
                            for ded in emp_calculo.deducciones:
                                if ded.deduccion_id:
                                    ded_obj = db.session.get(Deduccion, ded.deduccion_id)
                                    if ded_obj and ded_obj.antes_impuesto:
                                        deducciones_antes_impuesto_periodo += ded.monto
                            inputs["deducciones_antes_impuesto_periodo"] = deducciones_antes_impuesto_periodo
                            inputs["inss_periodo"] = deducciones_antes_impuesto_periodo

                            engine = FormulaEngine(regla.esquema_json)
                            result = engine.execute(inputs)
                            monto_calculado = Decimal(str(result.get("output", 0))).quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )
                        except FormulaEngineError as e:
                            self.warnings.append(f"Error en ReglaCalculo {regla.codigo}: {str(e)}")
                            monto_calculado = Decimal("0.00")
                    else:
                        self.warnings.append(f"ReglaCalculo no encontrada para deducción {codigo_concepto}")
                        monto_calculado = Decimal("0.00")

                case _:
                    monto_calculado = Decimal(str(monto_default or 0))

        # CRITICAL: Ensure calculated amounts are never negative
        # Negative values in deductions/perceptions would cause incorrect calculations
        # (e.g., negative deduction would add to salary instead of subtracting)
        if monto_calculado < 0:
            self.warnings.append(
                f"Concepto '{codigo_concepto or 'desconocido'}': Configuración incorrecta resultó en "
                f"monto negativo ({monto_calculado}). Ajustando a 0.00. "
                f"Verifique la configuración del concepto (porcentaje o monto)."
            )
            return Decimal("0.00")

        return monto_calculado

    def _crear_nomina_empleado(self, emp_calculo: EmpleadoCalculo) -> NominaEmpleado:
        """Create the NominaEmpleado record with all details.

        Args:
            emp_calculo: Employee calculation container

        Returns:
            Created NominaEmpleado record
        """
        empleado = emp_calculo.empleado

        nomina_empleado = NominaEmpleado(
            nomina_id=self.nomina.id,
            empleado_id=empleado.id,
            salario_bruto=emp_calculo.salario_bruto,
            total_ingresos=emp_calculo.total_percepciones,
            total_deducciones=emp_calculo.total_deducciones,
            salario_neto=emp_calculo.salario_neto,
            moneda_origen_id=emp_calculo.moneda_origen_id,
            tipo_cambio_aplicado=emp_calculo.tipo_cambio,
            cargo_snapshot=empleado.cargo,
            area_snapshot=empleado.area,
            centro_costos_snapshot=empleado.centro_costos,
            sueldo_base_historico=emp_calculo.salario_base,
        )
        db.session.add(nomina_empleado)
        db.session.flush()

        # Create detail records for perceptions
        orden = 0
        for percepcion in emp_calculo.percepciones:
            orden += 1
            detalle = NominaDetalle(
                nomina_empleado_id=nomina_empleado.id,
                tipo="ingreso",
                codigo=percepcion.codigo,
                descripcion=percepcion.nombre,
                monto=percepcion.monto,
                orden=orden,
                percepcion_id=percepcion.percepcion_id,
            )
            db.session.add(detalle)

        # Create detail records for deductions
        for deduccion in emp_calculo.deducciones:
            orden += 1
            detalle = NominaDetalle(
                nomina_empleado_id=nomina_empleado.id,
                tipo="deduccion",
                codigo=deduccion.codigo,
                descripcion=deduccion.nombre,
                monto=deduccion.monto,
                orden=orden,
                deduccion_id=deduccion.deduccion_id,
            )
            db.session.add(detalle)

        # Create detail records for benefits (employer costs)
        for prestacion in emp_calculo.prestaciones:
            orden += 1
            detalle = NominaDetalle(
                nomina_empleado_id=nomina_empleado.id,
                tipo="prestacion",
                codigo=prestacion.codigo,
                descripcion=prestacion.nombre,
                monto=prestacion.monto,
                orden=orden,
                prestacion_id=prestacion.prestacion_id,
            )
            db.session.add(detalle)

        return nomina_empleado

    def _actualizar_acumulados(
        self,
        emp_calculo: EmpleadoCalculo,
        _nomina_empleado: NominaEmpleado,
    ) -> None:
        """Update accumulated annual values for the employee.

        Args:
            emp_calculo: Employee calculation container
            _nomina_empleado: The created NominaEmpleado record (reserved for future use)
        """
        if not self.planilla.tipo_planilla:
            return

        tipo_planilla = self.planilla.tipo_planilla
        empleado = emp_calculo.empleado

        # Calculate fiscal period
        anio = self.fecha_calculo.year
        mes_inicio = tipo_planilla.mes_inicio_fiscal
        dia_inicio = tipo_planilla.dia_inicio_fiscal

        if self.fecha_calculo.month < mes_inicio:
            anio -= 1

        periodo_fiscal_inicio = date(anio, mes_inicio, dia_inicio)
        periodo_fiscal_fin = date(anio + 1, mes_inicio, dia_inicio)

        # Determine empresa_id: prefer planilla's empresa, fallback to employee's empresa
        # This is critical because AcumuladoAnual requires empresa_id (NOT NULL constraint)
        # and tracks separate accumulations when employees change companies
        empresa_id = self.planilla.empresa_id or empleado.empresa_id
        if not empresa_id:
            raise ValidationError(
                _("No se puede crear acumulado anual: ni la planilla ni el empleado tienen empresa_id asignado")
            )

        # Get or create accumulated record
        # IMPORTANT: Must filter by empresa_id to match the unique constraint and
        # ensure separate accumulations for different companies
        acumulado = db.session.execute(
            db.select(AcumuladoAnual).filter(
                AcumuladoAnual.empleado_id == empleado.id,
                AcumuladoAnual.tipo_planilla_id == tipo_planilla.id,
                AcumuladoAnual.empresa_id == empresa_id,
                AcumuladoAnual.periodo_fiscal_inicio == periodo_fiscal_inicio,
            )
        ).scalar()

        if not acumulado:
            # Initialize with pre-system accumulated values for mid-year implementations
            # These values come from the employee record and represent work done before
            # the system was deployed (e.g., Jan-June when system starts in July)
            salario_inicial = empleado.salario_acumulado or Decimal("0.00")
            impuesto_inicial = empleado.impuesto_acumulado or Decimal("0.00")

            acumulado = AcumuladoAnual(
                empleado_id=empleado.id,
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa_id,
                periodo_fiscal_inicio=periodo_fiscal_inicio,
                periodo_fiscal_fin=periodo_fiscal_fin,
                salario_bruto_acumulado=salario_inicial,
                salario_gravable_acumulado=Decimal("0.00"),  # Will be calculated
                deducciones_antes_impuesto_acumulado=impuesto_inicial,
                impuesto_retenido_acumulado=Decimal("0.00"),  # IR will be calculated
                periodos_procesados=0,  # Only counts periods processed in system
                salario_acumulado_mes=Decimal("0.00"),
                mes_actual=self.periodo_fin.month,
            )
            db.session.add(acumulado)

        # Reset monthly accumulation if entering a new month
        acumulado.reset_mes_acumulado_if_needed(self.periodo_fin)

        # Update accumulated values
        acumulado.salario_bruto_acumulado += emp_calculo.salario_bruto
        acumulado.salario_acumulado_mes += emp_calculo.salario_bruto
        acumulado.periodos_procesados += 1
        acumulado.ultimo_periodo_procesado = self.periodo_fin

        # Calculate gravable income (perceptions that are gravable)
        salario_gravable = emp_calculo.salario_base
        for percepcion in emp_calculo.percepciones:
            if percepcion.gravable:
                salario_gravable += percepcion.monto
        acumulado.salario_gravable_acumulado += salario_gravable

        # Sum up before-tax deductions and taxes
        for deduccion in emp_calculo.deducciones:
            # Check if this is a tax deduction
            deduccion_obj = db.session.get(Deduccion, deduccion.deduccion_id) if deduccion.deduccion_id else None
            if deduccion_obj:
                if deduccion_obj.es_impuesto:
                    acumulado.impuesto_retenido_acumulado += deduccion.monto
                elif deduccion_obj.antes_impuesto:
                    acumulado.deducciones_antes_impuesto_acumulado += deduccion.monto

    def _crear_transacciones_prestaciones(
        self,
        emp_calculo: EmpleadoCalculo,
        nomina_empleado: NominaEmpleado,
    ) -> None:
        """Create transactional records for accumulated benefits.

        This method creates immutable transaction records for each benefit
        calculated in the payroll. Each transaction includes the previous balance,
        the amount added, and the new balance for complete audit trail.

        Args:
            emp_calculo: Employee calculation container
            nomina_empleado: The created NominaEmpleado record
        """
        if not self.nomina:
            return

        empleado = emp_calculo.empleado
        periodo_anio = self.periodo_fin.year
        periodo_mes = self.periodo_fin.month

        # Get the payroll's currency
        moneda_id = self.planilla.moneda_id

        for prestacion_item in emp_calculo.prestaciones:
            if not prestacion_item.prestacion_id:
                continue

            # Get the prestacion object to check accumulation type
            prestacion = db.session.get(Prestacion, prestacion_item.prestacion_id)
            if not prestacion:
                continue

            # Get the previous balance for this employee and prestacion
            # Order by fecha_transaccion and creado (timestamp) to get the most recent transaction
            ultima_transaccion = (
                db.session.execute(
                    db.select(PrestacionAcumulada)
                    .filter(
                        PrestacionAcumulada.empleado_id == empleado.id,
                        PrestacionAcumulada.prestacion_id == prestacion.id,
                    )
                    .order_by(
                        PrestacionAcumulada.fecha_transaccion.desc(),
                        PrestacionAcumulada.creado.desc(),
                    )
                    .limit(1)
                )
                .unique()
                .scalars()
                .first()
            )

            saldo_anterior = ultima_transaccion.saldo_nuevo if ultima_transaccion else Decimal("0.00")

            # For monthly settlement benefits, the balance resets each month
            # So the previous balance should be 0 if we're in a new month
            if prestacion.tipo_acumulacion == "mensual":
                # Check if the last transaction was in a different month
                if ultima_transaccion and (
                    ultima_transaccion.anio != periodo_anio or ultima_transaccion.mes != periodo_mes
                ):
                    saldo_anterior = Decimal("0.00")

            # Calculate new balance
            monto_transaccion = prestacion_item.monto
            saldo_nuevo = saldo_anterior + monto_transaccion

            # Create the transaction record
            transaccion = PrestacionAcumulada(
                empleado_id=empleado.id,
                prestacion_id=prestacion.id,
                fecha_transaccion=self.fecha_calculo,
                tipo_transaccion="adicion",  # Provision from payroll
                anio=periodo_anio,
                mes=periodo_mes,
                moneda_id=moneda_id,
                monto_transaccion=monto_transaccion,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=saldo_nuevo,
                nomina_id=self.nomina.id,
                observaciones=(
                    f"Provisión nómina {self.periodo_inicio.strftime('%Y-%m-%d')} - "
                    f"{self.periodo_fin.strftime('%Y-%m-%d')}"
                ),
                procesado_por=self.nomina.generado_por,
                creado_por=self.nomina.generado_por,
            )

            db.session.add(transaccion)

    def _procesar_vacaciones(
        self, empleado: Empleado, emp_calculo: EmpleadoCalculo, nomina_empleado: NominaEmpleado
    ) -> None:
        """Process vacation accrual and usage for an employee.

        This method:
        1. Accumulates vacation time based on the vacation policy
        2. Processes any vacation novelties (time off taken)

        Args:
            empleado: The employee
            emp_calculo: Employee calculation data
            nomina_empleado: The payroll record for this employee
        """
        try:
            from coati_payroll.vacation_service import VacationService

            vacation_service = VacationService(
                planilla=self.planilla,
                periodo_inicio=self.periodo_inicio,
                periodo_fin=self.periodo_fin,
            )

            # Accumulate vacation time
            accrued = vacation_service.acumular_vacaciones_empleado(
                empleado=empleado,
                nomina_empleado=nomina_empleado,
                usuario=self.usuario,
            )

            if accrued > 0:
                self._trace(f"Acumuladas {accrued} unidades de vacaciones para empleado " f"{empleado.codigo_empleado}")

            # Process vacation novelties (time off taken)
            used = vacation_service.procesar_novedades_vacaciones(
                empleado=empleado,
                novedades=emp_calculo.novedades,
                usuario=self.usuario,
            )

            if used > 0:
                self._trace(
                    f"Procesadas {used} unidades de vacaciones usadas para empleado " f"{empleado.codigo_empleado}"
                )

        except Exception as e:
            # Log error but don't fail payroll execution
            log.error(f"Error procesando vacaciones para empleado {empleado.codigo_empleado}: {str(e)}")
            self.warnings.append(
                f"No se pudieron procesar vacaciones para {empleado.primer_nombre} "
                f"{empleado.primer_apellido}: {str(e)}"
            )

    def _calcular_totales(self) -> None:
        """Calculate grand totals for the nomina."""
        if not self.nomina:
            return

        total_bruto = Decimal("0.00")
        total_deducciones = Decimal("0.00")
        total_neto = Decimal("0.00")

        for emp_calculo in self.empleados_calculo:
            total_bruto += emp_calculo.salario_bruto
            total_deducciones += emp_calculo.total_deducciones
            total_neto += emp_calculo.salario_neto

        self.nomina.total_bruto = total_bruto
        self.nomina.total_deducciones = total_deducciones
        self.nomina.total_neto = total_neto


def ejecutar_nomina(
    planilla_id: str,
    periodo_inicio: date,
    periodo_fin: date,
    fecha_calculo: date | None = None,
    usuario: str | None = None,
) -> tuple[Nomina | None, list[str], list[str]]:
    """Execute a payroll run for a planilla.

    Convenience function for executing a payroll run.

    Args:
        planilla_id: ID of the Planilla to execute
        periodo_inicio: Start date of the payroll period
        periodo_fin: End date of the payroll period
        fecha_calculo: Date of calculation (defaults to today)
        usuario: Username executing the payroll

    Returns:
        Tuple of (Nomina or None, list of errors, list of warnings)
    """
    # Eagerly load all relationships needed for payroll processing
    # This prevents DetachedInstanceError in test contexts
    from sqlalchemy.orm import joinedload
    from coati_payroll.model import PlanillaIngreso, PlanillaDeduccion, PlanillaPrestacion, PlanillaEmpleado

    planilla = (
        db.session.execute(
            db.select(Planilla)
            .options(
                joinedload(Planilla.planilla_percepciones).joinedload(PlanillaIngreso.percepcion),
                joinedload(Planilla.planilla_deducciones).joinedload(PlanillaDeduccion.deduccion),
                joinedload(Planilla.planilla_prestaciones).joinedload(PlanillaPrestacion.prestacion),
                joinedload(Planilla.planilla_empleados).joinedload(PlanillaEmpleado.empleado),
                joinedload(Planilla.planilla_reglas_calculo),
                joinedload(Planilla.tipo_planilla),
                joinedload(Planilla.moneda),
            )
            .filter(Planilla.id == planilla_id)
        )
        .unique()
        .scalar_one_or_none()
    )

    if not planilla:
        return None, ["Planilla no encontrada."], []

    engine = NominaEngine(
        planilla=planilla,
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        fecha_calculo=fecha_calculo,
        usuario=usuario,
    )

    nomina = engine.ejecutar()

    return nomina, engine.errors, engine.warnings
