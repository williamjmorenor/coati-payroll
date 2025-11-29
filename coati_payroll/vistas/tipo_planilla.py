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
"""Payroll Type (TipoPlanilla) CRUD routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from coati_payroll.forms import TipoPlanillaForm
from coati_payroll.i18n import _
from coati_payroll.model import TipoPlanilla, db
from coati_payroll.vistas.constants import PER_PAGE

tipo_planilla_bp = Blueprint("tipo_planilla", __name__, url_prefix="/tipo-planilla")


@tipo_planilla_bp.route("/")
@login_required
def index():
    """List all payroll types with pagination."""
    page = request.args.get("page", 1, type=int)
    pagination = db.paginate(
        db.select(TipoPlanilla).order_by(TipoPlanilla.codigo),
        page=page,
        per_page=PER_PAGE,
        error_out=False,
    )
    return render_template(
        "modules/tipo_planilla/index.html",
        tipos_planilla=pagination.items,
        pagination=pagination,
    )


@tipo_planilla_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create a new payroll type."""
    form = TipoPlanillaForm()

    if form.validate_on_submit():
        tipo_planilla = TipoPlanilla()
        tipo_planilla.codigo = form.codigo.data
        tipo_planilla.descripcion = form.descripcion.data
        tipo_planilla.periodicidad = form.periodicidad.data
        tipo_planilla.dias = form.dias.data
        tipo_planilla.mes_inicio_fiscal = form.mes_inicio_fiscal.data
        tipo_planilla.dia_inicio_fiscal = form.dia_inicio_fiscal.data
        tipo_planilla.acumula_anual = form.acumula_anual.data
        tipo_planilla.periodos_por_anio = form.periodos_por_anio.data
        tipo_planilla.activo = form.activo.data
        tipo_planilla.creado_por = current_user.usuario

        db.session.add(tipo_planilla)
        db.session.commit()
        flash(_("Tipo de planilla creado exitosamente."), "success")
        return redirect(url_for("tipo_planilla.index"))

    return render_template(
        "modules/tipo_planilla/form.html",
        form=form,
        title=_("Nuevo Tipo de Planilla"),
    )


@tipo_planilla_bp.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def edit(id: str):
    """Edit an existing payroll type."""
    tipo_planilla = db.session.get(TipoPlanilla, id)
    if not tipo_planilla:
        flash(_("Tipo de planilla no encontrado."), "error")
        return redirect(url_for("tipo_planilla.index"))

    form = TipoPlanillaForm(obj=tipo_planilla)

    if form.validate_on_submit():
        tipo_planilla.codigo = form.codigo.data
        tipo_planilla.descripcion = form.descripcion.data
        tipo_planilla.periodicidad = form.periodicidad.data
        tipo_planilla.dias = form.dias.data
        tipo_planilla.mes_inicio_fiscal = form.mes_inicio_fiscal.data
        tipo_planilla.dia_inicio_fiscal = form.dia_inicio_fiscal.data
        tipo_planilla.acumula_anual = form.acumula_anual.data
        tipo_planilla.periodos_por_anio = form.periodos_por_anio.data
        tipo_planilla.activo = form.activo.data
        tipo_planilla.modificado_por = current_user.usuario

        db.session.commit()
        flash(_("Tipo de planilla actualizado exitosamente."), "success")
        return redirect(url_for("tipo_planilla.index"))

    return render_template(
        "modules/tipo_planilla/form.html",
        form=form,
        title=_("Editar Tipo de Planilla"),
        tipo_planilla=tipo_planilla,
    )


@tipo_planilla_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
def delete(id: str):
    """Delete a payroll type."""
    tipo_planilla = db.session.get(TipoPlanilla, id)
    if not tipo_planilla:
        flash(_("Tipo de planilla no encontrado."), "error")
        return redirect(url_for("tipo_planilla.index"))

    # Check if this type is used by any planilla
    if tipo_planilla.planillas:
        flash(
            _("No se puede eliminar un tipo de planilla que está siendo usado."),
            "error",
        )
        return redirect(url_for("tipo_planilla.index"))

    db.session.delete(tipo_planilla)
    db.session.commit()
    flash(_("Tipo de planilla eliminado exitosamente."), "success")
    return redirect(url_for("tipo_planilla.index"))
