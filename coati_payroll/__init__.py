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
# Standard library
# <-------------------------------------------------------------------------> #
from datetime import datetime

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask import Flask, flash, redirect, url_for
from flask_babel import Babel
from flask_login import LoginManager
from flask_session import Session
import flask_session.sqlalchemy.sqlalchemy as fs_sqlalchemy
from sqlalchemy import Column, DateTime, Integer, LargeBinary, Sequence, String

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.app import app as app_blueprint
from coati_payroll.auth import auth
from coati_payroll.config import DIRECTORIO_ARCHIVOS_BASE, DIRECTORIO_PLANTILLAS_BASE
from coati_payroll.i18n import _
from coati_payroll.model import Usuario, db
from coati_payroll.log import log


# Patch Flask-Session to use extend_existing=True for the sessions table
# This prevents the "Table 'sessions' is already defined" error when the app
# is initialized multiple times (e.g., by the CLI).
#
# NOTE: This monkey-patch is necessary because Flask-Session v0.8.0 does not
# provide a configuration option to set extend_existing=True on the sessions
# table. Without this, the CLI fails when it initializes the app multiple times.
# This is a minimal, surgical fix that only modifies the table_args to add
# extend_existing=True. If Flask-Session adds native support for this in a
# future version, this patch can be removed.
def _patched_create_session_model(db, table_name, schema=None, bind_key=None, sequence=None):
    """Patched version of Flask-Session's create_session_model that includes extend_existing=True."""

    class Session(db.Model):
        __tablename__ = table_name
        # Include extend_existing=True to allow table redefinition
        __table_args__ = {"schema": schema, "extend_existing": True} if schema else {"extend_existing": True}
        __bind_key__ = bind_key

        id = Column(Integer, Sequence(sequence), primary_key=True) if sequence else Column(Integer, primary_key=True)
        session_id = Column(String(255), unique=True)
        data = Column(LargeBinary)
        expiry = Column(DateTime)

        def __init__(self, session_id: str, data, expiry: datetime):
            self.session_id = session_id
            self.data = data
            self.expiry = expiry

        def __repr__(self):
            return f"<Session data {self.data}>"

    return Session


fs_sqlalchemy.create_session_model = _patched_create_session_model

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
# Locale selector for Flask-Babel
# ---------------------------------------------------------------------------------------
def get_locale():
    """Determine the locale for the current request.

    Returns the language configured in the database (with caching).
    Falls back to English if database is not available.
    """
    try:
        from coati_payroll.locale_config import get_language_from_db

        return get_language_from_db()
    except Exception:
        # Fallback to default if database not available (e.g., during initialization)
        return "en"


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

    # Warn if using default SECRET_KEY in production
    from coati_payroll.config import DESARROLLO

    if not DESARROLLO and app.config.get("SECRET_KEY") == "dev":
        log.warning("Using default SECRET_KEY in production! This can cause issues.")

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

    # Configure session storage
    # In testing mode, respect the SESSION_TYPE from config (e.g., filesystem)
    # to avoid conflicts with parallel test execution
    if not app.config.get("SESSION_TYPE"):
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

    # Configure Flask-Babel
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"
    babel.init_app(app, locale_selector=get_locale)

    session_manager.init_app(app)
    login_manager.init_app(app)

    # Load initial data and demo data after Babel is initialized
    # This allows translations to work properly
    # Skip loading in test environments to keep test databases clean
    if not app.config.get("TESTING"):
        with app.app_context():
            # Load initial data (currencies, income concepts, deduction concepts)
            # Strings are translated automatically based on the configured language
            try:
                from coati_payroll.initial_data import load_initial_data

                load_initial_data()
            except Exception as exc:
                log.trace(f"Could not load initial data: {exc}")

            # Load demo data if COATI_LOAD_DEMO_DATA environment variable is set
            # This provides comprehensive sample data for manual testing
            if environ.get("COATI_LOAD_DEMO_DATA"):
                try:
                    from coati_payroll.demo_data import load_demo_data

                    load_demo_data()
                except Exception as exc:
                    log.trace(f"Could not load demo data: {exc}")

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(app_blueprint, url_prefix="/")

    # Register CRUD blueprints
    from coati_payroll.vistas import (
        user_bp,
        currency_bp,
        exchange_rate_bp,
        employee_bp,
        custom_field_bp,
        calculation_rule_bp,
        percepcion_bp,
        deduccion_bp,
        prestacion_bp,
        planilla_bp,
        tipo_planilla_bp,
        prestamo_bp,
        empresa_bp,
        configuracion_bp,
        carga_inicial_prestacion_bp,
        vacation_bp,
        prestacion_management_bp,
        report_bp,
        settings_bp,
    )

    app.register_blueprint(user_bp)
    app.register_blueprint(currency_bp)
    app.register_blueprint(exchange_rate_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(custom_field_bp)
    app.register_blueprint(calculation_rule_bp)
    app.register_blueprint(percepcion_bp)
    app.register_blueprint(deduccion_bp)
    app.register_blueprint(prestacion_bp)
    app.register_blueprint(planilla_bp)
    app.register_blueprint(tipo_planilla_bp)
    app.register_blueprint(prestamo_bp)
    app.register_blueprint(empresa_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(carga_inicial_prestacion_bp)
    app.register_blueprint(vacation_bp)
    app.register_blueprint(prestacion_management_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(settings_bp)

    # Register CLI commands
    from coati_payroll.cli import register_cli_commands

    register_cli_commands(app)

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
                log.trace(f"ensure_database_initialized: Flask SQLALCHEMY_DATABASE_URI = {db_uri}")
            except Exception:
                log.trace("ensure_database_initialized: could not read SQLALCHEMY_DATABASE_URI from ctx.config")

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
        registro_admin = _db.session.execute(_db.select(Usuario).filter_by(tipo="admin")).scalar_one_or_none()

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

        # Initialize language from environment variable if provided
        try:
            from coati_payroll.locale_config import initialize_language_from_env

            initialize_language_from_env()
        except Exception as exc:
            log.trace(f"Could not initialize language from environment: {exc}")
