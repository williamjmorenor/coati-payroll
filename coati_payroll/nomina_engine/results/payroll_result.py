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
"""Payroll execution result DTO."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from coati_payroll.model import Nomina

if TYPE_CHECKING:
    from ..domain.employee_calculation import EmpleadoCalculo
    from ..domain.payroll_context import PayrollContext


@dataclass
class PayrollResult:
    """Result of a payroll execution."""

    context: "PayrollContext"
    nomina: Optional[Nomina] = None
    employee_calculations: list["EmpleadoCalculo"] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_errors(self, errors: list[str]) -> None:
        """Add multiple error messages."""
        self.errors.extend(errors)

    def set_success(self, nomina: Nomina, calculations: list["EmpleadoCalculo"]) -> None:
        """Set the result as successful."""
        self.nomina = nomina
        self.employee_calculations = calculations
