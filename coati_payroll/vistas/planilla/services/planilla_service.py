# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Service for planilla business logic."""

from coati_payroll.model import Planilla


class PlanillaService:
    """Service for planilla operations."""

    @staticmethod
    def can_delete(planilla: Planilla) -> tuple[bool, str | None]:
        """Check if a planilla can be deleted.

        Args:
            planilla: The planilla to check

        Returns:
            Tuple of (can_delete, error_message). If can_delete is True, error_message is None.
        """
        if planilla.nominas:
            return False, "No se puede eliminar una planilla con nóminas generadas."
        return True, None
