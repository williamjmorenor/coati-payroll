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
"""Custom employee field CRUD routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from coati_payroll.forms import CustomFieldForm
from coati_payroll.i18n import _
from coati_payroll.model import CampoPersonalizado, db
from coati_payroll.vistas.constants import PER_PAGE

custom_field_bp = Blueprint("custom_field", __name__, url_prefix="/custom_field")


@custom_field_bp.route("/")
@login_required
def index():
    """List all custom fields with pagination."""
    page = request.args.get("page", 1, type=int)
    pagination = db.paginate(
        db.select(CampoPersonalizado).order_by(CampoPersonalizado.orden),
        page=page,
        per_page=PER_PAGE,
        error_out=False,
    )
    return render_template(
        "modules/custom_field/index.html",
        custom_fields=pagination.items,
        pagination=pagination,
    )


@custom_field_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create a new custom field."""
    form = CustomFieldForm()

    if form.validate_on_submit():
        custom_field = CampoPersonalizado()
        custom_field.nombre_campo = form.nombre_campo.data
        custom_field.etiqueta = form.etiqueta.data
        custom_field.tipo_dato = form.tipo_dato.data
        custom_field.descripcion = form.descripcion.data
        custom_field.orden = int(form.orden.data or 0)
        custom_field.activo = form.activo.data
        custom_field.creado_por = current_user.usuario

        db.session.add(custom_field)
        db.session.commit()
        flash(_("Campo personalizado creado exitosamente."), "success")
        return redirect(url_for("custom_field.index"))

    return render_template(
        "modules/custom_field/form.html",
        form=form,
        title=_("Nuevo Campo Personalizado"),
    )


@custom_field_bp.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def edit(id: str):
    """Edit an existing custom field."""
    custom_field = db.session.get(CampoPersonalizado, id)
    if not custom_field:
        flash(_("Campo personalizado no encontrado."), "error")
        return redirect(url_for("custom_field.index"))

    form = CustomFieldForm(obj=custom_field)

    if form.validate_on_submit():
        custom_field.nombre_campo = form.nombre_campo.data
        custom_field.etiqueta = form.etiqueta.data
        custom_field.tipo_dato = form.tipo_dato.data
        custom_field.descripcion = form.descripcion.data
        custom_field.orden = int(form.orden.data or 0)
        custom_field.activo = form.activo.data
        custom_field.modificado_por = current_user.usuario

        db.session.commit()
        flash(_("Campo personalizado actualizado exitosamente."), "success")
        return redirect(url_for("custom_field.index"))

    return render_template(
        "modules/custom_field/form.html",
        form=form,
        title=_("Editar Campo Personalizado"),
        custom_field=custom_field,
    )


@custom_field_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
def delete(id: str):
    """Delete a custom field."""
    custom_field = db.session.get(CampoPersonalizado, id)
    if not custom_field:
        flash(_("Campo personalizado no encontrado."), "error")
        return redirect(url_for("custom_field.index"))

    db.session.delete(custom_field)
    db.session.commit()
    flash(_("Campo personalizado eliminado exitosamente."), "success")
    return redirect(url_for("custom_field.index"))
