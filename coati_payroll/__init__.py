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
"""
Coati Payroll
=============

Simple payroll management system.
"""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from os import environ

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask import Flask, flash, redirect, url_for
from flask_babel import Babel
from flask_login import LoginManager
from flask_session import Session

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.app import app as app_blueprint
from coati_payroll.auth import auth
from coati_payroll.config import DIRECTORIO_ARCHIVOS_BASE, DIRECTORIO_PLANTILLAS_BASE
from coati_payroll.i18n import _
from coati_payroll.model import Usuario, db

# Third party libraries
session_manager = Session()
login_manager = LoginManager()
babel = Babel()


# ---------------------------------------------------------------------------------------
# Control de acceso a la aplicación con la extensión flask_login.
# ---------------------------------------------------------------------------------------
@login_manager.user_loader
def cargar_sesion(identidad):
    """Devuelve la entrada correspondiente al usuario que inicio sesión desde la base de datos."""
    if identidad is not None:
        return db.session.get(Usuario, identidad)
    return None


@login_manager.unauthorized_handler
def no_autorizado():
    """Redirecciona al inicio de sesión usuarios no autorizados."""
    flash(_("Favor iniciar sesión para acceder al sistema."), "warning")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------------------
# app factory.
# ---------------------------------------------------------------------------------------
def create_app(config) -> Flask:
    """App factory."""

    app = Flask(
        __name__,
        static_folder=DIRECTORIO_ARCHIVOS_BASE,
        template_folder=DIRECTORIO_PLANTILLAS_BASE,
    )

    if config:
        app.config.from_mapping(config)
    else:
        from coati_payroll.config import configuration

        app.config.from_object(configuration)

    db.init_app(app)

    if session_redis_url := environ.get("SESSION_REDIS_URL", None):
        from redis import Redis

        app.config["SESSION_TYPE"] = "redis"
        app.config["SESSION_REDIS"] = Redis.from_url(session_redis_url)

    else:
        app.config["SESSION_TYPE"] = "sqlalchemy"
        app.config["SESSION_SQLALCHEMY"] = db
        app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
        app.config["SESSION_PERMANENT"] = False
        app.config["SESSION_USE_SIGNER"] = True

    babel.init_app(app)
    session_manager.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(app_blueprint, url_prefix="/")

    return app
