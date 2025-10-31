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
"""Data model for the payroll module."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from datetime import date, datetime, timezone

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from ulid import ULID

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
database = db


def generador_de_codigos_unicos() -> str:
    """Genera codigo unicos basados en ULID."""

    codigo_aleatorio = ULID()
    id_unico = str(codigo_aleatorio)

    return id_unico


def utc_now() -> datetime:
    """Generate timezone-aware UTC datetime.

    Replacement for deprecated datetime.utcnow() with timezone-aware alternative.
    """
    return datetime.now(timezone.utc)


class BaseTabla:
    """Columnas estandar para todas las tablas de la base de datos."""

    # Pistas de auditoria comunes a todas las tablas.
    id = database.Column(
        database.String(26),
        primary_key=True,
        nullable=False,
        index=True,
        default=generador_de_codigos_unicos,
    )
    timestamp = database.Column(database.DateTime,
                                default=utc_now,
                                nullable=False)
    creado = database.Column(database.Date, default=date.today, nullable=False)
    creado_por = database.Column(database.String(150), nullable=True)
    modificado = database.Column(database.DateTime,
                                 onupdate=utc_now,
                                 nullable=True)
    modificado_por = database.Column(database.String(150), nullable=True)


class Usuario(UserMixin, database.Model, BaseTabla):
    """Una entidad con acceso al sistema."""

    # Información Básica
    __table_args__ = (database.UniqueConstraint("usuario",
                                                name="id_usuario_unico"), )
    __table_args__ = (database.UniqueConstraint("correo_electronico",
                                                name="correo_usuario_unico"), )
    # Info de sistema
    usuario = database.Column(database.String(150),
                              nullable=False,
                              index=True,
                              unique=True)
    acceso = database.Column(database.LargeBinary(), nullable=False)
    nombre = database.Column(database.String(100))
    apellido = database.Column(database.String(100))
    correo_electronico = database.Column(database.String(150))
    correo_electronico_verificado = database.Column(database.Boolean(),
                                                    default=False)
    tipo = database.Column(
        database.String(20))  # Puede ser: admin, user, instructor, moderator
    activo = database.Column(database.Boolean())
