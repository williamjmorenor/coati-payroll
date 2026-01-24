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
"""Calculation items - immutable domain models for payroll items."""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple


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
