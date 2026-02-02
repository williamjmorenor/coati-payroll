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
"""Repository for Exchange Rate operations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from coati_payroll.model import TipoCambio
from .base_repository import BaseRepository


class ExchangeRateRepository(BaseRepository[TipoCambio]):
    """Repository for TipoCambio operations."""

    def get_by_id(self, tipo_cambio_id: str) -> Optional[TipoCambio]:
        """Get exchange rate by ID."""
        return self.session.get(TipoCambio, tipo_cambio_id)

    def get_rate(self, moneda_origen_id: str, moneda_destino_id: str, fecha: date) -> Optional[Decimal]:
        """Get exchange rate for currency pair on or before given date."""
        from sqlalchemy import select

        tipo_cambio = (
            self.session.execute(
                select(TipoCambio)
                .filter(
                    TipoCambio.moneda_origen_id == moneda_origen_id,
                    TipoCambio.moneda_destino_id == moneda_destino_id,
                    TipoCambio.fecha <= fecha,
                )
                .order_by(TipoCambio.fecha.desc())
            )
            .unique()
            .scalar_one_or_none()
        )

        if tipo_cambio:
            return Decimal(str(tipo_cambio.tasa))
        return None

    def save(self, tipo_cambio: TipoCambio) -> TipoCambio:
        """Save exchange rate."""
        self.session.add(tipo_cambio)
        return tipo_cambio
