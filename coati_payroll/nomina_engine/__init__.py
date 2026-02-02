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
"""Payroll execution engine - Domain-driven architecture.

This module provides a modular payroll execution engine organized by domain.
Main modules:
- domain: Domain models (immutable data structures)
- validators: Business validations
- calculators: Calculation logic
- processors: Specialized processors (loans, vacations, etc.)
- repositories: Data access layer
- services: Business services
- results: Result DTOs

This package maintains backward compatibility with the original nomina_engine.py
implementation while providing a new modular structure for future development.
"""

from __future__ import annotations

from .engine import (
    NominaEngine,
    ejecutar_nomina,
    EmpleadoCalculo,
)

# Export calculation items for backward compatibility
from .domain.calculation_items import (
    DeduccionItem,
    PercepcionItem,
    PrestacionItem,
)

# Export domain models
from .domain import (
    PayrollContext,
    EmployeeCalculation,
)

# Export results
from .results import (
    ValidationResult,
    ErrorResult,
    PayrollResult,
)

# Export exceptions
from .validators import (
    NominaEngineError,
    ValidationError,
    CalculationError,
)

__all__ = [
    # Main engine
    "NominaEngine",
    "ejecutar_nomina",
    # Legacy compatibility
    "EmpleadoCalculo",
    "DeduccionItem",
    "PercepcionItem",
    "PrestacionItem",
    # Domain models
    "PayrollContext",
    "EmployeeCalculation",
    # Results
    "ValidationResult",
    "ErrorResult",
    "PayrollResult",
    # Exceptions
    "NominaEngineError",
    "ValidationError",
    "CalculationError",
]

__version__ = "2.0.0"
