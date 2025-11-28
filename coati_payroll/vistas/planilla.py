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
"""Views for managing Planilla (master payroll) and its associations.

A Planilla is the central hub that connects:
- Employees (via PlanillaEmpleado)
- Perceptions (via PlanillaIngreso)
- Deductions (via PlanillaDeduccion) - with priority ordering
- Benefits/Prestaciones (via PlanillaPrestacion)
- Calculation Rules (via PlanillaReglaCalculo)
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from coati_payroll.model import (
    db,
    Planilla,
    TipoPlanilla,
    Moneda,
    Empleado,
    Percepcion,
    Deduccion,
    Prestacion,
    ReglaCalculo,
    PlanillaEmpleado,
    PlanillaIngreso,
    PlanillaDeduccion,
    PlanillaPrestacion,
    PlanillaReglaCalculo,
)
from coati_payroll.forms import PlanillaForm
from coati_payroll.i18n import _

planilla_bp = Blueprint("planilla", __name__, url_prefix="/planilla")


@planilla_bp.route("/")
@login_required
def index():
    """List all planillas."""
    planillas = Planilla.query.order_by(Planilla.nombre).all()
    return render_template("modules/planilla/index.html", planillas=planillas)


@planilla_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create a new planilla."""
    form = PlanillaForm()
    _populate_form_choices(form)

    if form.validate_on_submit():
        planilla = Planilla(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            tipo_planilla_id=form.tipo_planilla_id.data,
            moneda_id=form.moneda_id.data,
            periodo_fiscal_inicio=form.periodo_fiscal_inicio.data,
            periodo_fiscal_fin=form.periodo_fiscal_fin.data,
            prioridad_prestamos=form.prioridad_prestamos.data or 250,
            prioridad_adelantos=form.prioridad_adelantos.data or 251,
            aplicar_prestamos_automatico=form.aplicar_prestamos_automatico.data,
            aplicar_adelantos_automatico=form.aplicar_adelantos_automatico.data,
            activo=form.activo.data,
            creado_por=current_user.usuario,
        )
        db.session.add(planilla)
        db.session.commit()
        flash(_("Planilla creada exitosamente."), "success")
        return redirect(url_for("planilla.edit", planilla_id=planilla.id))

    return render_template("modules/planilla/form.html", form=form, is_edit=False)


@planilla_bp.route("/<planilla_id>/edit", methods=["GET", "POST"])
@login_required
def edit(planilla_id: str):
    """Edit a planilla and manage its associations."""
    planilla = Planilla.query.get_or_404(planilla_id)
    form = PlanillaForm(obj=planilla)
    _populate_form_choices(form)

    if form.validate_on_submit():
        planilla.nombre = form.nombre.data
        planilla.descripcion = form.descripcion.data
        planilla.tipo_planilla_id = form.tipo_planilla_id.data
        planilla.moneda_id = form.moneda_id.data
        planilla.periodo_fiscal_inicio = form.periodo_fiscal_inicio.data
        planilla.periodo_fiscal_fin = form.periodo_fiscal_fin.data
        planilla.prioridad_prestamos = form.prioridad_prestamos.data or 250
        planilla.prioridad_adelantos = form.prioridad_adelantos.data or 251
        planilla.aplicar_prestamos_automatico = form.aplicar_prestamos_automatico.data
        planilla.aplicar_adelantos_automatico = form.aplicar_adelantos_automatico.data
        planilla.activo = form.activo.data
        planilla.modificado_por = current_user.usuario
        db.session.commit()
        flash(_("Planilla actualizada exitosamente."), "success")
        return redirect(url_for("planilla.edit", planilla_id=planilla.id))

    # Get current associations for display
    empleados_asignados = PlanillaEmpleado.query.filter_by(
        planilla_id=planilla_id
    ).all()
    percepciones_asignadas = PlanillaIngreso.query.filter_by(
        planilla_id=planilla_id
    ).all()
    deducciones_asignadas = (
        PlanillaDeduccion.query.filter_by(planilla_id=planilla_id)
        .order_by(PlanillaDeduccion.prioridad)
        .all()
    )
    prestaciones_asignadas = PlanillaPrestacion.query.filter_by(
        planilla_id=planilla_id
    ).all()
    reglas_asignadas = (
        PlanillaReglaCalculo.query.filter_by(planilla_id=planilla_id)
        .order_by(PlanillaReglaCalculo.orden)
        .all()
    )

    # Get available items for adding
    empleados_disponibles = (
        Empleado.query.filter_by(activo=True).order_by(Empleado.primer_apellido).all()
    )
    percepciones_disponibles = (
        Percepcion.query.filter_by(activo=True).order_by(Percepcion.nombre).all()
    )
    deducciones_disponibles = (
        Deduccion.query.filter_by(activo=True).order_by(Deduccion.nombre).all()
    )
    prestaciones_disponibles = (
        Prestacion.query.filter_by(activo=True).order_by(Prestacion.nombre).all()
    )
    reglas_disponibles = (
        ReglaCalculo.query.filter_by(activo=True).order_by(ReglaCalculo.nombre).all()
    )

    return render_template(
        "modules/planilla/form.html",
        form=form,
        planilla=planilla,
        is_edit=True,
        empleados_asignados=empleados_asignados,
        percepciones_asignadas=percepciones_asignadas,
        deducciones_asignadas=deducciones_asignadas,
        prestaciones_asignadas=prestaciones_asignadas,
        reglas_asignadas=reglas_asignadas,
        empleados_disponibles=empleados_disponibles,
        percepciones_disponibles=percepciones_disponibles,
        deducciones_disponibles=deducciones_disponibles,
        prestaciones_disponibles=prestaciones_disponibles,
        reglas_disponibles=reglas_disponibles,
    )


@planilla_bp.route("/<planilla_id>/delete", methods=["POST"])
@login_required
def delete(planilla_id: str):
    """Delete a planilla."""
    planilla = Planilla.query.get_or_404(planilla_id)

    # Check if planilla has nominas (payroll runs)
    if planilla.nominas:
        flash(_("No se puede eliminar una planilla con nóminas generadas."), "error")
        return redirect(url_for("planilla.index"))

    db.session.delete(planilla)
    db.session.commit()
    flash(_("Planilla eliminada exitosamente."), "success")
    return redirect(url_for("planilla.index"))


# ============================================================================
# EMPLOYEE ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/empleado/add", methods=["POST"])
@login_required
def add_empleado(planilla_id: str):
    """Add an employee to the planilla."""
    planilla = Planilla.query.get_or_404(planilla_id)
    empleado_id = request.form.get("empleado_id")

    if not empleado_id:
        flash(_("Debe seleccionar un empleado."), "error")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    # Check if already exists
    existing = PlanillaEmpleado.query.filter_by(
        planilla_id=planilla_id, empleado_id=empleado_id
    ).first()

    if existing:
        flash(_("El empleado ya está asignado a esta planilla."), "warning")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    association = PlanillaEmpleado(
        planilla_id=planilla_id,
        empleado_id=empleado_id,
        fecha_inicio=date.today(),
        activo=True,
        creado_por=current_user.usuario,
    )
    db.session.add(association)
    db.session.commit()
    flash(_("Empleado agregado exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


@planilla_bp.route("/<planilla_id>/empleado/<association_id>/remove", methods=["POST"])
@login_required
def remove_empleado(planilla_id: str, association_id: str):
    """Remove an employee from the planilla."""
    association = PlanillaEmpleado.query.get_or_404(association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Empleado removido exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


# ============================================================================
# PERCEPTION ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/percepcion/add", methods=["POST"])
@login_required
def add_percepcion(planilla_id: str):
    """Add a perception to the planilla."""
    planilla = Planilla.query.get_or_404(planilla_id)
    percepcion_id = request.form.get("percepcion_id")

    if not percepcion_id:
        flash(_("Debe seleccionar una percepción."), "error")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    existing = PlanillaIngreso.query.filter_by(
        planilla_id=planilla_id, percepcion_id=percepcion_id
    ).first()

    if existing:
        flash(_("La percepción ya está asignada a esta planilla."), "warning")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    orden = request.form.get("orden", 0, type=int)

    association = PlanillaIngreso(
        planilla_id=planilla_id,
        percepcion_id=percepcion_id,
        orden=orden,
        editable=True,
        activo=True,
        creado_por=current_user.usuario,
    )
    db.session.add(association)
    db.session.commit()
    flash(_("Percepción agregada exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


@planilla_bp.route(
    "/<planilla_id>/percepcion/<association_id>/remove", methods=["POST"]
)
@login_required
def remove_percepcion(planilla_id: str, association_id: str):
    """Remove a perception from the planilla."""
    association = PlanillaIngreso.query.get_or_404(association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Percepción removida exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


# ============================================================================
# DEDUCTION ASSOCIATIONS (with priority)
# ============================================================================


@planilla_bp.route("/<planilla_id>/deduccion/add", methods=["POST"])
@login_required
def add_deduccion(planilla_id: str):
    """Add a deduction to the planilla with priority."""
    planilla = Planilla.query.get_or_404(planilla_id)
    deduccion_id = request.form.get("deduccion_id")

    if not deduccion_id:
        flash(_("Debe seleccionar una deducción."), "error")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    existing = PlanillaDeduccion.query.filter_by(
        planilla_id=planilla_id, deduccion_id=deduccion_id
    ).first()

    if existing:
        flash(_("La deducción ya está asignada a esta planilla."), "warning")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    prioridad = request.form.get("prioridad", 100, type=int)
    es_obligatoria = request.form.get("es_obligatoria") == "on"

    association = PlanillaDeduccion(
        planilla_id=planilla_id,
        deduccion_id=deduccion_id,
        prioridad=prioridad,
        es_obligatoria=es_obligatoria,
        editable=True,
        activo=True,
        creado_por=current_user.usuario,
    )
    db.session.add(association)
    db.session.commit()
    flash(_("Deducción agregada exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


@planilla_bp.route("/<planilla_id>/deduccion/<association_id>/remove", methods=["POST"])
@login_required
def remove_deduccion(planilla_id: str, association_id: str):
    """Remove a deduction from the planilla."""
    association = PlanillaDeduccion.query.get_or_404(association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Deducción removida exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


@planilla_bp.route(
    "/<planilla_id>/deduccion/<association_id>/update-priority", methods=["POST"]
)
@login_required
def update_deduccion_priority(planilla_id: str, association_id: str):
    """Update the priority of a deduction."""
    association = PlanillaDeduccion.query.get_or_404(association_id)

    prioridad = request.form.get("prioridad", type=int)
    if prioridad is not None:
        association.prioridad = prioridad
        association.modificado_por = current_user.usuario
        db.session.commit()
        flash(_("Prioridad actualizada."), "success")

    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


# ============================================================================
# BENEFIT (PRESTACION) ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/prestacion/add", methods=["POST"])
@login_required
def add_prestacion(planilla_id: str):
    """Add a benefit (prestacion) to the planilla."""
    planilla = Planilla.query.get_or_404(planilla_id)
    prestacion_id = request.form.get("prestacion_id")

    if not prestacion_id:
        flash(_("Debe seleccionar una prestación."), "error")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    existing = PlanillaPrestacion.query.filter_by(
        planilla_id=planilla_id, prestacion_id=prestacion_id
    ).first()

    if existing:
        flash(_("La prestación ya está asignada a esta planilla."), "warning")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    orden = request.form.get("orden", 0, type=int)

    association = PlanillaPrestacion(
        planilla_id=planilla_id,
        prestacion_id=prestacion_id,
        orden=orden,
        editable=True,
        activo=True,
        creado_por=current_user.usuario,
    )
    db.session.add(association)
    db.session.commit()
    flash(_("Prestación agregada exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


@planilla_bp.route(
    "/<planilla_id>/prestacion/<association_id>/remove", methods=["POST"]
)
@login_required
def remove_prestacion(planilla_id: str, association_id: str):
    """Remove a benefit from the planilla."""
    association = PlanillaPrestacion.query.get_or_404(association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Prestación removida exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


# ============================================================================
# CALCULATION RULE ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/regla/add", methods=["POST"])
@login_required
def add_regla(planilla_id: str):
    """Add a calculation rule to the planilla."""
    planilla = Planilla.query.get_or_404(planilla_id)
    regla_calculo_id = request.form.get("regla_calculo_id")

    if not regla_calculo_id:
        flash(_("Debe seleccionar una regla de cálculo."), "error")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    existing = PlanillaReglaCalculo.query.filter_by(
        planilla_id=planilla_id, regla_calculo_id=regla_calculo_id
    ).first()

    if existing:
        flash(_("La regla ya está asignada a esta planilla."), "warning")
        return redirect(url_for("planilla.edit", planilla_id=planilla_id))

    orden = request.form.get("orden", 0, type=int)

    association = PlanillaReglaCalculo(
        planilla_id=planilla_id,
        regla_calculo_id=regla_calculo_id,
        orden=orden,
        activo=True,
        creado_por=current_user.usuario,
    )
    db.session.add(association)
    db.session.commit()
    flash(_("Regla de cálculo agregada exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


@planilla_bp.route("/<planilla_id>/regla/<association_id>/remove", methods=["POST"])
@login_required
def remove_regla(planilla_id: str, association_id: str):
    """Remove a calculation rule from the planilla."""
    association = PlanillaReglaCalculo.query.get_or_404(association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Regla de cálculo removida exitosamente."), "success")
    return redirect(url_for("planilla.edit", planilla_id=planilla_id))


# ============================================================================
# NOMINA EXECUTION
# ============================================================================


@planilla_bp.route("/<planilla_id>/ejecutar", methods=["GET", "POST"])
@login_required
def ejecutar_nomina(planilla_id: str):
    """Execute a payroll run for a planilla."""
    from datetime import date
    from coati_payroll.nomina_engine import NominaEngine
    from coati_payroll.model import Nomina

    planilla = Planilla.query.get_or_404(planilla_id)

    if request.method == "POST":
        periodo_inicio = request.form.get("periodo_inicio")
        periodo_fin = request.form.get("periodo_fin")
        fecha_calculo = request.form.get("fecha_calculo")

        if not periodo_inicio or not periodo_fin:
            flash(_("Debe especificar el período de la nómina."), "error")
            return redirect(
                url_for("planilla.ejecutar_nomina", planilla_id=planilla_id)
            )

        # Parse dates
        try:
            periodo_inicio = date.fromisoformat(periodo_inicio)
            periodo_fin = date.fromisoformat(periodo_fin)
            fecha_calculo = (
                date.fromisoformat(fecha_calculo) if fecha_calculo else date.today()
            )
        except ValueError:
            flash(_("Formato de fecha inválido."), "error")
            return redirect(
                url_for("planilla.ejecutar_nomina", planilla_id=planilla_id)
            )

        # Execute the payroll
        engine = NominaEngine(
            planilla=planilla,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_calculo=fecha_calculo,
            usuario=current_user.usuario,
        )

        nomina = engine.ejecutar()

        if engine.errors:
            for error in engine.errors:
                flash(error, "error")

        if engine.warnings:
            for warning in engine.warnings:
                flash(warning, "warning")

        if nomina:
            flash(_("Nómina generada exitosamente."), "success")
            return redirect(
                url_for(
                    "planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina.id
                )
            )
        else:
            return redirect(
                url_for("planilla.ejecutar_nomina", planilla_id=planilla_id)
            )

    # GET - show execution form
    # Get last nomina for default dates
    ultima_nomina = (
        Nomina.query.filter_by(planilla_id=planilla_id)
        .order_by(Nomina.periodo_fin.desc())
        .first()
    )

    # Calculate suggested period
    from datetime import timedelta

    hoy = date.today()

    if ultima_nomina:
        # Start from the day after last period ended
        periodo_inicio_sugerido = ultima_nomina.periodo_fin + timedelta(days=1)
    else:
        # First day of current month
        periodo_inicio_sugerido = hoy.replace(day=1)

    # Calculate end of period based on tipo_planilla
    tipo = planilla.tipo_planilla
    match tipo.periodicidad if tipo else "mensual":
        case "semanal":
            periodo_fin_sugerido = periodo_inicio_sugerido + timedelta(days=6)
        case "quincenal":
            if periodo_inicio_sugerido.day <= 15:
                periodo_fin_sugerido = periodo_inicio_sugerido.replace(day=15)
            else:
                # End of month
                next_month = periodo_inicio_sugerido.replace(day=28) + timedelta(days=4)
                periodo_fin_sugerido = next_month - timedelta(days=next_month.day)
        case _:  # mensual or other
            # End of month
            next_month = periodo_inicio_sugerido.replace(day=28) + timedelta(days=4)
            periodo_fin_sugerido = next_month - timedelta(days=next_month.day)

    return render_template(
        "modules/planilla/ejecutar_nomina.html",
        planilla=planilla,
        periodo_inicio=periodo_inicio_sugerido,
        periodo_fin=periodo_fin_sugerido,
        fecha_calculo=hoy,
        ultima_nomina=ultima_nomina,
    )


@planilla_bp.route("/<planilla_id>/nominas")
@login_required
def listar_nominas(planilla_id: str):
    """List all nominas for a planilla."""
    from coati_payroll.model import Nomina

    planilla = Planilla.query.get_or_404(planilla_id)
    nominas = (
        Nomina.query.filter_by(planilla_id=planilla_id)
        .order_by(Nomina.periodo_fin.desc())
        .all()
    )

    return render_template(
        "modules/planilla/listar_nominas.html",
        planilla=planilla,
        nominas=nominas,
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>")
@login_required
def ver_nomina(planilla_id: str, nomina_id: str):
    """View details of a specific nomina."""
    from coati_payroll.model import Nomina, NominaEmpleado

    planilla = Planilla.query.get_or_404(planilla_id)
    nomina = Nomina.query.get_or_404(nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    nomina_empleados = NominaEmpleado.query.filter_by(nomina_id=nomina_id).all()

    return render_template(
        "modules/planilla/ver_nomina.html",
        planilla=planilla,
        nomina=nomina,
        nomina_empleados=nomina_empleados,
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/empleado/<nomina_empleado_id>")
@login_required
def ver_nomina_empleado(planilla_id: str, nomina_id: str, nomina_empleado_id: str):
    """View details of an employee's payroll."""
    from coati_payroll.model import Nomina, NominaEmpleado, NominaDetalle

    planilla = Planilla.query.get_or_404(planilla_id)
    nomina = Nomina.query.get_or_404(nomina_id)
    nomina_empleado = NominaEmpleado.query.get_or_404(nomina_empleado_id)

    if nomina_empleado.nomina_id != nomina_id:
        flash(_("El detalle no pertenece a esta nómina."), "error")
        return redirect(
            url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id)
        )

    detalles = (
        NominaDetalle.query.filter_by(nomina_empleado_id=nomina_empleado_id)
        .order_by(NominaDetalle.orden)
        .all()
    )

    # Separate by type
    percepciones = [d for d in detalles if d.tipo == "ingreso"]
    deducciones = [d for d in detalles if d.tipo == "deduccion"]
    prestaciones = [d for d in detalles if d.tipo == "prestacion"]

    return render_template(
        "modules/planilla/ver_nomina_empleado.html",
        planilla=planilla,
        nomina=nomina,
        nomina_empleado=nomina_empleado,
        percepciones=percepciones,
        deducciones=deducciones,
        prestaciones=prestaciones,
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/aprobar", methods=["POST"])
@login_required
def aprobar_nomina(planilla_id: str, nomina_id: str):
    """Approve a nomina for payment."""
    from coati_payroll.model import Nomina

    nomina = Nomina.query.get_or_404(nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    if nomina.estado != "generado":
        flash(_("Solo se pueden aprobar nóminas en estado 'generado'."), "error")
        return redirect(
            url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id)
        )

    nomina.estado = "aprobado"
    nomina.modificado_por = current_user.usuario
    db.session.commit()

    flash(_("Nómina aprobada exitosamente."), "success")
    return redirect(
        url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id)
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/aplicar", methods=["POST"])
@login_required
def aplicar_nomina(planilla_id: str, nomina_id: str):
    """Mark a nomina as applied (paid)."""
    from coati_payroll.model import Nomina

    nomina = Nomina.query.get_or_404(nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    if nomina.estado != "aprobado":
        flash(_("Solo se pueden aplicar nóminas en estado 'aprobado'."), "error")
        return redirect(
            url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id)
        )

    nomina.estado = "aplicado"
    nomina.modificado_por = current_user.usuario
    db.session.commit()

    flash(_("Nómina aplicada exitosamente."), "success")
    return redirect(
        url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id)
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _populate_form_choices(form: PlanillaForm):
    """Populate form select choices from database."""
    tipos = (
        TipoPlanilla.query.filter_by(activo=True).order_by(TipoPlanilla.codigo).all()
    )
    form.tipo_planilla_id.choices = [("", _("-- Seleccionar --"))] + [
        (t.id, f"{t.codigo} - {t.descripcion or t.codigo}") for t in tipos
    ]

    monedas = Moneda.query.filter_by(activo=True).order_by(Moneda.codigo).all()
    form.moneda_id.choices = [("", _("-- Seleccionar --"))] + [
        (m.id, f"{m.codigo} - {m.nombre}") for m in monedas
    ]
