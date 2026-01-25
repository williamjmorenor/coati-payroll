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

"""Liquidaciones module views."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required, current_user

from coati_payroll.i18n import _
from coati_payroll.model import Liquidacion, LiquidacionConcepto, Empleado, db
from coati_payroll.model import PlanillaEmpleado
from coati_payroll.rbac import require_read_access, require_write_access
from coati_payroll.liquidacion_engine import ejecutar_liquidacion, recalcular_liquidacion
from coati_payroll.vistas.planilla.helpers import check_openpyxl_available
from coati_payroll.vistas.planilla.services import ExportService

liquidacion_bp = Blueprint("liquidacion", __name__, url_prefix="/liquidaciones")

# Constants
ROUTE_LIQUIDACION_VER = "liquidacion.ver"


@liquidacion_bp.route("/")
@login_required
@require_read_access()
def index():
    """List liquidaciones."""
    liquidaciones = db.session.execute(db.select(Liquidacion).order_by(Liquidacion.creado.desc())).scalars().all()
    return render_template("modules/liquidacion/index.html", liquidaciones=liquidaciones)


@liquidacion_bp.route("/nueva", methods=["GET", "POST"])
@login_required
@require_write_access()
def nueva():
    """Create and calculate a new liquidacion."""
    empleados = (
        db.session.execute(db.select(Empleado).filter_by(activo=True).order_by(Empleado.primer_apellido))
        .scalars()
        .all()
    )
    conceptos = (
        db.session.execute(db.select(LiquidacionConcepto).filter_by(activo=True).order_by(LiquidacionConcepto.nombre))
        .scalars()
        .all()
    )

    if request.method == "POST":
        empleado_id = request.form.get("empleado_id")
        concepto_id = request.form.get("concepto_id") or None
        fecha_calculo_str = request.form.get("fecha_calculo")

        try:
            fecha_calculo = date.fromisoformat(fecha_calculo_str) if fecha_calculo_str else date.today()
        except ValueError:
            flash(_("Formato de fecha inválido."), "error")
            return redirect(url_for("liquidacion.nueva"))

        liquidacion, errors, warnings = ejecutar_liquidacion(
            empleado_id=empleado_id,
            concepto_id=concepto_id,
            fecha_calculo=fecha_calculo,
            usuario=getattr(current_user, "usuario", None),
        )

        for e in errors:
            flash(e, "error")
        for w in warnings:
            flash(w, "warning")

        if liquidacion:
            flash(_("Liquidación calculada."), "success")
            return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion.id))

        return redirect(url_for("liquidacion.nueva"))

    return render_template(
        "modules/liquidacion/nueva.html", empleados=empleados, conceptos=conceptos, fecha_calculo=date.today()
    )


@liquidacion_bp.route("/<liquidacion_id>")
@login_required
@require_read_access()
def ver(liquidacion_id: str):
    """View liquidacion detail."""
    liquidacion = db.get_or_404(Liquidacion, liquidacion_id)
    return render_template("modules/liquidacion/ver.html", liquidacion=liquidacion)


@liquidacion_bp.route("/<liquidacion_id>/recalcular", methods=["POST"])
@login_required
@require_write_access()
def recalcular(liquidacion_id: str):
    liquidacion = db.get_or_404(Liquidacion, liquidacion_id)
    nueva, errors, warnings = recalcular_liquidacion(
        liquidacion_id=liquidacion.id,
        fecha_calculo=liquidacion.fecha_calculo,
        usuario=getattr(current_user, "usuario", None),
    )

    for e in errors:
        flash(e, "error")
    for w in warnings:
        flash(w, "warning")

    if nueva:
        flash(_("Liquidación recalculada."), "success")
    return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion.id))


@liquidacion_bp.route("/<liquidacion_id>/aplicar", methods=["POST"])
@login_required
@require_write_access()
def aplicar(liquidacion_id: str):
    liquidacion = db.get_or_404(Liquidacion, liquidacion_id)

    if liquidacion.estado != "borrador":
        flash(_("Solo se pueden aplicar liquidaciones en borrador."), "error")
        return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion.id))

    empleado = db.session.get(Empleado, liquidacion.empleado_id)
    if not empleado:
        flash(_("Empleado no encontrado."), "error")
        return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion.id))

    # Mark employee inactive
    empleado.activo = False
    empleado.fecha_baja = liquidacion.fecha_calculo

    # Deactivate all active planilla associations
    asociaciones = (
        db.session.execute(
            db.select(PlanillaEmpleado).where(
                PlanillaEmpleado.empleado_id == empleado.id,
                PlanillaEmpleado.activo.is_(True),
            )
        )
        .scalars()
        .all()
    )

    for pe in asociaciones:
        pe.activo = False
        pe.fecha_fin = liquidacion.fecha_calculo

    liquidacion.estado = "aplicada"
    db.session.commit()
    flash(_("Liquidación aplicada. Empleado marcado como inactivo y desvinculado de planillas."), "success")
    return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion.id))


@liquidacion_bp.route("/<liquidacion_id>/pagar", methods=["POST"])
@login_required
@require_write_access()
def pagar(liquidacion_id: str):
    liquidacion = db.get_or_404(Liquidacion, liquidacion_id)

    if liquidacion.estado != "aplicada":
        flash(_("Solo se pueden pagar liquidaciones aplicadas."), "error")
        return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion.id))

    liquidacion.estado = "pagada"
    db.session.commit()
    flash(_("Liquidación marcada como pagada."), "success")
    return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion.id))


@liquidacion_bp.route("/<liquidacion_id>/exportar-excel")
@login_required
@require_read_access()
def exportar_excel(liquidacion_id: str):
    if not check_openpyxl_available():
        flash(_("Excel export no disponible. Instale openpyxl."), "warning")
        return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion_id))

    liquidacion = db.get_or_404(Liquidacion, liquidacion_id)

    try:
        output, filename = ExportService.exportar_liquidacion_excel(liquidacion)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        flash(_("Error al exportar liquidación: {}").format(str(e)), "error")
        return redirect(url_for(ROUTE_LIQUIDACION_VER, liquidacion_id=liquidacion_id))
