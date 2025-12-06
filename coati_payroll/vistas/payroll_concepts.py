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
"""Payroll concepts CRUD routes: Percepciones, Deducciones, Prestaciones.

This module provides a unified, reusable backend for managing payroll concepts
(perceptions, deductions, benefits) with integrated calculation rule support.
"""

from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from coati_payroll.forms import (
    DeduccionForm,
    PercepcionForm,
    PrestacionForm,
)
from coati_payroll.i18n import _
from coati_payroll.model import Deduccion, Percepcion, Prestacion, db
from coati_payroll.rbac import require_read_access, require_write_access
from coati_payroll.vistas.constants import PER_PAGE

# Create blueprints for each concept type
percepcion_bp = Blueprint("percepcion", __name__, url_prefix="/percepciones")
deduccion_bp = Blueprint("deduccion", __name__, url_prefix="/deducciones")
prestacion_bp = Blueprint("prestacion", __name__, url_prefix="/prestaciones")


# ============================================================================
# SHARED UTILITIES
# ============================================================================


def get_concept_config(concept_type: str) -> dict:
    """Get configuration for a specific concept type.

    Args:
        concept_type: One of 'percepcion', 'deduccion', 'prestacion'

    Returns:
        Dictionary with model, form, labels, and template paths
    """
    match concept_type:
        case "percepcion":
            return {
                "model": Percepcion,
                "form": PercepcionForm,
                "singular": _("Percepción"),
                "plural": _("Percepciones"),
                "icon": "bi-plus-circle",
                "template_dir": "modules/percepcion",
                "blueprint": "percepcion",
                "route_prefix": "percepcion_",
            }
        case "deduccion":
            return {
                "model": Deduccion,
                "form": DeduccionForm,
                "singular": _("Deducción"),
                "plural": _("Deducciones"),
                "icon": "bi-dash-circle",
                "template_dir": "modules/deduccion",
                "blueprint": "deduccion",
                "route_prefix": "deduccion_",
            }
        case "prestacion":
            return {
                "model": Prestacion,
                "form": PrestacionForm,
                "singular": _("Prestación"),
                "plural": _("Prestaciones"),
                "icon": "bi-gift",
                "template_dir": "modules/prestacion",
                "blueprint": "prestacion",
                "route_prefix": "prestacion_",
            }
        case _:
            raise ValueError(f"Unknown concept type: {concept_type}")


def list_concepts(concept_type: str):
    """Generic list view for payroll concepts."""
    config = get_concept_config(concept_type)
    Model = config["model"]

    page = request.args.get("page", 1, type=int)
    pagination = db.paginate(
        db.select(Model).order_by(Model.codigo),
        page=page,
        per_page=PER_PAGE,
        error_out=False,
    )
    return render_template(
        f"{config['template_dir']}/index.html",
        items=pagination.items,
        pagination=pagination,
        config=config,
    )


def create_concept(concept_type: str):
    """Generic create view for payroll concepts."""
    config = get_concept_config(concept_type)
    Model = config["model"]
    Form = config["form"]

    form = Form()

    if form.validate_on_submit():
        concept = Model()
        populate_concept_from_form(concept, form)
        concept.creado_por = current_user.usuario

        db.session.add(concept)
        db.session.commit()
        flash(_("%(type)s creada exitosamente.", type=config["singular"]), "success")
        return redirect(url_for(f"{config['blueprint']}.{concept_type}_index"))

    return render_template(
        f"{config['template_dir']}/form.html",
        form=form,
        title=_("Nueva %(type)s", type=config["singular"]),
        config=config,
    )


def edit_concept(concept_type: str, concept_id: str):
    """Generic edit view for payroll concepts."""
    config = get_concept_config(concept_type)
    Model = config["model"]
    Form = config["form"]

    concept = db.session.get(Model, concept_id)
    if not concept:
        flash(_("%(type)s no encontrada.", type=config["singular"]), "error")
        return redirect(url_for(f"{config['blueprint']}.{concept_type}_index"))

    form = Form(obj=concept)

    if form.validate_on_submit():
        populate_concept_from_form(concept, form)
        concept.modificado_por = current_user.usuario

        db.session.commit()
        flash(_("%(type)s actualizada exitosamente.", type=config["singular"]), "success")
        return redirect(url_for(f"{config['blueprint']}.{concept_type}_index"))

    return render_template(
        f"{config['template_dir']}/form.html",
        form=form,
        title=_("Editar %(type)s", type=config["singular"]),
        concept=concept,
        config=config,
    )


def delete_concept(concept_type: str, concept_id: str):
    """Generic delete view for payroll concepts."""
    config = get_concept_config(concept_type)
    Model = config["model"]

    concept = db.session.get(Model, concept_id)
    if not concept:
        flash(_("%(type)s no encontrada.", type=config["singular"]), "error")
        return redirect(url_for(f"{config['blueprint']}.{concept_type}_index"))

    # Check if concept is in use
    if hasattr(concept, "planillas") and concept.planillas:
        flash(
            _(
                "No se puede eliminar: %(type)s está asociada a una o más planillas.",
                type=config["singular"],
            ),
            "error",
        )
        return redirect(url_for(f"{config['blueprint']}.{concept_type}_index"))

    db.session.delete(concept)
    db.session.commit()
    flash(_("%(type)s eliminada exitosamente.", type=config["singular"]), "success")
    return redirect(url_for(f"{config['blueprint']}.{concept_type}_index"))


def populate_concept_from_form(concept, form):
    """Populate a concept model from a form.

    This is a shared function that handles the common fields
    across Percepcion, Deduccion, and Prestacion.
    """
    concept.codigo = form.codigo.data
    concept.nombre = form.nombre.data
    concept.descripcion = form.descripcion.data
    concept.formula_tipo = form.formula_tipo.data
    concept.activo = form.activo.data

    # Handle monto_default
    if form.monto_default.data:
        concept.monto_default = Decimal(str(form.monto_default.data))
    else:
        concept.monto_default = None

    # Handle porcentaje
    if form.porcentaje.data:
        concept.porcentaje = Decimal(str(form.porcentaje.data))
    else:
        concept.porcentaje = None

    # Common optional fields
    if hasattr(form, "base_calculo") and form.base_calculo.data:
        concept.base_calculo = form.base_calculo.data

    if hasattr(form, "unidad_calculo") and form.unidad_calculo.data:
        concept.unidad_calculo = form.unidad_calculo.data

    if hasattr(form, "recurrente"):
        concept.recurrente = form.recurrente.data

    if hasattr(form, "contabilizable"):
        concept.contabilizable = form.contabilizable.data

    if hasattr(form, "codigo_cuenta_debe") and form.codigo_cuenta_debe.data:
        concept.codigo_cuenta_debe = form.codigo_cuenta_debe.data

    if hasattr(form, "descripcion_cuenta_debe") and form.descripcion_cuenta_debe.data:
        concept.descripcion_cuenta_debe = form.descripcion_cuenta_debe.data

    if hasattr(form, "codigo_cuenta_haber") and form.codigo_cuenta_haber.data:
        concept.codigo_cuenta_haber = form.codigo_cuenta_haber.data

    if hasattr(form, "descripcion_cuenta_haber") and form.descripcion_cuenta_haber.data:
        concept.descripcion_cuenta_haber = form.descripcion_cuenta_haber.data

    if hasattr(form, "editable_en_nomina"):
        concept.editable_en_nomina = form.editable_en_nomina.data

    # Vigencia fields
    if hasattr(form, "vigente_desde"):
        concept.vigente_desde = form.vigente_desde.data

    if hasattr(form, "valido_hasta"):
        concept.valido_hasta = form.valido_hasta.data

    # Type-specific fields
    if hasattr(form, "gravable"):  # Percepcion
        concept.gravable = form.gravable.data

    if hasattr(form, "tipo") and form.tipo.data:  # Deduccion, Prestacion
        concept.tipo = form.tipo.data

    if hasattr(form, "es_impuesto"):  # Deduccion
        concept.es_impuesto = form.es_impuesto.data

    if hasattr(form, "antes_impuesto"):  # Deduccion
        concept.antes_impuesto = form.antes_impuesto.data

    # Prestacion-specific fields
    if hasattr(form, "tope_aplicacion"):
        if form.tope_aplicacion.data:
            concept.tope_aplicacion = Decimal(str(form.tope_aplicacion.data))
        else:
            concept.tope_aplicacion = None


# ============================================================================
# PERCEPCION ROUTES
# ============================================================================


@percepcion_bp.route("/")
@require_read_access()
def percepcion_index():
    """List all perceptions."""
    return list_concepts("percepcion")


@percepcion_bp.route("/new", methods=["GET", "POST"])
@require_write_access()
def percepcion_new():
    """Create a new perception. Admin and HR can create perceptions."""
    return create_concept("percepcion")


@percepcion_bp.route("/edit/<string:concept_id>", methods=["GET", "POST"])
@require_write_access()
def percepcion_edit(concept_id: str):
    """Edit an existing perception. Admin and HR can edit perceptions."""
    return edit_concept("percepcion", concept_id)


@percepcion_bp.route("/delete/<string:concept_id>", methods=["POST"])
@require_write_access()
def percepcion_delete(concept_id: str):
    """Delete a perception. Admin and HR can delete perceptions."""
    return delete_concept("percepcion", concept_id)


# ============================================================================
# DEDUCCION ROUTES
# ============================================================================


@deduccion_bp.route("/")
@require_read_access()
def deduccion_index():
    """List all deductions."""
    return list_concepts("deduccion")


@deduccion_bp.route("/new", methods=["GET", "POST"])
@require_write_access()
def deduccion_new():
    """Create a new deduction. Admin and HR can create deductions."""
    return create_concept("deduccion")


@deduccion_bp.route("/edit/<string:concept_id>", methods=["GET", "POST"])
@require_write_access()
def deduccion_edit(concept_id: str):
    """Edit an existing deduction. Admin and HR can edit deductions."""
    return edit_concept("deduccion", concept_id)


@deduccion_bp.route("/delete/<string:concept_id>", methods=["POST"])
@require_write_access()
def deduccion_delete(concept_id: str):
    """Delete a deduction. Admin and HR can delete deductions."""
    return delete_concept("deduccion", concept_id)


# ============================================================================
# PRESTACION ROUTES
# ============================================================================


@prestacion_bp.route("/")
@require_read_access()
def prestacion_index():
    """List all benefits."""
    return list_concepts("prestacion")


@prestacion_bp.route("/new", methods=["GET", "POST"])
@require_write_access()
def prestacion_new():
    """Create a new benefit. Admin and HR can create benefits."""
    return create_concept("prestacion")


@prestacion_bp.route("/edit/<string:concept_id>", methods=["GET", "POST"])
@require_write_access()
def prestacion_edit(concept_id: str):
    """Edit an existing benefit. Admin and HR can edit benefits."""
    return edit_concept("prestacion", concept_id)


@prestacion_bp.route("/delete/<string:concept_id>", methods=["POST"])
@require_write_access()
def prestacion_delete(concept_id: str):
    """Delete a benefit. Admin and HR can delete benefits."""
    return delete_concept("prestacion", concept_id)
