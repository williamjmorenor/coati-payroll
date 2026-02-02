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
"""Repository for Novelty operations."""

from __future__ import annotations

from datetime import date
from typing import Optional

from coati_payroll.model import NominaNovedad
from .base_repository import BaseRepository


class NoveltyRepository(BaseRepository[NominaNovedad]):
    """Repository for NominaNovedad operations."""

    def get_by_id(self, novelty_id: str) -> Optional[NominaNovedad]:
        """Get novelty by ID."""
        return self.session.get(NominaNovedad, novelty_id)

    def get_by_employee_and_period(
        self, empleado_id: str, periodo_inicio: date, periodo_fin: date
    ) -> list[NominaNovedad]:
        """Get novelties for employee within period."""
        from sqlalchemy import select

        return list(
            self.session.execute(
                select(NominaNovedad).filter(
                    NominaNovedad.empleado_id == empleado_id,
                    NominaNovedad.fecha_novedad >= periodo_inicio,
                    NominaNovedad.fecha_novedad <= periodo_fin,
                )
            )
            .unique()
            .scalars()
            .all()
        )

    def save(self, novelty: NominaNovedad) -> NominaNovedad:
        """Save novelty."""
        self.session.add(novelty)
        return novelty
