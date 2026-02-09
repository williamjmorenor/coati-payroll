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

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from importlib import import_module

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask import Blueprint

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #

# Create the blueprint
planilla_bp = Blueprint("planilla", __name__, url_prefix="/planilla")

# Import all route modules to register them with the blueprint
# This must be done after creating the blueprint
for module_name in (
    "coati_payroll.vistas.planilla.routes",
    "coati_payroll.vistas.planilla.config_routes",
    "coati_payroll.vistas.planilla.association_routes",
    "coati_payroll.vistas.planilla.nomina_routes",
    "coati_payroll.vistas.planilla.novedad_routes",
    "coati_payroll.vistas.planilla.export_routes",
):
    import_module(module_name)

__all__ = ["planilla_bp"]
