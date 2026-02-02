# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from os import environ
from pathlib import Path

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll import create_app
from coati_payroll.log import log
from coati_payroll.config import configuration
from coati_payroll.wsgi_server import serve

# Asegurar que por defecto use un archivo sqlite en la raíz del repositorio
# llamado `coati_payroll.db` si no se suministra `DATABASE_URL`.
repo_root = Path(__file__).resolve().parent
default_db_path = repo_root.joinpath("coati_payroll.db")
default_db_uri = f"sqlite:///{default_db_path}"

# Crear aplicación.
app = create_app(configuration)
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL", None) or default_db_uri
log.trace("app module: application instance created")

# Puerto predefinido.
port = environ.get("PORT", 5000)

if __name__ == "__main__":
    serve(app=app, host="0.0.0.0", port=port)
