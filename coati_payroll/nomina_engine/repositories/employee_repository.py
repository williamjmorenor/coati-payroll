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
"""Repository for Employee operations."""

from __future__ import annotations

from typing import Optional

from coati_payroll.model import Empleado
from .base_repository import BaseRepository


class EmployeeRepository(BaseRepository[Empleado]):
    """Repository for Employee operations."""

    def get_by_id(self, empleado_id: str) -> Optional[Empleado]:
        """Get employee by ID."""
        return self.session.get(Empleado, empleado_id)

    def save(self, empleado: Empleado) -> Empleado:
        """Save employee."""
        self.session.add(empleado)
        return empleado
