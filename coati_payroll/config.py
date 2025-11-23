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
"""Base configuration for the payroll module."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from os import environ, getcwd, name, path, sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #


# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.log import log


# ---------------------------------------------------------------------------------------
# Configuration file loading functionality
# ---------------------------------------------------------------------------------------
def load_config_from_file() -> dict:
    """
    Busca y carga configuración desde archivo con ConfigObj.

    Busca en las siguientes ubicaciones en orden:
    1. /etc/coati-payroll/coati-payroll.conf
    2. /etc/coati-payroll.conf
    3. ~/.config/coati-payroll/coati-payroll.conf
    3. ./coati-payroll.conf

    Returns:
        dict: Diccionario de configuración, vacío si no se encuentra archivo
    """
    try:
        from configobj import ConfigObj
    except ImportError:
        log.debug("ConfigObj not available, skipping file-based configuration.")
        return {}

    search_paths = [
        "/etc/coati-payroll/coati-payroll.conf",
        "/etc/coati-payroll.conf",
        path.expanduser("~/.config/coati-payroll/coati-payroll.conf"),
        path.join(getcwd(), "coati-payroll.conf"),
    ]

    for config_path in search_paths:
        if config_path and path.isfile(config_path):
            try:
                log.info(f"Loading configuration from file: {config_path}")
                config_obj = ConfigObj(config_path, encoding="utf-8")

                # Convert ConfigObj to regular dict and handle aliases
                config_dict = dict(config_obj)

                # Handle aliases as specified in the requirements
                if "DATABASE_URL" in config_dict:
                    config_dict["SQLALCHEMY_DATABASE_URI"] = config_dict["DATABASE_URL"]
                    # Keep the alias for backward compatibility

                if "REDIS_URL" in config_dict:
                    config_dict["CACHE_REDIS_URL"] = config_dict["REDIS_URL"]
                    # Keep the alias for backward compatibility

                return config_dict

            except Exception as e:
                log.warning(f"Error loading configuration from {config_path}: {e}")
                continue

    log.trace("No configuration file found in search paths.")
    return {}


# < --------------------------------------------------------------------------------------------- >
# Configuración central de la aplicación.
VALORES_TRUE = {*["1", "true", "yes", "on"], *["development", "dev"]}
DEBUG_VARS = ["DEBUG", "CI", "DEV", "DEVELOPMENT"]
FRAMEWORK_VARS = ["FLASK_ENV", "DJANGO_DEBUG", "NODE_ENV"]
GENERIC_VARS = ["ENV", "APP_ENV"]

# < --------------------------------------------------------------------------------------------- >
# Gestión de variables de entorno.
DESARROLLO = any(
    str(environ.get(var, "")).strip().lower() in VALORES_TRUE
    for var in [*DEBUG_VARS, *FRAMEWORK_VARS, *GENERIC_VARS]
)

# < --------------------------------------------------------------------------------------------- >
# Directorios base de la aplicacion
DIRECTORIO_ACTUAL: Path = Path(path.abspath(path.dirname(__file__)))
DIRECTORIO_APP: Path = DIRECTORIO_ACTUAL.parent.absolute()
DIRECTORIO_DESARROLLO: Path = DIRECTORIO_APP.parent.absolute()
DIRECTORIO_PLANTILLAS_BASE: str = path.join(DIRECTORIO_ACTUAL, "templates")
DIRECTORIO_ARCHIVOS_BASE: str = path.join(DIRECTORIO_ACTUAL, "static")

# < --------------------------------------------------------------------------------------------- >
# Directorios personalizados para la aplicación.
custom_data_dir = environ.get("NOW_LMS_DATA_DIR")
if custom_data_dir:
    log.trace("Data directory configuration found in environment variables.")
    DIRECTORIO_ARCHIVOS = custom_data_dir
else:
    DIRECTORIO_ARCHIVOS = DIRECTORIO_ARCHIVOS_BASE

custom_themes_dir = environ.get("NOW_LMS_THEMES_DIR")
if custom_themes_dir:
    log.trace("Themes directory configuration found in environment variables.")
    DIRECTORIO_PLANTILLAS = custom_themes_dir
else:
    DIRECTORIO_PLANTILLAS = DIRECTORIO_PLANTILLAS_BASE

# < --------------------------------------------------------------------------------------------- >
# Directorio base temas.
DIRECTORIO_BASE_UPLOADS = Path(str(path.join(str(DIRECTORIO_ARCHIVOS), "files")))

# < --------------------------------------------------------------------------------------------- >
# Ubicación predeterminada de base de datos SQLITE
if TESTING := (
    "PYTEST_CURRENT_TEST" in environ
    or "PYTEST_VERSION" in environ
    or "TESTING" in environ
    or hasattr(sys, "_called_from_test")
    or environ.get("CI")
    or "pytest" in sys.modules
    or path.basename(sys.argv[0]) in ["pytest", "py.test"]
):
    SQLITE: str = "sqlite://"
else:
    if name == "nt":
        SQLITE = "sqlite:///" + str(DIRECTORIO_DESARROLLO) + "\\now_lms.db"
    else:
        SQLITE = "sqlite:///" + str(DIRECTORIO_DESARROLLO) + "/now_lms.db"

# < --------------------------------------------------------------------------------------------- >
# Configuración de la aplicación:
# Se siguen las recomendaciones de "Twelve Factors App" y las opciones se leen del entorno.
CONFIGURACION: dict[str, str | bool | Path] = {}
CONFIGURACION["SECRET_KEY"] = environ.get("SECRET_KEY") or "dev"  # nosec

# Warn if using default SECRET_KEY in production
if not DESARROLLO and CONFIGURACION["SECRET_KEY"] == "dev":
    log.warning("Using default SECRET_KEY in production! This will can cause issues ")

CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("DATABASE_URL") or SQLITE
)  # nosec
# Opciones comunes de configuración.
CONFIGURACION["PRESERVE_CONTEXT_ON_EXCEPTION"] = False

if DESARROLLO:
    log.warning("Using default configuration.")
    log.info(
        "Default configuration is not recommended for use in production environments."
    )
    CONFIGURACION["SQLALCHEMY_TRACK_MODIFICATIONS"] = "False"
    CONFIGURACION["TEMPLATES_AUTO_RELOAD"] = True

# < --------------------------------------------------------------------------------------------- >
# Corrige la URI de conexión a la base de datos si el usuario omite el driver apropiado.

if DATABASE_URL_BASE := CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):

    DATABASE_URL_CORREGIDA = DATABASE_URL_BASE

    prefix = DATABASE_URL_BASE.split(":", 1)[
        0
    ]  # Extraer prefijo: "postgres", "mysql", etc.

    # Caso especial: Heroku + PostgreSQL
    if environ.get("DYNO") and prefix in (
        "postgres",
        "postgresql",
    ):  # type: ignore[operator]
        parsed = urlparse(DATABASE_URL_BASE)  # type: ignore[arg-type]
        query = parse_qs(parsed.query)
        query["sslmode"] = ["require"]
        DATABASE_URL_CORREGIDA = urlunparse(
            parsed._replace(scheme="postgresql", query=urlencode(query, doseq=True))
        )

    else:
        # Corrige el esquema según el prefijo detectado
        match prefix:
            case "postgresql":
                DATABASE_URL_CORREGIDA = (
                    "postgresql+pg8000" + DATABASE_URL_BASE[10:]
                )  # type: ignore[index]
            case "postgres":
                DATABASE_URL_CORREGIDA = (
                    "postgresql+pg8000" + DATABASE_URL_BASE[8:]
                )  # type: ignore[index]
            case "mysql":
                DATABASE_URL_CORREGIDA = (
                    "mysql+pymysql" + DATABASE_URL_BASE[5:]
                )  # type: ignore[index]
            case "mariadb":  # Not tested, but should work.
                DATABASE_URL_CORREGIDA = (
                    "mariadb+mariadbconnector" + DATABASE_URL_BASE[7:]
                )  # type: ignore[index]
            case _:
                pass  # Prefijo desconocido o ya corregido

    # Actualizar configuración si hubo cambio
    if DATABASE_URL_BASE != DATABASE_URL_CORREGIDA:
        log.info(
            f"Database URI corrected: {DATABASE_URL_BASE} → {DATABASE_URL_CORREGIDA}"
        )
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL_CORREGIDA

# < --------------------------------------------------------------------------------------------- >
configuration = CONFIGURACION
