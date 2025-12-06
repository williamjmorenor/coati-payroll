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
"""App module."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.model import db, Empleado, Empresa, Planilla, Nomina, Usuario

app = Blueprint("app", __name__)


@app.route("/")
@login_required
def index():
    # Get statistics for dashboard
    total_empleados = db.session.query(func.count(Empleado.id)).filter(Empleado.activo == True).scalar() or 0
    total_empresas = db.session.query(func.count(Empresa.id)).filter(Empresa.activo == True).scalar() or 0
    total_planillas = db.session.query(func.count(Planilla.id)).filter(Planilla.activo == True).scalar() or 0
    total_nominas = db.session.query(func.count(Nomina.id)).scalar() or 0

    # Get recent payrolls (last 5)
    recent_nominas = db.session.query(Nomina).order_by(Nomina.fecha_generacion.desc()).limit(5).all()

    return render_template(
        "index.html",
        total_empleados=total_empleados,
        total_empresas=total_empresas,
        total_planillas=total_planillas,
        total_nominas=total_nominas,
        recent_nominas=recent_nominas,
    )
