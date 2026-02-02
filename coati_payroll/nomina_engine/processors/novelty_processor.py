# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Novelty processor for loading employee novelties."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from coati_payroll.model import Empleado
from ..repositories.novelty_repository import NoveltyRepository


class NoveltyProcessor:
    """Processor for loading employee novelties."""

    def __init__(self, novelty_repository: NoveltyRepository):
        self.novelty_repo = novelty_repository

    def load_novelties(self, empleado: Empleado, periodo_inicio: date, periodo_fin: date) -> dict[str, Decimal]:
        """Load novelties for the employee in this period."""
        novedades: dict[str, Decimal] = {}

        nomina_novedades = self.novelty_repo.get_by_employee_and_period(empleado.id, periodo_inicio, periodo_fin)

        for novedad in nomina_novedades:
            codigo = novedad.codigo_concepto
            valor = Decimal(str(novedad.valor_cantidad or 0))
            novedades[codigo] = novedades.get(codigo, Decimal("0")) + valor

        return novedades
