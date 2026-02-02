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
"""Payroll execution context - immutable domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..results.validation_result import ValidationResult


@dataclass(frozen=True)
class PayrollContext:
    """Immutable context for payroll execution."""

    planilla_id: str
    periodo_inicio: date
    periodo_fin: date
    fecha_calculo: date
    usuario: Optional[str] = None
    validation_result: "ValidationResult | None" = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default validation_result if None."""
        if self.validation_result is None:
            from ..results.validation_result import ValidationResult

            object.__setattr__(self, "validation_result", ValidationResult())
