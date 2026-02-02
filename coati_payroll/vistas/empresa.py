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
"""Empresa (Company) views module."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from coati_payroll.enums import TipoUsuario
from coati_payroll.i18n import _
from coati_payroll.model import Empresa, db
from coati_payroll.rbac import require_role, require_read_access

empresa_bp = Blueprint("empresa", __name__, url_prefix="/empresa")


@empresa_bp.route("/")
@require_read_access()
def index():
    """List all companies."""
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = db.select(Empresa).order_by(Empresa.razon_social)
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    empresas = pagination.items

    return render_template(
        "modules/empresa/index.html",
        empresas=empresas,
        pagination=pagination,
    )


@empresa_bp.route("/new", methods=["GET", "POST"])
@require_role(TipoUsuario.ADMIN)
def new():
    """Create a new company. Only administrators can create companies."""
    from coati_payroll.forms import EmpresaForm

    form = EmpresaForm()

    if form.validate_on_submit():
        empresa = Empresa()
        form.populate_obj(empresa)
        empresa.creado_por = current_user.usuario

        db.session.add(empresa)
        try:
            db.session.commit()
            flash(_("Empresa creada exitosamente."), "success")
            return redirect(url_for("empresa.index"))
        except Exception as e:
            db.session.rollback()
            flash(_("Error al crear la empresa: {}").format(str(e)), "danger")

    return render_template("modules/empresa/form.html", form=form, titulo=_("Nueva Empresa"))


@empresa_bp.route("/<string:empresa_id>/edit", methods=["GET", "POST"])
@require_role(TipoUsuario.ADMIN)
def edit(empresa_id):
    """Edit an existing company. Only administrators can edit companies."""
    from coati_payroll.forms import EmpresaForm

    empresa = db.session.get(Empresa, empresa_id)
    if not empresa:
        flash(_("Empresa no encontrada."), "warning")
        return redirect(url_for("empresa.index"))

    form = EmpresaForm(obj=empresa)

    if form.validate_on_submit():
        form.populate_obj(empresa)
        empresa.modificado_por = current_user.usuario

        try:
            db.session.commit()
            flash(_("Empresa actualizada exitosamente."), "success")
            return redirect(url_for("empresa.index"))
        except Exception as e:
            db.session.rollback()
            flash(_("Error al actualizar la empresa: {}").format(str(e)), "danger")

    return render_template(
        "modules/empresa/form.html",
        form=form,
        empresa=empresa,
        titulo=_("Editar Empresa"),
    )


@empresa_bp.route("/<string:empresa_id>/delete", methods=["POST"])
@require_role(TipoUsuario.ADMIN)
def delete(empresa_id):
    """Delete a company. Only administrators can delete companies."""
    empresa = db.session.get(Empresa, empresa_id)
    if not empresa:
        flash(_("Empresa no encontrada."), "warning")
        return redirect(url_for("empresa.index"))

    # Check if company has employees or payrolls
    if empresa.empleados or empresa.planillas:
        flash(
            _("No se puede eliminar la empresa porque tiene empleados o planillas asociadas."),
            "danger",
        )
        return redirect(url_for("empresa.index"))

    try:
        db.session.delete(empresa)
        db.session.commit()
        flash(_("Empresa eliminada exitosamente."), "success")
    except Exception as e:
        db.session.rollback()
        flash(_("Error al eliminar la empresa: {}").format(str(e)), "danger")

    return redirect(url_for("empresa.index"))


@empresa_bp.route("/<string:empresa_id>/toggle", methods=["POST"])
@require_role(TipoUsuario.ADMIN)
def toggle_active(empresa_id):
    """Toggle company active status. Only administrators can toggle status."""
    empresa = db.session.get(Empresa, empresa_id)
    if not empresa:
        flash(_("Empresa no encontrada."), "warning")
        return redirect(url_for("empresa.index"))

    empresa.activo = not empresa.activo
    empresa.modificado_por = current_user.usuario

    try:
        db.session.commit()
        estado = _("activada") if empresa.activo else _("desactivada")
        flash(_("Empresa {} exitosamente.").format(estado), "success")
    except Exception as e:
        db.session.rollback()
        flash(_("Error al cambiar el estado de la empresa: {}").format(str(e)), "danger")

    return redirect(url_for("empresa.index"))
