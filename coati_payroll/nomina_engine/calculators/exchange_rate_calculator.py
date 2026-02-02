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
"""Exchange rate calculator for payroll processing."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from coati_payroll.model import Empleado, Planilla
from ..repositories.exchange_rate_repository import ExchangeRateRepository


class ExchangeRateCalculator:
    """Calculator for exchange rates."""

    def __init__(self, exchange_rate_repository: ExchangeRateRepository):
        self.exchange_rate_repo = exchange_rate_repository

    def get_exchange_rate(self, empleado: Empleado, planilla: Planilla, fecha_calculo: date) -> Decimal:
        """Get exchange rate for employee's currency to planilla currency."""
        if not empleado.moneda_id:
            return Decimal("1.00")

        if empleado.moneda_id == planilla.moneda_id:
            return Decimal("1.00")

        rate = self.exchange_rate_repo.get_rate(empleado.moneda_id, planilla.moneda_id, fecha_calculo)
        if rate is None:
            from ..validators import CalculationError

            raise CalculationError(
                f"No se encontró tipo de cambio para empleado "
                f"{empleado.primer_nombre} {empleado.primer_apellido}. "
                f"Se requiere un tipo de cambio de {empleado.moneda.codigo if empleado.moneda else 'desconocido'} "
                f"a {planilla.moneda.codigo if planilla.moneda else 'desconocido'} "
                f"para la fecha {fecha_calculo.strftime('%d/%m/%Y')}."
            )

        return Decimal(str(rate))
