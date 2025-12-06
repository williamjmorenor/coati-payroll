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
"""Currency CRUD routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from coati_payroll.forms import CurrencyForm
from coati_payroll.i18n import _
from coati_payroll.rbac import require_read_access, require_write_access
from coati_payroll.model import Moneda, db
from coati_payroll.vistas.constants import PER_PAGE

currency_bp = Blueprint("currency", __name__, url_prefix="/currency")


@currency_bp.route("/")
@require_read_access()
def index():
    """List all currencies with pagination."""
    page = request.args.get("page", 1, type=int)
    pagination = db.paginate(
        db.select(Moneda).order_by(Moneda.codigo),
        page=page,
        per_page=PER_PAGE,
        error_out=False,
    )
    return render_template(
        "modules/currency/index.html",
        currencies=pagination.items,
        pagination=pagination,
    )


@currency_bp.route("/new", methods=["GET", "POST"])
@require_write_access()
def new():
    """Create a new currency."""
    form = CurrencyForm()

    if form.validate_on_submit():
        currency = Moneda()
        currency.codigo = form.codigo.data
        currency.nombre = form.nombre.data
        currency.simbolo = form.simbolo.data
        currency.activo = form.activo.data
        currency.creado_por = current_user.usuario

        db.session.add(currency)
        db.session.commit()
        flash(_("Moneda creada exitosamente."), "success")
        return redirect(url_for("currency.index"))

    return render_template("modules/currency/form.html", form=form, title=_("Nueva Moneda"))


@currency_bp.route("/edit/<string:id>", methods=["GET", "POST"])
@require_write_access()
def edit(id: str):
    """Edit an existing currency."""
    currency = db.session.get(Moneda, id)
    if not currency:
        flash(_("Moneda no encontrada."), "error")
        return redirect(url_for("currency.index"))

    form = CurrencyForm(obj=currency)

    if form.validate_on_submit():
        currency.codigo = form.codigo.data
        currency.nombre = form.nombre.data
        currency.simbolo = form.simbolo.data
        currency.activo = form.activo.data
        currency.modificado_por = current_user.usuario

        db.session.commit()
        flash(_("Moneda actualizada exitosamente."), "success")
        return redirect(url_for("currency.index"))

    return render_template(
        "modules/currency/form.html",
        form=form,
        title=_("Editar Moneda"),
        currency=currency,
    )


@currency_bp.route("/delete/<string:id>", methods=["POST"])
@require_write_access()
def delete(id: str):
    """Delete a currency."""
    currency = db.session.get(Moneda, id)
    if not currency:
        flash(_("Moneda no encontrada."), "error")
        return redirect(url_for("currency.index"))

    db.session.delete(currency)
    db.session.commit()
    flash(_("Moneda eliminada exitosamente."), "success")
    return redirect(url_for("currency.index"))
