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
"""Business logic validators for planilla operations."""

from coati_payroll.model import Planilla, Empleado
from coati_payroll.i18n import _


class PlanillaValidator:
    """Validators for planilla business logic."""

    @staticmethod
    def validar_empresa_empleado(planilla: Planilla, empleado: Empleado) -> tuple[bool, str | None]:
        """Validate that planilla and employee belong to the same company.

        Args:
            planilla: The planilla to validate
            empleado: The employee to validate

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is None.
        """
        if not planilla.empresa_id:
            return False, _("La planilla debe tener una empresa asignada antes de agregar empleados.")
        if not empleado.empresa_id:
            return False, _("El empleado debe tener una empresa asignada antes de ser agregado a una planilla.")
        if planilla.empresa_id != empleado.empresa_id:
            return False, _("El empleado y la planilla deben pertenecer a la misma empresa.")
        return True, None
