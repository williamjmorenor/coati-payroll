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
from sqlalchemy.exc import SQLAlchemyError

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.model import db, Empleado, Empresa, Planilla, Nomina

app = Blueprint("app", __name__)


@app.route("/")
@login_required
def index():
    # Get statistics for dashboard
    total_empleados = (
        db.session.execute(db.select(func.count(Empleado.id)).filter(Empleado.activo.is_(True))).scalar() or 0
    )
    total_empresas = (
        db.session.execute(db.select(func.count(Empresa.id)).filter(Empresa.activo.is_(True))).scalar() or 0
    )
    total_planillas = (
        db.session.execute(db.select(func.count(Planilla.id)).filter(Planilla.activo.is_(True))).scalar() or 0
    )
    total_nominas = db.session.execute(db.select(func.count(Nomina.id))).scalar() or 0

    # Get recent payrolls (last 5)
    recent_nominas = (
        db.session.execute(db.select(Nomina).order_by(Nomina.fecha_generacion.desc()).limit(5)).scalars().all()
    )

    return render_template(
        "index.html",
        total_empleados=total_empleados,
        total_empresas=total_empresas,
        total_planillas=total_planillas,
        total_nominas=total_nominas,
        recent_nominas=recent_nominas,
    )


@app.route("/health")
def health():
    """Health check endpoint for container orchestration.

    Returns a simple OK response to indicate the application is running.
    This endpoint does not require authentication and does not check database connectivity.
    """
    return {"status": "ok"}, 200


@app.route("/ready")
def ready():
    """Readiness check endpoint for container orchestration.

    Returns OK if the application is ready to serve traffic (database is accessible).
    This endpoint does not require authentication.
    """
    try:
        # Test database connectivity using a fresh connection
        # This avoids issues with session state from other parts of the application
        with db.engine.connect() as connection:
            connection.execute(db.text("SELECT 1")).scalar()
        return {"status": "ok"}, 200
    except SQLAlchemyError:
        return {"status": "unavailable"}, 503
    except Exception:
        # Catch any other exception that might occur
        return {"status": "unavailable"}, 503
