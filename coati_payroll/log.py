# Copyright 2022 - 2024 BMO Soluciones, S.A.
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
#
"""Configuración de logs."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
import logging
from os import environ
from sys import stdout

# <-------------------------------------------------------------------------> #
# Third-party libraries
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #

# Definir nivel TRACE
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")


# Método adicional para usar logger.trace(...)
def trace(self, message, *args, **kwargs):
    """Log a message with TRACE level."""
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.trace = trace

# Configurar nivel desde variable de entorno (default: INFO)
log_level_str = environ.get("LOG_LEVEL", "INFO").upper()

# Soporte de niveles personalizados
custom_levels = {
    "TRACE": TRACE_LEVEL_NUM,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Nivel numérico, default INFO si no coincide
numeric_level = custom_levels.get(log_level_str, logging.INFO)

# Configurar logger raíz
root_logger = logging.getLogger("now_lms")
root_logger.setLevel(numeric_level)

# Handler solo para stdout
console_handler = logging.StreamHandler(stdout)
console_handler.setLevel(numeric_level)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Configurar logger de Flask y Werkzeug al mismo nivel
logging.getLogger("flask").setLevel(numeric_level)
logging.getLogger("werkzeug").setLevel(numeric_level)

# Configurar logger de SQLAlchemy al nivel WARNING
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

LOG_LEVEL = root_logger.getEffectiveLevel()

log = root_logger
logger = root_logger


# Cached helper to avoid repeated debug/level checks on every trace call
_TRACE_ACTIVE: bool | None = None


def _compute_trace_active(debug_flag: bool | None = None) -> bool:
    """Compute whether TRACE logging should be emitted.

    Prefers an explicit debug_flag, then Flask's current_app.debug (if available),
    then FLASK_DEBUG/FLASK_ENV environment hints. Also verifies the logger is
    actually enabled for TRACE level.
    """

    # Determine debug flag
    if debug_flag is None:
        try:
            from flask import current_app

            debug_flag = bool(getattr(current_app, "debug", False))
        except Exception:
            debug_flag = False

    if not debug_flag:
        debug_env = environ.get("FLASK_DEBUG") or environ.get("FLASK_ENV")
        if debug_env:
            debug_flag = str(debug_env).lower() in {
                "1",
                "true",
                "yes",
                "on",
                "development",
                "dev",
                "debug",
            }

    try:
        return bool(debug_flag) and log.isEnabledFor(TRACE_LEVEL_NUM)
    except Exception:
        return False


def is_trace_enabled(*, force_refresh: bool = False, debug_flag: bool | None = None) -> bool:
    """Return cached TRACE-enabled flag, computing once unless refreshed.

    This keeps per-log-call overhead minimal while allowing an explicit refresh
    if runtime configuration changes.
    """

    global _TRACE_ACTIVE
    if force_refresh or _TRACE_ACTIVE is None:
        _TRACE_ACTIVE = _compute_trace_active(debug_flag)
    return _TRACE_ACTIVE
