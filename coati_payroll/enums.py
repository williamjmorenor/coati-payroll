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

    GENERADO = "generado"  # Generated but not approved
    APROBADO = "aprobado"  # Approved and ready to apply
    APLICADO = "aplicado"  # Applied/executed


class AdelantoEstado(StrEnum):
    """States of a loan or salary advance.

    Using Python 3.11+ StrEnum for better type checking.
    """

    PENDIENTE = "pendiente"  # Pending approval
    APROBADO = "aprobado"  # Approved and active
    PAGADO = "pagado"  # Fully paid off
    RECHAZADO = "rechazado"  # Rejected
    CANCELADO = "cancelado"  # Cancelled


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
