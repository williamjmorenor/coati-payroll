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
"""Employee calculation domain models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from coati_payroll.model import Empleado, Planilla
from .calculation_items import DeduccionItem, PercepcionItem, PrestacionItem


class EmpleadoCalculo:
    """Container for employee calculation data during payroll processing.

    This is a mutable container used during payroll processing.
    For backward compatibility, this class maintains the same interface
    as the original implementation.
    """

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


# Alias for backward compatibility
EmployeeCalculation = EmpleadoCalculo
