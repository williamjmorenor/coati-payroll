# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Routes for nomina execution and management."""

from datetime import date
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from coati_payroll.model import db, Planilla, Nomina, NominaEmpleado, NominaDetalle, NominaNovedad
from coati_payroll.enums import NominaEstado, NovedadEstado
from coati_payroll.i18n import _
from coati_payroll.rbac import require_read_access, require_write_access
from coati_payroll.vistas.planilla import planilla_bp
from coati_payroll.vistas.planilla.services import NominaService
from coati_payroll.queue.tasks import retry_failed_nomina

# Constants
ROUTE_EJECUTAR_NOMINA = "planilla.ejecutar_nomina"
ROUTE_VER_NOMINA = "planilla.ver_nomina"
ROUTE_LISTAR_NOMINAS = "planilla.listar_nominas"
ERROR_NOMINA_NO_PERTENECE = "La nómina no pertenece a esta planilla."


@planilla_bp.route("/<planilla_id>/ejecutar", methods=["GET", "POST"])
@require_write_access()
def ejecutar_nomina(planilla_id: str):
    """Execute a payroll run for a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)

    if request.method == "POST":
        periodo_inicio = request.form.get("periodo_inicio")
        periodo_fin = request.form.get("periodo_fin")
        fecha_calculo = request.form.get("fecha_calculo")

        if not periodo_inicio or not periodo_fin:
            flash(_("Debe especificar el período de la nómina."), "error")
            return redirect(url_for(ROUTE_EJECUTAR_NOMINA, planilla_id=planilla_id))

        # Parse dates
        try:
            periodo_inicio = date.fromisoformat(periodo_inicio)
            periodo_fin = date.fromisoformat(periodo_fin)
            fecha_calculo = date.fromisoformat(fecha_calculo) if fecha_calculo else date.today()
        except ValueError:
            flash(_("Formato de fecha inválido."), "error")
            return redirect(url_for(ROUTE_EJECUTAR_NOMINA, planilla_id=planilla_id))

        nomina, errors, warnings = NominaService.ejecutar_nomina(
            planilla=planilla,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_calculo=fecha_calculo,
            usuario=current_user.usuario,
        )

        if errors:
            for error in errors:
                flash(error, "error")

        if warnings:
            for warning in warnings:
                flash(warning, "warning")

        if nomina:
            if nomina.procesamiento_en_background:
                num_empleados = nomina.total_empleados or 0
                flash(
                    _(
                        "La nómina está siendo calculada en segundo plano. "
                        "Se procesarán %(num)d empleados. "
                        "Por favor, revise el progreso en unos momentos.",
                        num=num_empleados,
                    ),
                    "info",
                )
            else:
                flash(_("Nómina generada exitosamente."), "success")
            return redirect(
                url_for(
                    ROUTE_VER_NOMINA,
                    planilla_id=planilla_id,
                    nomina_id=nomina.id,
                )
            )
        else:
            return redirect(url_for(ROUTE_EJECUTAR_NOMINA, planilla_id=planilla_id))

    # GET - show execution form
    periodo_inicio, periodo_fin = NominaService.calcular_periodo_sugerido(planilla)
    hoy = date.today()

    # Get last nomina for reference
    ultima_nomina = db.session.execute(
        db.select(Nomina).filter_by(planilla_id=planilla_id).order_by(Nomina.periodo_fin.desc())
    ).scalar_one_or_none()

    return render_template(
        "modules/planilla/ejecutar_nomina.html",
        planilla=planilla,
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        fecha_calculo=hoy,
        ultima_nomina=ultima_nomina,
    )


@planilla_bp.route("/<planilla_id>/nominas")
@require_read_access()
def listar_nominas(planilla_id: str):
    """List all nominas for a planilla."""
    planilla = db.get_or_404(Planilla, planilla_id)
    nominas = (
        db.session.execute(db.select(Nomina).filter_by(planilla_id=planilla_id).order_by(Nomina.periodo_fin.desc()))
        .scalars()
        .all()
    )

    return render_template(
        "modules/planilla/listar_nominas.html",
        planilla=planilla,
        nominas=nominas,
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>")
@require_read_access()
def ver_nomina(planilla_id: str, nomina_id: str):
    """View details of a specific nomina."""
    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_(ERROR_NOMINA_NO_PERTENECE), "error")
        return redirect(url_for(ROUTE_LISTAR_NOMINAS, planilla_id=planilla_id))

    nomina_empleados = db.session.execute(db.select(NominaEmpleado).filter_by(nomina_id=nomina_id)).scalars().all()

    # Check for errors and warnings in the processing log
    has_errors = _nomina_has_errors(nomina)
    has_warnings = _nomina_has_warnings(nomina)

    # Get error and warning messages for display
    error_messages = []
    warning_messages = []
    if nomina.log_procesamiento:
        for entry in nomina.log_procesamiento:
            status = entry.get("status") or entry.get("tipo")
            message = entry.get("message") or entry.get("mensaje") or ""
            if status == "error":
                error_messages.append(message)
            elif status in ("warning", "advertencia_contabilidad"):
                warning_messages.append(message)

    return render_template(
        "modules/planilla/ver_nomina.html",
        planilla=planilla,
        nomina=nomina,
        nomina_empleados=nomina_empleados,
        has_errors=has_errors,
        has_warnings=has_warnings,
        error_messages=error_messages,
        warning_messages=warning_messages,
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/empleado/<nomina_empleado_id>")
@require_read_access()
def ver_nomina_empleado(planilla_id: str, nomina_id: str, nomina_empleado_id: str):
    """View details of an employee's payroll."""
    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)
    nomina_empleado = db.get_or_404(NominaEmpleado, nomina_empleado_id)

    if nomina_empleado.nomina_id != nomina_id:
        flash(_("El detalle no pertenece a esta nómina."), "error")
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))

    detalles = (
        db.session.execute(
            db.select(NominaDetalle).filter_by(nomina_empleado_id=nomina_empleado_id).order_by(NominaDetalle.orden)
        )
        .scalars()
        .all()
    )

    # Separate by type
    percepciones = [d for d in detalles if d.tipo == "income"]
    deducciones = [d for d in detalles if d.tipo == "deduction"]
    prestaciones = [d for d in detalles if d.tipo == "benefit"]

    return render_template(
        "modules/planilla/ver_nomina_empleado.html",
        planilla=planilla,
        nomina=nomina,
        nomina_empleado=nomina_empleado,
        percepciones=percepciones,
        deducciones=deducciones,
        prestaciones=prestaciones,
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/progreso")
@require_read_access()
def progreso_nomina(planilla_id: str, nomina_id: str):
    """API endpoint to check calculation progress of a nomina."""
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        return jsonify({"error": "Nomina does not belong to this planilla"}), 404

    return jsonify(
        {
            "estado": nomina.estado,
            "total_empleados": nomina.total_empleados or 0,
            "empleados_procesados": nomina.empleados_procesados or 0,
            "empleados_con_error": nomina.empleados_con_error or 0,
            "progreso_porcentaje": (
                int((nomina.empleados_procesados / nomina.total_empleados) * 100)
                if nomina.total_empleados and nomina.total_empleados > 0
                else 0
            ),
            "errores_calculo": nomina.errores_calculo or {},
            "procesamiento_en_background": nomina.procesamiento_en_background,
            "empleado_actual": nomina.empleado_actual or "",
            "log_procesamiento": nomina.log_procesamiento or [],
        }
    )


def _nomina_has_errors(nomina: Nomina) -> bool:
    """Check if a nomina has errors in its processing log."""
    if not nomina.log_procesamiento:
        return False
    for entry in nomina.log_procesamiento:
        status = entry.get("status") or entry.get("tipo")
        if status == "error":
            return True
    return False


def _nomina_has_warnings(nomina: Nomina) -> bool:
    """Check if a nomina has warnings in its processing log."""
    if not nomina.log_procesamiento:
        return False
    for entry in nomina.log_procesamiento:
        status = entry.get("status") or entry.get("tipo")
        if status in ("warning", "advertencia_contabilidad"):
            return True
    return False


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/aprobar", methods=["POST"])
@require_write_access()
def aprobar_nomina(planilla_id: str, nomina_id: str):
    """Approve a nomina for payment."""
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_(ERROR_NOMINA_NO_PERTENECE), "error")
        return redirect(url_for(ROUTE_LISTAR_NOMINAS, planilla_id=planilla_id))

    if nomina.estado != "generated":
        flash(_("Solo se pueden aprobar nóminas en estado 'generated'."), "error")
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))

    # Check for errors in the processing log - cannot approve with errors
    if _nomina_has_errors(nomina):
        flash(
            _(
                "No se puede aprobar una nómina con errores de procesamiento. "
                "Corrija los errores y recalcule la nómina antes de aprobar."
            ),
            "error",
        )
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))

    nomina.estado = "approved"
    nomina.modificado_por = current_user.usuario
    db.session.commit()

    flash(_("Nómina aprobada exitosamente."), "success")
    return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/aplicar", methods=["POST"])
@require_write_access()
def aplicar_nomina(planilla_id: str, nomina_id: str):
    """Mark a nomina as applied (paid)."""
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_(ERROR_NOMINA_NO_PERTENECE), "error")
        return redirect(url_for(ROUTE_LISTAR_NOMINAS, planilla_id=planilla_id))

    if nomina.estado != "approved":
        flash(_("Solo se pueden aplicar nóminas en estado 'approved'."), "error")
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))

    nomina.estado = "applied"
    nomina.modificado_por = current_user.usuario

    # Actualizar estado de todas las novedades asociadas a "ejecutada"
    planilla = db.get_or_404(Planilla, planilla_id)
    empleado_ids = [pe.empleado_id for pe in planilla.planilla_empleados if pe.activo]

    # Actualizar novedades que corresponden a este período
    novedades = (
        db.session.execute(
            db.select(NominaNovedad).filter(
                NominaNovedad.empleado_id.in_(empleado_ids),
                NominaNovedad.fecha_novedad >= nomina.periodo_inicio,
                NominaNovedad.fecha_novedad <= nomina.periodo_fin,
                NominaNovedad.estado == NovedadEstado.PENDIENTE,
            )
        )
        .scalars()
        .all()
    )

    for novedad in novedades:
        novedad.estado = NovedadEstado.EJECUTADA
        novedad.modificado_por = current_user.usuario

    db.session.commit()

    flash(
        _("Nómina aplicada exitosamente. {} novedad(es) marcadas como ejecutadas.").format(len(novedades)),
        "success",
    )
    return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/reintentar", methods=["POST"])
@require_write_access()
def reintentar_nomina(planilla_id: str, nomina_id: str):
    """Retry processing a failed nomina."""
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_(ERROR_NOMINA_NO_PERTENECE), "error")
        return redirect(url_for(ROUTE_LISTAR_NOMINAS, planilla_id=planilla_id))

    if nomina.estado != NominaEstado.ERROR:
        flash(_("Solo se pueden reintentar nóminas en estado 'error'."), "error")
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))

    # Call the retry function
    result = retry_failed_nomina(nomina_id, current_user.usuario)

    if result.get("success"):
        flash(
            _("Reintento de nómina iniciado exitosamente. El procesamiento se realizará en segundo plano."), "success"
        )
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))
    else:
        flash(_("Error al reintentar la nómina: {}").format(result.get("error", "Error desconocido")), "error")
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/recalcular", methods=["POST"])
@require_write_access()
def recalcular_nomina(planilla_id: str, nomina_id: str):
    """Recalculate an existing nomina."""
    nomina = db.get_or_404(Nomina, nomina_id)
    planilla = db.get_or_404(Planilla, planilla_id)

    if nomina.planilla_id != planilla_id:
        flash(_(ERROR_NOMINA_NO_PERTENECE), "error")
        return redirect(url_for(ROUTE_LISTAR_NOMINAS, planilla_id=planilla_id))

    if nomina.estado == "applied":
        flash(_("No se puede recalcular una nómina en estado 'applied' (paid)."), "error")
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=nomina_id))

    new_nomina, errors, warnings = NominaService.recalcular_nomina(nomina, planilla, current_user.usuario)

    if errors:
        for error in errors:
            flash(error, "error")

    if warnings:
        for warning in warnings:
            flash(warning, "warning")

    if new_nomina:
        flash(_("Nómina recalculada exitosamente."), "success")
        return redirect(url_for(ROUTE_VER_NOMINA, planilla_id=planilla_id, nomina_id=new_nomina.id))
    else:
        flash(_("Error al recalcular la nómina."), "error")
        return redirect(url_for(ROUTE_LISTAR_NOMINAS, planilla_id=planilla_id))


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/log")
@require_read_access()
def ver_log_nomina(planilla_id: str, nomina_id: str):
    """View execution log for a nomina including warnings and errors."""
    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_(ERROR_NOMINA_NO_PERTENECE), "error")
        return redirect(url_for(ROUTE_LISTAR_NOMINAS, planilla_id=planilla_id))

    # Get log entries
    log_entries = nomina.log_procesamiento or []

    # Get comprobante warnings if exists
    from coati_payroll.model import ComprobanteContable

    comprobante = db.session.execute(db.select(ComprobanteContable).filter_by(nomina_id=nomina_id)).scalar_one_or_none()

    comprobante_warnings = comprobante.advertencias if comprobante else []

    return render_template(
        "modules/planilla/log_nomina.html",
        planilla=planilla,
        nomina=nomina,
        log_entries=log_entries,
        comprobante_warnings=comprobante_warnings,
    )


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/regenerar-comprobante", methods=["POST"])
@login_required
@require_write_access()
def regenerar_comprobante_contable(planilla_id: str, nomina_id: str):
    """Regenerate accounting voucher for an applied/paid nomina without recalculating.

    This is useful when accounting configuration was incomplete at the time of calculation
    and has been updated afterwards. Only regenerates the accounting entries based on
    existing payroll calculations.
    """
    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    # Only allow for applied or paid nominas
    from coati_payroll.enums import NominaEstado

    if nomina.estado not in (NominaEstado.APLICADO, NominaEstado.PAGADO):
        flash(
            _(
                "Solo se puede regenerar el comprobante contable para nóminas en estado 'applied' o 'paid'. "
                "Para nóminas en otros estados, use 'recalcular'."
            ),
            "error",
        )
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))

    try:
        from coati_payroll.nomina_engine.services.accounting_voucher_service import AccountingVoucherService
        from flask_login import current_user

        accounting_service = AccountingVoucherService(db.session)

        # Regenerate voucher using existing nomina data
        fecha_calculo = nomina.fecha_calculo_original or nomina.periodo_fin
        usuario = current_user.nombre_usuario if current_user and current_user.is_authenticated else None
        comprobante = accounting_service.generate_accounting_voucher(nomina, planilla, fecha_calculo, usuario)

        db.session.commit()

        flash(_("Comprobante contable regenerado exitosamente."), "success")

        # Show warnings if configuration is still incomplete
        if comprobante.advertencias:
            for warning in comprobante.advertencias:
                flash(warning, "warning")

    except Exception as e:
        db.session.rollback()
        flash(_("Error al regenerar comprobante contable: {}").format(str(e)), "error")

    return redirect(url_for("planilla.ver_log_nomina", planilla_id=planilla_id, nomina_id=nomina_id))
