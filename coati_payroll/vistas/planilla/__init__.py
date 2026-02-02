# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
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
