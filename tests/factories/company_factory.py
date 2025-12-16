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
"""Factory functions for creating companies."""

from coati_payroll.model import Empresa


def create_company(
    db_session,
    codigo,
    razon_social,
    ruc,
    nombre_comercial=None,
    direccion=None,
    telefono=None,
    correo=None,
    activo=True,
):
    """
    Create a company in the database.

    This is a simple factory function that creates a company with the given
    parameters. No implicit data creation or side effects.

    Args:
        db_session: SQLAlchemy session
        codigo: Unique company code
        razon_social: Legal name
        ruc: Tax identification number
        nombre_comercial: Trade name (optional)
        direccion: Address (optional)
        telefono: Phone number (optional)
        correo: Email (optional)
        activo: Active status (default: True)

    Returns:
        Empresa: Created company instance with ID assigned
    """
    empresa = Empresa()
    empresa.codigo = codigo
    empresa.razon_social = razon_social
    empresa.ruc = ruc
    empresa.nombre_comercial = nombre_comercial
    empresa.direccion = direccion
    empresa.telefono = telefono
    empresa.correo = correo
    empresa.activo = activo

    db_session.add(empresa)
    db_session.commit()
    db_session.refresh(empresa)

    return empresa
