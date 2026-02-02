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
"""Views for managing Planilla (master payroll) and its associations.

A Planilla is the central hub that connects:
- Employees (via PlanillaEmpleado)
- Perceptions (via PlanillaIngreso)
- Deductions (via PlanillaDeduccion) - with priority ordering
- Benefits/Prestaciones (via PlanillaPrestacion)
- Calculation Rules (via PlanillaReglaCalculo)
"""

from flask import Blueprint

# Create the blueprint
planilla_bp = Blueprint("planilla", __name__, url_prefix="/planilla")

# Import all route modules to register them with the blueprint
# This must be done after creating the blueprint
from coati_payroll.vistas.planilla import routes  # noqa: E402, F401
from coati_payroll.vistas.planilla import config_routes  # noqa: E402, F401
from coati_payroll.vistas.planilla import association_routes  # noqa: E402, F401
from coati_payroll.vistas.planilla import nomina_routes  # noqa: E402, F401
from coati_payroll.vistas.planilla import novedad_routes  # noqa: E402, F401
from coati_payroll.vistas.planilla import export_routes  # noqa: E402, F401

__all__ = ["planilla_bp"]
