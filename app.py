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

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from os import environ
from pathlib import Path

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from waitress import serve as wsgi_server

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll import create_app, ensure_database_initialized
from coati_payroll.log import log
from coati_payroll.config import configuration

# Asegurar que por defecto use un archivo sqlite en la raíz del repositorio
# llamado `coati_payroll.db` si no se suministra `DATABASE_URL`.
repo_root = Path(__file__).resolve().parent
default_db_path = repo_root.joinpath("coati_payroll.db")
default_db_uri = f"sqlite:///{default_db_path}"

# Only set the default database URL if DATABASE_URL is not already provided.
# This allows Docker containers and production environments to provide their
# own database URL via environment variables.
if not environ.get("DATABASE_URL"):
    environ["DATABASE_URL"] = default_db_uri

# Crear aplicación.
app = create_app(configuration)
log.trace("app module: application instance created")

# Puerto predefinido.
port = environ.get("PORT", 5000)


# Servidor predefinido.
def serve():

    # Asegura que la base de datos esté inicializada y exista un administrador.
    try:
        log.trace(
            f"Flask SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}"
        )
        ensure_database_initialized(app)
        log.trace("Database initialized")
    except Exception as exc:
        log.trace(f"Database init raised: {exc}")

    log.trace("Starting waitress on 0.0.0.0:{port}")
    wsgi_server(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    serve()
