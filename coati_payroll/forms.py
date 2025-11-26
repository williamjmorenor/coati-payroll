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

"""Forms module.

Contiene los formularios WTForms usados por la aplicación.
"""

from __future__ import annotations

# Terceros
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, Optional
from coati_payroll.i18n import _


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión.

    Campos:
    - email: correo o nombre de usuario identificador del usuario
    - password: contraseña
    """

    # Permitimos que el usuario use su nombre de usuario o su correo electrónico
    # para iniciar sesión, por eso no forzamos el validador Email.
    email = StringField(
        _("Usuario o correo electrónico"), validators=[DataRequired(), Length(max=150)]
    )
    password = PasswordField(
        _("Contraseña"), validators=[DataRequired(), Length(min=6)]
    )
    submit = SubmitField(_("Entrar"))


# --------------------------------------------------------------------------------------
# CRUD Forms
# --------------------------------------------------------------------------------------


class UserForm(FlaskForm):
    """Form for creating and editing users."""

    usuario = StringField(_("Usuario"), validators=[DataRequired(), Length(max=150)])
    password = PasswordField(_("Contraseña"), validators=[Length(min=6)])
    nombre = StringField(_("Nombre"), validators=[Optional(), Length(max=100)])
    apellido = StringField(_("Apellido"), validators=[Optional(), Length(max=100)])
    correo_electronico = StringField(
        _("Correo electrónico"),
        validators=[Optional(), Email(), Length(max=150)],
    )
    tipo = SelectField(
        _("Tipo de usuario"),
        choices=[
            ("admin", _("Administrador")),
            ("hhrr", _("Recursos Humanos")),
            ("audit", _("Auditoría")),
        ],
        validators=[DataRequired()],
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class CurrencyForm(FlaskForm):
    """Form for creating and editing currencies."""

    codigo = StringField(_("Código"), validators=[DataRequired(), Length(max=10)])
    nombre = StringField(_("Nombre"), validators=[DataRequired(), Length(max=100)])
    simbolo = StringField(_("Símbolo"), validators=[Optional(), Length(max=10)])
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class ExchangeRateForm(FlaskForm):
    """Form for creating and editing exchange rates."""

    fecha = DateField(_("Fecha"), validators=[DataRequired()])
    moneda_origen_id = SelectField(
        _("Moneda origen"), validators=[DataRequired()], coerce=str
    )
    moneda_destino_id = SelectField(
        _("Moneda destino"), validators=[DataRequired()], coerce=str
    )
    tasa = DecimalField(_("Tasa de cambio"), validators=[DataRequired()], places=10)
    submit = SubmitField(_("Guardar"))


class EmployeeForm(FlaskForm):
    """Form for creating and editing employees."""

    primer_nombre = StringField(
        _("Primer nombre"), validators=[DataRequired(), Length(max=100)]
    )
    segundo_nombre = StringField(
        _("Segundo nombre"), validators=[Optional(), Length(max=100)]
    )
    primer_apellido = StringField(
        _("Primer apellido"), validators=[DataRequired(), Length(max=100)]
    )
    segundo_apellido = StringField(
        _("Segundo apellido"), validators=[Optional(), Length(max=100)]
    )
    genero = SelectField(
        _("Género"),
        choices=[
            ("", _("Seleccionar...")),
            ("masculino", _("Masculino")),
            ("femenino", _("Femenino")),
            ("otro", _("Otro")),
        ],
        validators=[Optional()],
    )
    nacionalidad = StringField(
        _("Nacionalidad"), validators=[Optional(), Length(max=100)]
    )
    identificacion_personal = StringField(
        _("Identificación personal"), validators=[DataRequired(), Length(max=50)]
    )
    tipo_sangre = SelectField(
        _("Tipo de sangre"),
        choices=[
            ("", _("Seleccionar...")),
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
            ("O+", "O+"),
            ("O-", "O-"),
        ],
        validators=[Optional()],
    )
    fecha_nacimiento = DateField(_("Fecha de nacimiento"), validators=[Optional()])
    fecha_alta = DateField(_("Fecha de alta"), validators=[DataRequired()])
    fecha_baja = DateField(_("Fecha de baja"), validators=[Optional()])
    activo = BooleanField(_("Activo"), default=True)
    cargo = StringField(_("Cargo"), validators=[Optional(), Length(max=150)])
    area = StringField(_("Área"), validators=[Optional(), Length(max=150)])
    centro_costos = StringField(
        _("Centro de costos"), validators=[Optional(), Length(max=150)]
    )
    salario_base = DecimalField(
        _("Salario base"), validators=[DataRequired()], places=2
    )
    moneda_id = SelectField(_("Moneda"), validators=[Optional()], coerce=str)
    correo = StringField(
        _("Correo electrónico"), validators=[Optional(), Email(), Length(max=150)]
    )
    telefono = StringField(_("Teléfono"), validators=[Optional(), Length(max=50)])
    direccion = StringField(_("Dirección"), validators=[Optional(), Length(max=255)])
    estado_civil = SelectField(
        _("Estado civil"),
        choices=[
            ("", _("Seleccionar...")),
            ("soltero", _("Soltero/a")),
            ("casado", _("Casado/a")),
            ("divorciado", _("Divorciado/a")),
            ("viudo", _("Viudo/a")),
            ("union_libre", _("Unión libre")),
        ],
        validators=[Optional()],
    )
    banco = StringField(_("Banco"), validators=[Optional(), Length(max=100)])
    numero_cuenta_bancaria = StringField(
        _("Número de cuenta bancaria"), validators=[Optional(), Length(max=100)]
    )
    tipo_contrato = SelectField(
        _("Tipo de contrato"),
        choices=[
            ("", _("Seleccionar...")),
            ("indefinido", _("Indefinido")),
            ("temporal", _("Temporal")),
            ("por_obra", _("Por obra")),
            ("practicas", _("Prácticas")),
        ],
        validators=[Optional()],
    )
    submit = SubmitField(_("Guardar"))
