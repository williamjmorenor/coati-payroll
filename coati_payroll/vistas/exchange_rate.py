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
"""Exchange Rate CRUD routes."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from coati_payroll.forms import ExchangeRateForm
from coati_payroll.i18n import _
from coati_payroll.model import Moneda, TipoCambio, db
from coati_payroll.vistas.constants import PER_PAGE

exchange_rate_bp = Blueprint("exchange_rate", __name__, url_prefix="/exchange_rate")


def get_currency_choices():
    """Get list of currencies for select fields."""
    currencies = (
        db.session.execute(
            db.select(Moneda).filter_by(activo=True).order_by(Moneda.codigo)
        )
        .scalars()
        .all()
    )
    return [(c.id, f"{c.codigo} - {c.nombre}") for c in currencies]


@exchange_rate_bp.route("/")
@login_required
def index():
    """List all exchange rates with pagination and filters."""
    page = request.args.get("page", 1, type=int)

    # Get filter parameters
    fecha_desde = request.args.get("fecha_desde", type=str)
    fecha_hasta = request.args.get("fecha_hasta", type=str)
    moneda_origen_id = (
        request.args.get("moneda_origen_id", type=str)
        if request.args.get("moneda_origen_id")
        else None
    )
    moneda_destino_id = (
        request.args.get("moneda_destino_id", type=str)
        if request.args.get("moneda_destino_id")
        else None
    )

    # Build query with filters
    query = db.select(TipoCambio)

    if fecha_desde:
        query = query.filter(TipoCambio.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(TipoCambio.fecha <= fecha_hasta)
    if moneda_origen_id:
        query = query.filter(TipoCambio.moneda_origen_id == moneda_origen_id)
    if moneda_destino_id:
        query = query.filter(TipoCambio.moneda_destino_id == moneda_destino_id)

    query = query.order_by(TipoCambio.fecha.desc())

    pagination = db.paginate(
        query,
        page=page,
        per_page=PER_PAGE,
        error_out=False,
    )

    # Get currencies for filter dropdowns
    currencies = get_currency_choices()

    return render_template(
        "modules/exchange_rate/index.html",
        exchange_rates=pagination.items,
        pagination=pagination,
        currencies=currencies,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
    )


@exchange_rate_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create a new exchange rate."""
    form = ExchangeRateForm()
    form.moneda_origen_id.choices = [("", _("Seleccionar..."))] + get_currency_choices()
    form.moneda_destino_id.choices = [
        ("", _("Seleccionar..."))
    ] + get_currency_choices()

    if form.validate_on_submit():
        exchange_rate = TipoCambio()
        exchange_rate.fecha = form.fecha.data
        exchange_rate.moneda_origen_id = form.moneda_origen_id.data
        exchange_rate.moneda_destino_id = form.moneda_destino_id.data
        exchange_rate.tasa = form.tasa.data
        exchange_rate.creado_por = current_user.usuario

        db.session.add(exchange_rate)
        db.session.commit()
        flash(_("Tipo de cambio creado exitosamente."), "success")
        return redirect(url_for("exchange_rate.index"))

    # Default date to today
    if not form.fecha.data:
        form.fecha.data = date.today()

    return render_template(
        "modules/exchange_rate/form.html", form=form, title=_("Nuevo Tipo de Cambio")
    )


@exchange_rate_bp.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def edit(id: str):
    """Edit an existing exchange rate."""
    exchange_rate = db.session.get(TipoCambio, id)
    if not exchange_rate:
        flash(_("Tipo de cambio no encontrado."), "error")
        return redirect(url_for("exchange_rate.index"))

    form = ExchangeRateForm(obj=exchange_rate)
    form.moneda_origen_id.choices = [("", _("Seleccionar..."))] + get_currency_choices()
    form.moneda_destino_id.choices = [
        ("", _("Seleccionar..."))
    ] + get_currency_choices()

    if form.validate_on_submit():
        exchange_rate.fecha = form.fecha.data
        exchange_rate.moneda_origen_id = form.moneda_origen_id.data
        exchange_rate.moneda_destino_id = form.moneda_destino_id.data
        exchange_rate.tasa = form.tasa.data
        exchange_rate.modificado_por = current_user.usuario

        db.session.commit()
        flash(_("Tipo de cambio actualizado exitosamente."), "success")
        return redirect(url_for("exchange_rate.index"))

    return render_template(
        "modules/exchange_rate/form.html",
        form=form,
        title=_("Editar Tipo de Cambio"),
        exchange_rate=exchange_rate,
    )


@exchange_rate_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
def delete(id: str):
    """Delete an exchange rate."""
    exchange_rate = db.session.get(TipoCambio, id)
    if not exchange_rate:
        flash(_("Tipo de cambio no encontrado."), "error")
        return redirect(url_for("exchange_rate.index"))

    db.session.delete(exchange_rate)
    db.session.commit()
    flash(_("Tipo de cambio eliminado exitosamente."), "success")
    return redirect(url_for("exchange_rate.index"))
