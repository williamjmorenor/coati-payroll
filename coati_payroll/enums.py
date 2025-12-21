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
"""Enumerations for type safety using Python 3.11+ StrEnum.

This module defines string-based enums using Python 3.11's StrEnum class,
which provides better type safety and autocompletion compared to plain strings.

StrEnum was introduced in Python 3.11 and automatically generates string values
from member names when values aren't explicitly provided.
"""

from __future__ import annotations

from enum import StrEnum


class FormulaType(StrEnum):
    """Types of formulas for calculating payroll concepts.

    Python 3.11+ StrEnum provides automatic string conversion and better IDE support.
    """

    FIJO = "fijo"  # Fixed amount
    PORCENTAJE = "porcentaje"  # Percentage
    PORCENTAJE_SALARIO = "porcentaje_salario"  # Percentage of salary
    PORCENTAJE_BRUTO = "porcentaje_bruto"  # Percentage of gross
    FORMULA = "formula"  # Complex formula using FormulaEngine
    REGLA_CALCULO = "regla_calculo"  # Uses linked ReglaCalculo for calculation
    HORAS = "horas"  # Based on hours
    DIAS = "dias"  # Based on days


class StepType(StrEnum):
    """Types of calculation steps in FormulaEngine schemas.

    Using StrEnum (Python 3.11+) provides better pattern matching in match/case
    statements and autocompletion in IDEs.
    """

    CALCULATION = "calculation"  # Mathematical calculation
    CONDITIONAL = "conditional"  # If/else logic
    TAX_LOOKUP = "tax_lookup"  # Tax table lookup
    ASSIGNMENT = "assignment"  # Variable assignment


class NominaEstado(StrEnum):
    """States of a payroll run (Nomina).

    StrEnum ensures type safety when checking or setting nomina status.
    """

    CALCULANDO = "calculando"  # Calculating in background
    GENERADO = "generado"  # Generated but not approved
    APROBADO = "aprobado"  # Approved and ready to apply
    APLICADO = "aplicado"  # Applied/executed
    PAGADO = "pagado"  # Paid out (synonym for APLICADO, for compatibility)
    ANULADO = "anulado"  # Cancelled/voided
    ERROR = "error"  # Error during calculation


class AdelantoEstado(StrEnum):
    """States of a loan or salary advance.

    Using Python 3.11+ StrEnum for better type checking.
    """

    BORRADOR = "borrador"  # Draft - not yet submitted
    PENDIENTE = "pendiente"  # Pending approval
    APROBADO = "aprobado"  # Approved and active
    APLICADO = "aplicado"  # Applied/disbursed (paid out to employee)
    PAGADO = "pagado"  # Fully paid off (all installments completed)
    RECHAZADO = "rechazado"  # Rejected
    CANCELADO = "cancelado"  # Cancelled


class AdelantoTipo(StrEnum):
    """Types of advances/loans.

    Using Python 3.11+ StrEnum for type safety.
    """

    ADELANTO = "adelanto"  # Salary advance
    PRESTAMO = "prestamo"  # Loan with optional interest


class TipoInteres(StrEnum):
    """Interest rate types for loans.

    Using Python 3.11+ StrEnum for type safety.
    """

    NINGUNO = "ninguno"  # No interest
    SIMPLE = "simple"  # Simple interest
    COMPUESTO = "compuesto"  # Compound interest


class MetodoAmortizacion(StrEnum):
    """Amortization methods for loans with interest.

    Using Python 3.11+ StrEnum for type safety.
    """

    FRANCES = "frances"  # French method - constant payment (cuota constante)
    ALEMAN = "aleman"  # German method - constant amortization (amortización constante)


class VacacionEstado(StrEnum):
    """States of vacation requests.

    Python 3.11+ StrEnum for type-safe vacation status handling.
    """

    PENDIENTE = "pendiente"  # Pending approval
    APROBADO = "aprobado"  # Approved
    RECHAZADO = "rechazado"  # Rejected
    DISFRUTADO = "disfrutado"  # Taken/enjoyed


class TipoUsuario(StrEnum):
    """User types in the system.

    StrEnum (Python 3.11+) provides better type safety for user roles.
    """

    ADMIN = "admin"  # Administrator
    HHRR = "hhrr"  # Human Resources
    AUDIT = "audit"  # Auditor


class TipoDetalle(StrEnum):
    """Types of payroll detail entries.

    Using Python 3.11+ StrEnum for better type safety in detail records.
    """

    INGRESO = "ingreso"  # Income/perception
    DEDUCCION = "deduccion"  # Deduction
    PRESTACION = "prestacion"  # Employer benefit


class Periodicidad(StrEnum):
    """Payroll periodicities.

    Python 3.11+ StrEnum for type-safe period definitions.
    """

    MENSUAL = "mensual"  # Monthly
    QUINCENAL = "quincenal"  # Biweekly
    SEMANAL = "semanal"  # Weekly
    DIARIO = "diario"  # Daily


class NovedadEstado(StrEnum):
    """States of a payroll novelty (novedad).

    Python 3.11+ StrEnum for type-safe novedad status handling.
    """

    PENDIENTE = "pendiente"  # Pending - not yet executed
    EJECUTADA = "ejecutada"  # Executed - nomina has been applied


class TipoAcumulacionPrestacion(StrEnum):
    """Types of benefit accumulation periods.

    Defines how employee benefits (prestaciones) accumulate over time.
    Python 3.11+ StrEnum for type safety.
    """

    MENSUAL = "mensual"  # Settled monthly (e.g., INSS, INATEC)
    ANUAL = "anual"  # Accumulated annually (e.g., 13th month)
    VIDA_LABORAL = "vida_laboral"  # Accumulated over employment lifetime (e.g., severance)


class CargaInicialEstado(StrEnum):
    """States for initial benefit balance loading.

    Python 3.11+ StrEnum for type-safe initial balance status handling.
    """

    BORRADOR = "borrador"  # Draft - not yet applied
    APLICADO = "aplicado"  # Applied - transferred to accumulated table


class TipoTransaccionPrestacion(StrEnum):
    """Transaction types for accumulated benefits.

    Defines the types of transactions that can modify benefit balances.
    Python 3.11+ StrEnum for type safety.
    """

    SALDO_INICIAL = "saldo_inicial"  # Initial balance
    ADICION = "adicion"  # Addition (increase)
    DISMINUCION = "disminucion"  # Decrease (reduction)
    AJUSTE = "ajuste"  # Adjustment (can be positive or negative)


# ============================================================================
# Vacation Module Enums
# ============================================================================


class AccrualMethod(StrEnum):
    """Methods for vacation accrual calculation.

    Defines how vacation time is calculated and earned.
    Python 3.11+ StrEnum for type safety.
    """

    PERIODIC = "periodic"  # Fixed amount per period (monthly, annually, etc.)
    PROPORTIONAL = "proportional"  # Based on worked days/hours
    SENIORITY = "seniority"  # Tiered by years of service


class AccrualFrequency(StrEnum):
    """Frequency of vacation accrual.

    Determines how often vacation time is credited to employee accounts.
    Python 3.11+ StrEnum for type safety.
    """

    MONTHLY = "monthly"  # Monthly accrual
    BIWEEKLY = "biweekly"  # Every two weeks
    ANNUAL = "annual"  # Once per year


class AccrualBasis(StrEnum):
    """Basis for proportional accrual calculation.

    Used when accrual_method is PROPORTIONAL.
    Python 3.11+ StrEnum for type safety.
    """

    DAYS_WORKED = "days_worked"  # Based on days actually worked
    HOURS_WORKED = "hours_worked"  # Based on hours worked


class VacationLedgerType(StrEnum):
    """Types of vacation ledger entries.

    All vacation balance changes must be recorded with one of these types.
    Python 3.11+ StrEnum for type safety.
    """

    ACCRUAL = "accrual"  # Earned vacation time
    USAGE = "usage"  # Vacation time taken
    ADJUSTMENT = "adjustment"  # Manual adjustment (+ or -)
    EXPIRATION = "expiration"  # Expired vacation time
    PAYOUT = "payout"  # Paid out vacation (e.g., on termination)


class VacationUnitType(StrEnum):
    """Unit types for vacation balances.

    Country-specific: some use days, some use hours.
    Python 3.11+ StrEnum for type safety.
    """

    DAYS = "days"  # Calendar or working days
    HOURS = "hours"  # Hours


class ExpirationRule(StrEnum):
    """Rules for vacation expiration.

    Defines when unused vacation expires.
    Python 3.11+ StrEnum for type safety.
    """

    NEVER = "never"  # Vacation never expires
    FISCAL_YEAR_END = "fiscal_year_end"  # Expires at fiscal year end
    ANNIVERSARY = "anniversary"  # Expires on employment anniversary
    CUSTOM_DATE = "custom_date"  # Custom expiration date


# ============================================================================
# Reports Module Enums
# ============================================================================


class ReportType(StrEnum):
    """Types of reports in the system.

    System reports are pre-defined, optimized reports built into the core.
    Custom reports are user-defined reports created through the UI.
    Python 3.11+ StrEnum for type safety.
    """

    SYSTEM = "system"  # System-defined report
    CUSTOM = "custom"  # User-defined custom report


class ReportStatus(StrEnum):
    """Administrative status of a report.

    Controls whether a report is available for execution.
    Python 3.11+ StrEnum for type safety.
    """

    ENABLED = "enabled"  # Report is available for execution
    DISABLED = "disabled"  # Report is not available


class ReportExecutionStatus(StrEnum):
    """Status of a report execution.

    Tracks the lifecycle of a report execution from queued to completed.
    Python 3.11+ StrEnum for type safety.
    """

    QUEUED = "queued"  # Report execution is queued
    RUNNING = "running"  # Report is currently executing
    COMPLETED = "completed"  # Report execution completed successfully
    FAILED = "failed"  # Report execution failed
    CANCELLED = "cancelled"  # Report execution was cancelled
