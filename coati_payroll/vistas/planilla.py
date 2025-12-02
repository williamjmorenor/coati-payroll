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
    planillas = (
        db.session.execute(db.select(Planilla).order_by(Planilla.nombre))
        .scalars()
        .all()
    )
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
    """Edit basic planilla configuration."""
    planilla = db.get_or_404(Planilla, planilla_id)
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
        return redirect(url_for("planilla.config", planilla_id=planilla.id))

    # Get association counts for the summary
    counts = _get_planilla_component_counts(planilla_id)

    return render_template(
        "modules/planilla/form.html",
        form=form,
        planilla=planilla,
        is_edit=True,
        **counts,
    )


@planilla_bp.route("/<planilla_id>/config")
@login_required
def config(planilla_id: str):
    """Configuration overview page for a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

    # Get association counts for the summary
    counts = _get_planilla_component_counts(planilla_id)

    return render_template(
        "modules/planilla/config.html",
        planilla=planilla,
        **counts,
    )


# ============================================================================
# CONFIGURATION PAGES FOR ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/config/empleados")
@login_required
def config_empleados(planilla_id: str):
    """Manage employees associated with a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

    empleados_asignados = (
        db.session.execute(
            db.select(PlanillaEmpleado).filter_by(planilla_id=planilla_id)
        )
        .scalars()
        .all()
    )

    empleados_disponibles = (
        db.session.execute(
            db.select(Empleado)
            .filter_by(activo=True)
            .order_by(Empleado.primer_apellido)
        )
        .scalars()
        .all()
    )

    return render_template(
        "modules/planilla/config_empleados.html",
        planilla=planilla,
        empleados_asignados=empleados_asignados,
        empleados_disponibles=empleados_disponibles,
    )


@planilla_bp.route("/<planilla_id>/config/percepciones")
@login_required
def config_percepciones(planilla_id: str):
    """Manage perceptions associated with a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

    percepciones_asignadas = (
        db.session.execute(
            db.select(PlanillaIngreso).filter_by(planilla_id=planilla_id)
        )
        .scalars()
        .all()
    )

    percepciones_disponibles = (
        db.session.execute(
            db.select(Percepcion).filter_by(activo=True).order_by(Percepcion.nombre)
        )
        .scalars()
        .all()
    )

    return render_template(
        "modules/planilla/config_percepciones.html",
        planilla=planilla,
        percepciones_asignadas=percepciones_asignadas,
        percepciones_disponibles=percepciones_disponibles,
    )


@planilla_bp.route("/<planilla_id>/config/deducciones")
@login_required
def config_deducciones(planilla_id: str):
    """Manage deductions associated with a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

    deducciones_asignadas = (
        db.session.execute(
            db.select(PlanillaDeduccion)
            .filter_by(planilla_id=planilla_id)
            .order_by(PlanillaDeduccion.prioridad)
        )
        .scalars()
        .all()
    )

    deducciones_disponibles = (
        db.session.execute(
            db.select(Deduccion).filter_by(activo=True).order_by(Deduccion.nombre)
        )
        .scalars()
        .all()
    )

    return render_template(
        "modules/planilla/config_deducciones.html",
        planilla=planilla,
        deducciones_asignadas=deducciones_asignadas,
        deducciones_disponibles=deducciones_disponibles,
    )


@planilla_bp.route("/<planilla_id>/config/prestaciones")
@login_required
def config_prestaciones(planilla_id: str):
    """Manage benefits associated with a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

    prestaciones_asignadas = (
        db.session.execute(
            db.select(PlanillaPrestacion).filter_by(planilla_id=planilla_id)
        )
        .scalars()
        .all()
    )

    prestaciones_disponibles = (
        db.session.execute(
            db.select(Prestacion).filter_by(activo=True).order_by(Prestacion.nombre)
        )
        .scalars()
        .all()
    )

    return render_template(
        "modules/planilla/config_prestaciones.html",
        planilla=planilla,
        prestaciones_asignadas=prestaciones_asignadas,
        prestaciones_disponibles=prestaciones_disponibles,
    )


@planilla_bp.route("/<planilla_id>/config/reglas")
@login_required
def config_reglas(planilla_id: str):
    """Manage calculation rules associated with a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

    reglas_asignadas = (
        db.session.execute(
            db.select(PlanillaReglaCalculo)
            .filter_by(planilla_id=planilla_id)
            .order_by(PlanillaReglaCalculo.orden)
        )
        .scalars()
        .all()
    )

    reglas_disponibles = (
        db.session.execute(
            db.select(ReglaCalculo).filter_by(activo=True).order_by(ReglaCalculo.nombre)
        )
        .scalars()
        .all()
    )

    return render_template(
        "modules/planilla/config_reglas.html",
        planilla=planilla,
        reglas_asignadas=reglas_asignadas,
        reglas_disponibles=reglas_disponibles,
    )


@planilla_bp.route("/<planilla_id>/delete", methods=["POST"])
@login_required
def delete(planilla_id: str):
    """Delete a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

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
    # Verify planilla exists (raises 404 if not found)
    db.get_or_404(Planilla, planilla_id)
    empleado_id = request.form.get("empleado_id")

    if not empleado_id:
        flash(_("Debe seleccionar un empleado."), "error")
        return redirect(url_for("planilla.config_empleados", planilla_id=planilla_id))

    # Check if already exists
    existing = db.session.execute(
        db.select(PlanillaEmpleado).filter_by(
            planilla_id=planilla_id, empleado_id=empleado_id
        )
    ).scalar_one_or_none()

    if existing:
        flash(_("El empleado ya está asignado a esta planilla."), "warning")
        return redirect(url_for("planilla.config_empleados", planilla_id=planilla_id))

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
    return redirect(url_for("planilla.config_empleados", planilla_id=planilla_id))


@planilla_bp.route("/<planilla_id>/empleado/<association_id>/remove", methods=["POST"])
@login_required
def remove_empleado(planilla_id: str, association_id: str):
    """Remove an employee from the planilla."""
    association = db.get_or_404(PlanillaEmpleado, association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Empleado removido exitosamente."), "success")
    return redirect(url_for("planilla.config_empleados", planilla_id=planilla_id))


# ============================================================================
# PERCEPTION ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/percepcion/add", methods=["POST"])
@login_required
def add_percepcion(planilla_id: str):
    """Add a perception to the planilla."""
    # Verify planilla exists (raises 404 if not found)
    db.get_or_404(Planilla, planilla_id)
    percepcion_id = request.form.get("percepcion_id")

    if not percepcion_id:
        flash(_("Debe seleccionar una percepción."), "error")
        return redirect(
            url_for("planilla.config_percepciones", planilla_id=planilla_id)
        )

    existing = db.session.execute(
        db.select(PlanillaIngreso).filter_by(
            planilla_id=planilla_id, percepcion_id=percepcion_id
        )
    ).scalar_one_or_none()

    if existing:
        flash(_("La percepción ya está asignada a esta planilla."), "warning")
        return redirect(
            url_for("planilla.config_percepciones", planilla_id=planilla_id)
        )

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
    return redirect(url_for("planilla.config_percepciones", planilla_id=planilla_id))


@planilla_bp.route(
    "/<planilla_id>/percepcion/<association_id>/remove", methods=["POST"]
)
@login_required
def remove_percepcion(planilla_id: str, association_id: str):
    """Remove a perception from the planilla."""
    association = db.get_or_404(PlanillaIngreso, association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Percepción removida exitosamente."), "success")
    return redirect(url_for("planilla.config_percepciones", planilla_id=planilla_id))


# ============================================================================
# DEDUCTION ASSOCIATIONS (with priority)
# ============================================================================


@planilla_bp.route("/<planilla_id>/deduccion/add", methods=["POST"])
@login_required
def add_deduccion(planilla_id: str):
    """Add a deduction to the planilla with priority."""
    # Verify planilla exists (raises 404 if not found)
    db.get_or_404(Planilla, planilla_id)
    deduccion_id = request.form.get("deduccion_id")

    if not deduccion_id:
        flash(_("Debe seleccionar una deducción."), "error")
        return redirect(url_for("planilla.config_deducciones", planilla_id=planilla_id))

    existing = db.session.execute(
        db.select(PlanillaDeduccion).filter_by(
            planilla_id=planilla_id, deduccion_id=deduccion_id
        )
    ).scalar_one_or_none()

    if existing:
        flash(_("La deducción ya está asignada a esta planilla."), "warning")
        return redirect(url_for("planilla.config_deducciones", planilla_id=planilla_id))

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
    return redirect(url_for("planilla.config_deducciones", planilla_id=planilla_id))


@planilla_bp.route("/<planilla_id>/deduccion/<association_id>/remove", methods=["POST"])
@login_required
def remove_deduccion(planilla_id: str, association_id: str):
    """Remove a deduction from the planilla."""
    association = db.get_or_404(PlanillaDeduccion, association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Deducción removida exitosamente."), "success")
    return redirect(url_for("planilla.config_deducciones", planilla_id=planilla_id))


@planilla_bp.route(
    "/<planilla_id>/deduccion/<association_id>/update-priority", methods=["POST"]
)
@login_required
def update_deduccion_priority(planilla_id: str, association_id: str):
    """Update the priority of a deduction."""
    association = db.get_or_404(PlanillaDeduccion, association_id)

    prioridad = request.form.get("prioridad", type=int)
    if prioridad is not None:
        association.prioridad = prioridad
        association.modificado_por = current_user.usuario
        db.session.commit()
        flash(_("Prioridad actualizada."), "success")

    return redirect(url_for("planilla.config_deducciones", planilla_id=planilla_id))


# ============================================================================
# BENEFIT (PRESTACION) ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/prestacion/add", methods=["POST"])
@login_required
def add_prestacion(planilla_id: str):
    """Add a benefit (prestacion) to the planilla."""
    # Verify planilla exists (raises 404 if not found)
    db.get_or_404(Planilla, planilla_id)
    prestacion_id = request.form.get("prestacion_id")

    if not prestacion_id:
        flash(_("Debe seleccionar una prestación."), "error")
        return redirect(
            url_for("planilla.config_prestaciones", planilla_id=planilla_id)
        )

    existing = db.session.execute(
        db.select(PlanillaPrestacion).filter_by(
            planilla_id=planilla_id, prestacion_id=prestacion_id
        )
    ).scalar_one_or_none()

    if existing:
        flash(_("La prestación ya está asignada a esta planilla."), "warning")
        return redirect(
            url_for("planilla.config_prestaciones", planilla_id=planilla_id)
        )

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
    return redirect(url_for("planilla.config_prestaciones", planilla_id=planilla_id))


@planilla_bp.route(
    "/<planilla_id>/prestacion/<association_id>/remove", methods=["POST"]
)
@login_required
def remove_prestacion(planilla_id: str, association_id: str):
    """Remove a benefit from the planilla."""
    association = db.get_or_404(PlanillaPrestacion, association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Prestación removida exitosamente."), "success")
    return redirect(url_for("planilla.config_prestaciones", planilla_id=planilla_id))


# ============================================================================
# CALCULATION RULE ASSOCIATIONS
# ============================================================================


@planilla_bp.route("/<planilla_id>/regla/add", methods=["POST"])
@login_required
def add_regla(planilla_id: str):
    """Add a calculation rule to the planilla."""
    # Verify planilla exists (raises 404 if not found)
    db.get_or_404(Planilla, planilla_id)
    regla_calculo_id = request.form.get("regla_calculo_id")

    if not regla_calculo_id:
        flash(_("Debe seleccionar una regla de cálculo."), "error")
        return redirect(url_for("planilla.config_reglas", planilla_id=planilla_id))

    existing = db.session.execute(
        db.select(PlanillaReglaCalculo).filter_by(
            planilla_id=planilla_id, regla_calculo_id=regla_calculo_id
        )
    ).scalar_one_or_none()

    if existing:
        flash(_("La regla ya está asignada a esta planilla."), "warning")
        return redirect(url_for("planilla.config_reglas", planilla_id=planilla_id))

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
    return redirect(url_for("planilla.config_reglas", planilla_id=planilla_id))


@planilla_bp.route("/<planilla_id>/regla/<association_id>/remove", methods=["POST"])
@login_required
def remove_regla(planilla_id: str, association_id: str):
    """Remove a calculation rule from the planilla."""
    association = db.get_or_404(PlanillaReglaCalculo, association_id)
    db.session.delete(association)
    db.session.commit()
    flash(_("Regla de cálculo removida exitosamente."), "success")
    return redirect(url_for("planilla.config_reglas", planilla_id=planilla_id))


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

    planilla = db.get_or_404(Planilla, planilla_id)

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
    ultima_nomina = db.session.execute(
        db.select(Nomina)
        .filter_by(planilla_id=planilla_id)
        .order_by(Nomina.periodo_fin.desc())
    ).scalar()

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

    planilla = db.get_or_404(Planilla, planilla_id)
    nominas = (
        db.session.execute(
            db.select(Nomina)
            .filter_by(planilla_id=planilla_id)
            .order_by(Nomina.periodo_fin.desc())
        )
        .scalars()
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

    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    nomina_empleados = (
        db.session.execute(db.select(NominaEmpleado).filter_by(nomina_id=nomina_id))
        .scalars()
        .all()
    )

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

    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)
    nomina_empleado = db.get_or_404(NominaEmpleado, nomina_empleado_id)

    if nomina_empleado.nomina_id != nomina_id:
        flash(_("El detalle no pertenece a esta nómina."), "error")
        return redirect(
            url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id)
        )

    detalles = (
        db.session.execute(
            db.select(NominaDetalle)
            .filter_by(nomina_empleado_id=nomina_empleado_id)
            .order_by(NominaDetalle.orden)
        )
        .scalars()
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

    nomina = db.get_or_404(Nomina, nomina_id)

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

    nomina = db.get_or_404(Nomina, nomina_id)

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


def _get_planilla_component_counts(planilla_id: str) -> dict:
    """Get counts of all components associated with a planilla.

    Returns a dictionary with counts for empleados, percepciones, deducciones,
    prestaciones, and reglas.
    """
    return {
        "empleados_count": db.session.query(PlanillaEmpleado)
        .filter_by(planilla_id=planilla_id)
        .count(),
        "percepciones_count": db.session.query(PlanillaIngreso)
        .filter_by(planilla_id=planilla_id)
        .count(),
        "deducciones_count": db.session.query(PlanillaDeduccion)
        .filter_by(planilla_id=planilla_id)
        .count(),
        "prestaciones_count": db.session.query(PlanillaPrestacion)
        .filter_by(planilla_id=planilla_id)
        .count(),
        "reglas_count": db.session.query(PlanillaReglaCalculo)
        .filter_by(planilla_id=planilla_id)
        .count(),
    }


def _populate_form_choices(form: PlanillaForm):
    """Populate form select choices from database."""
    tipos = (
        db.session.execute(
            db.select(TipoPlanilla).filter_by(activo=True).order_by(TipoPlanilla.codigo)
        )
        .scalars()
        .all()
    )
    form.tipo_planilla_id.choices = [("", _("-- Seleccionar --"))] + [
        (t.id, f"{t.codigo} - {t.descripcion or t.codigo}") for t in tipos
    ]

    monedas = (
        db.session.execute(
            db.select(Moneda).filter_by(activo=True).order_by(Moneda.codigo)
        )
        .scalars()
        .all()
    )
    form.moneda_id.choices = [("", _("-- Seleccionar --"))] + [
        (m.id, f"{m.codigo} - {m.nombre}") for m in monedas
    ]
