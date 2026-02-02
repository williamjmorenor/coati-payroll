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
