# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
# Copyright 2025 - 2026 BMO Soluciones, S.A.
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
"""Factory functions for creating users."""

from coati_payroll.auth import proteger_passwd
from coati_payroll.model import Usuario


def create_user(
    db_session, usuario, password, nombre="Test", apellido="User", correo_electronico=None, tipo="user", activo=True
):
    """
    Create a user in the database.

    This is a simple factory function that creates a user with the given
    parameters. No implicit data creation or side effects.

    Args:
        db_session: SQLAlchemy session
        usuario: Username (unique identifier)
        password: Plain text password (will be hashed)
        nombre: First name (default: "Test")
        apellido: Last name (default: "User")
        correo_electronico: Email address (optional)
        tipo: User type (default: "user")
        activo: Active status (default: True)

    Returns:
        Usuario: Created user instance with ID assigned
    """
    user = Usuario()
    user.usuario = usuario
    user.acceso = proteger_passwd(password)
    user.nombre = nombre
    user.apellido = apellido
    user.correo_electronico = correo_electronico
    user.tipo = tipo
    user.activo = activo

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user
