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
from coati_payroll.log import log

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

    log.trace("create_app: initializing app")
    db.init_app(app)

    # Mostrar la URI de la base de datos para diagnóstico
    try:
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
        log.trace(f"create_app: SQLALCHEMY_DATABASE_URI = {db_uri}")
    except Exception:
        log.trace("create_app: could not read SQLALCHEMY_DATABASE_URI from app.config")

    # Asegurar la creación de las tablas básicas al iniciar la app.
    try:
        log.trace("create_app: calling ensure_database_initialized")
        ensure_database_initialized(app)
        log.trace("create_app: ensure_database_initialized completed")
    except Exception as exc:
        log.trace(f"create_app: ensure_database_initialized raised: {exc}")
        try:
            log.exception("create_app: ensure_database_initialized exception")
        except Exception:
            pass
        # No interrumpir el arranque si la inicialización automática falla.
        pass

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

    # Register CRUD blueprints
    from coati_payroll.vistas import user_bp, currency_bp, exchange_rate_bp, employee_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(currency_bp)
    app.register_blueprint(exchange_rate_bp)
    app.register_blueprint(employee_bp)

    return app


def ensure_database_initialized(app: Flask | None = None) -> None:
    """Verifica que la base de datos haya sido inicializada.

    - Si la tabla de `Usuario` no existe, ejecuta `create_all()`.
    - Si no existe al menos un usuario con `tipo='admin'`, crea un usuario
      administrador usando las variables de entorno `ADMIN_USER` y
      `ADMIN_PASSWORD` (con valores por defecto si no están presentes).

    Esta función puede llamarse con la `app` o desde un `app.app_context()` ya activo.
    """

    from os import environ as _environ
    from coati_payroll.model import Usuario, db as _db
    from coati_payroll.auth import proteger_passwd as _proteger_passwd

    # Determinar si debemos usar el contexto de la app pasada o el actual.
    ctx = app
    if ctx is None:
        from flask import current_app

        ctx = current_app

    with ctx.app_context():
        # Crear todas las tablas definidas (idempotente). Esto garantiza que
        # el archivo sqlite se cree cuando se use una URI sqlite.
        try:
            # Logear información útil para diagnóstico
            try:
                log.trace(f"ensure_database_initialized: engine.url = {_db.engine.url}")
            except Exception:
                log.trace("ensure_database_initialized: could not read _db.engine.url")

            try:
                db_uri = ctx.config.get("SQLALCHEMY_DATABASE_URI")
                log.trace(
                    f"ensure_database_initialized: Flask SQLALCHEMY_DATABASE_URI = {db_uri}"
                )
            except Exception:
                log.trace(
                    "ensure_database_initialized: could not read SQLALCHEMY_DATABASE_URI from ctx.config"
                )

            log.trace("ensure_database_initialized: calling create_all()")
            _db.create_all()
            log.trace("ensure_database_initialized: create_all() completed")
        except Exception as exc:
            # Registrar excepción completa para diagnóstico
            log.trace(f"ensure_database_initialized: create_all() raised: {exc}")
            try:
                log.exception("ensure_database_initialized: create_all() exception")
            except Exception:
                pass
            # Re-raise? No — dejar que el llamador decida; aquí se registra la traza.

        # Comprobar existencia de al menos un admin.
        registro_admin = _db.session.execute(
            _db.select(Usuario).filter_by(tipo="admin")
        ).scalar_one_or_none()

        if registro_admin is None:
            # Leer credenciales de entorno o usar valores por defecto.
            admin_user = _environ.get("ADMIN_USER", "coati-admin")
            admin_pass = _environ.get("ADMIN_PASSWORD", "coati-admin")

            nuevo = Usuario()
            nuevo.usuario = admin_user
            nuevo.acceso = _proteger_passwd(admin_pass)
            nuevo.nombre = "Administrador"
            nuevo.apellido = ""
            nuevo.correo_electronico = None
            nuevo.tipo = "admin"
            nuevo.activo = True

            _db.session.add(nuevo)
            _db.session.commit()
