# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from typing import TYPE_CHECKING, Optional

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from waitress import serve as wsgi_server

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll import ensure_database_initialized
from coati_payroll.log import log

if TYPE_CHECKING:
    from flask import Flask


# Servidor predefinido.
def serve(app: Optional[Flask] = None, host: str = "0.0.0.0", port: int | str = 5000):

    try:
        log.trace(f"Flask SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        ensure_database_initialized(app)
        log.trace("Database initialized")
    except Exception as exc:
        log.trace(f"Database init raised: {exc}")

    log.trace("Starting waitress on 0.0.0.0:{port}")
    wsgi_server(app, host=host, port=port)
