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
"""Global configuration views."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask import Blueprint, flash, redirect, render_template, request, url_for

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.i18n import _
from coati_payroll.rbac import require_write_access
from coati_payroll.locale_config import (
    SUPPORTED_LANGUAGES,
    get_language_from_db,
    set_language_in_db,
)

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


@configuracion_bp.route("/")
@require_write_access()
def index():
    """Display global configuration page."""
    from coati_payroll.model import ConfiguracionGlobal, db
    
    current_language = get_language_from_db()
    
    # Get current configuration
    config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one_or_none()
    permitir_acceso_email_no_verificado = (
        config.permitir_acceso_email_no_verificado if config else False
    )

    # Language names for display
    language_names = {"en": "English", "es": "Español"}

    return render_template(
        "modules/configuracion/index.html",
        current_language=current_language,
        supported_languages=SUPPORTED_LANGUAGES,
        language_names=language_names,
        permitir_acceso_email_no_verificado=permitir_acceso_email_no_verificado,
    )


@configuracion_bp.route("/idioma", methods=["POST"])
@require_write_access()
def cambiar_idioma():
    """Change the application language."""
    new_language = request.form.get("idioma", "").strip()

    if not new_language:
        flash(_("Por favor seleccione un idioma."), "warning")
        return redirect(url_for("configuracion.index"))

    if new_language not in SUPPORTED_LANGUAGES:
        flash(_("Idioma no soportado."), "danger")
        return redirect(url_for("configuracion.index"))

    try:
        set_language_in_db(new_language)

        # Message will be shown in the new language after redirect
        language_names = {"en": "English", "es": "Español"}
        flash(
            _(
                "Idioma actualizado a %(language)s.",
                language=language_names[new_language],
            ),
            "success",
        )
    except Exception as e:
        flash(_("Error al actualizar el idioma: %(error)s", error=str(e)), "danger")

    return redirect(url_for("configuracion.index"))


@configuracion_bp.route("/acceso_email", methods=["POST"])
@require_write_access()
def cambiar_acceso_email():
    """Change the restricted access for unverified email configuration."""
    from coati_payroll.model import ConfiguracionGlobal, db
    
    permitir = request.form.get("permitir_acceso_email_no_verificado") == "on"

    try:
        config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one_or_none()

        if config:
            config.permitir_acceso_email_no_verificado = permitir
        else:
            # Create new configuration record
            config = ConfiguracionGlobal()
            config.permitir_acceso_email_no_verificado = permitir
            db.session.add(config)

        db.session.commit()

        if permitir:
            flash(
                _("Acceso limitado habilitado para usuarios con correo no verificado."),
                "success",
            )
        else:
            flash(
                _("Acceso limitado deshabilitado para usuarios con correo no verificado."),
                "success",
            )
    except Exception as e:
        flash(_("Error al actualizar la configuración: %(error)s", error=str(e)), "danger")

    return redirect(url_for("configuracion.index"))
