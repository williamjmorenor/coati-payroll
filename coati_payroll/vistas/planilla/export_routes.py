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
"""Routes for Excel export operations."""

from flask import flash, redirect, send_file, url_for
from flask_login import login_required

from coati_payroll.model import db, Planilla, Nomina
from coati_payroll.i18n import _
from coati_payroll.rbac import require_read_access
from coati_payroll.vistas.planilla import planilla_bp
from coati_payroll.vistas.planilla.helpers import check_openpyxl_available
from coati_payroll.vistas.planilla.services import ExportService


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/exportar-excel")
@login_required
@require_read_access()
def exportar_nomina_excel(planilla_id: str, nomina_id: str):
    """Export nomina to Excel with employee details and calculations."""
    if not check_openpyxl_available():
        flash(_("Excel export no disponible. Instale openpyxl."), "warning")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))

    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    try:
        output, filename = ExportService.exportar_nomina_excel(planilla, nomina)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        flash(_("Error al exportar nómina: {}").format(str(e)), "error")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/exportar-prestaciones-excel")
@login_required
@require_read_access()
def exportar_prestaciones_excel(planilla_id: str, nomina_id: str):
    """Export benefits (prestaciones) to Excel separately."""
    if not check_openpyxl_available():
        flash(_("Excel export no disponible. Instale openpyxl."), "warning")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))

    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    try:
        output, filename = ExportService.exportar_prestaciones_excel(planilla, nomina)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        flash(_("Error al exportar prestaciones: {}").format(str(e)), "error")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/exportar-comprobante-excel")
@login_required
@require_read_access()
def exportar_comprobante_excel(planilla_id: str, nomina_id: str):
    """Export summarized accounting voucher (comprobante contable) to Excel."""
    if not check_openpyxl_available():
        flash(_("Excel export no disponible. Instale openpyxl."), "warning")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))

    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    # Check if comprobante exists
    from coati_payroll.model import ComprobanteContable

    comprobante = db.session.execute(
        db.select(ComprobanteContable).filter_by(nomina_id=nomina_id)
    ).scalar_one_or_none()

    if not comprobante:
        flash(_("No existe comprobante contable para esta nómina. Debe recalcular la nómina."), "error")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))

    # Check for configuration warnings
    if comprobante.advertencias:
        flash(
            _("ADVERTENCIA: La configuración contable está incompleta. Revise las advertencias en el log."),
            "warning",
        )

    try:
        output, filename = ExportService.exportar_comprobante_excel(planilla, nomina)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        flash(_("Error al exportar comprobante: {}").format(str(e)), "error")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))


@planilla_bp.route("/<planilla_id>/nomina/<nomina_id>/exportar-comprobante-detallado-excel")
@login_required
@require_read_access()
def exportar_comprobante_detallado_excel(planilla_id: str, nomina_id: str):
    """Export detailed accounting voucher per employee to Excel."""
    if not check_openpyxl_available():
        flash(_("Excel export no disponible. Instale openpyxl."), "warning")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))

    planilla = db.get_or_404(Planilla, planilla_id)
    nomina = db.get_or_404(Nomina, nomina_id)

    if nomina.planilla_id != planilla_id:
        flash(_("La nómina no pertenece a esta planilla."), "error")
        return redirect(url_for("planilla.listar_nominas", planilla_id=planilla_id))

    # Check if comprobante exists
    from coati_payroll.model import ComprobanteContable

    comprobante = db.session.execute(
        db.select(ComprobanteContable).filter_by(nomina_id=nomina_id)
    ).scalar_one_or_none()

    if not comprobante:
        flash(_("No existe comprobante contable para esta nómina. Debe recalcular la nómina."), "error")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))

    # Check for configuration warnings
    if comprobante.advertencias:
        flash(
            _("ADVERTENCIA: La configuración contable está incompleta. Revise las advertencias en el log."),
            "warning",
        )

    try:
        output, filename = ExportService.exportar_comprobante_detallado_excel(planilla, nomina)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        flash(_("Error al exportar comprobante detallado: {}").format(str(e)), "error")
        return redirect(url_for("planilla.ver_nomina", planilla_id=planilla_id, nomina_id=nomina_id))
