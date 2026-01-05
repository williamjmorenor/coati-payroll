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
"""Auth module."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from datetime import datetime

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.log import log
from coati_payroll.model import Usuario, ConfiguracionGlobal, database
from coati_payroll.forms import LoginForm
from coati_payroll.i18n import _

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Mostrar y procesar el formulario de inicio de sesión.

    Rate limited to 5 attempts per minute per IP address to prevent
    brute force attacks on user credentials. Rate limiting is configured
    in coati_payroll/__init__.py using Flask-Limiter.
    """
    form = LoginForm()

    if form.validate_on_submit():
        usuario_id = form.email.data or ""
        clave = form.password.data or ""

        if validar_acceso(usuario_id, clave):
            # Cargar el registro del usuario (puede buscar por usuario o correo)
            registro = database.session.execute(
                database.select(Usuario).filter_by(usuario=usuario_id)
            ).scalar_one_or_none()

            if not registro:
                registro = database.session.execute(
                    database.select(Usuario).filter_by(correo_electronico=usuario_id)
                ).scalar_one_or_none()

            if registro is not None:
                # Check if email is verified or if restricted access is allowed
                config = database.session.execute(
                    database.select(ConfiguracionGlobal)
                ).scalar_one_or_none()
                
                permitir_acceso_no_verificado = (
                    config.permitir_acceso_email_no_verificado 
                    if config else False
                )
                
                # If email is not verified
                if not registro.email_verificado:
                    # If restricted access is not allowed, block login
                    if not permitir_acceso_no_verificado:
                        flash(
                            _("Debe verificar su correo electrónico antes de acceder al sistema."),
                            "warning"
                        )
                        return render_template("auth/login.html", form=form)
                    else:
                        # Allow restricted access and show warning
                        flash(
                            _("Su correo electrónico no ha sido verificado. Su acceso al sistema es limitado."),
                            "warning"
                        )
                
                login_user(registro)
                return redirect(url_for("app.index"))

        # Si llegamos aquí, el login falló
        flash(_("Usuario o contraseña incorrectos."), "error")

    return render_template("auth/login.html", form=form)


@auth.route("/logout")
def logout():
    """Cerrar sesión del usuario."""
    logout_user()
    flash(_("Sesión cerrada correctamente."), "info")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------------------
# Proteger contraseñas de usuarios.
# ---------------------------------------------------------------------------------------
ph = PasswordHasher()


def proteger_passwd(clave: str, /) -> bytes:
    """Devuelve una contraseña salteada con argon2."""
    _hash = ph.hash(clave.encode()).encode("utf-8")

    return _hash


def validar_acceso(usuario_id: str, acceso: str, /) -> bool:
    """Verifica el inicio de sesión del usuario."""
    log.trace(f"Verifying access for {usuario_id}")
    registro = database.session.execute(database.select(Usuario).filter_by(usuario=usuario_id)).scalar_one_or_none()

    if not registro:
        registro = database.session.execute(
            database.select(Usuario).filter_by(correo_electronico=usuario_id)
        ).scalar_one_or_none()

    if registro is not None:
        try:
            ph.verify(registro.acceso, acceso.encode())
            clave_validada = True
        except VerifyMismatchError:
            clave_validada = False
    else:
        log.trace(f"User record not found for {usuario_id}")
        clave_validada = False

    log.trace(f"Access validation result is {clave_validada}")
    if clave_validada:
        registro.ultimo_acceso = datetime.now()
        database.session.commit()

    return clave_validada
