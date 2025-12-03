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

from coati_payroll.enums import TipoUsuario
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    Regexp,
)
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
            (TipoUsuario.ADMIN, _("Administrador")),
            (TipoUsuario.HHRR, _("Recursos Humanos")),
            (TipoUsuario.AUDIT, _("Auditoría")),
        ],
        validators=[DataRequired()],
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class ProfileForm(FlaskForm):
    """Form for editing user profile and password."""

    nombre = StringField(_("Nombre"), validators=[Optional(), Length(max=100)])
    apellido = StringField(_("Apellido"), validators=[Optional(), Length(max=100)])
    correo_electronico = StringField(
        _("Correo electrónico"),
        validators=[Optional(), Email(), Length(max=150)],
    )
    current_password = PasswordField(
        _("Contraseña actual"), validators=[Optional(), Length(min=6)]
    )
    new_password = PasswordField(
        _("Nueva contraseña"), validators=[Optional(), Length(min=6)]
    )
    confirm_password = PasswordField(
        _("Confirmar nueva contraseña"), validators=[Optional(), Length(min=6)]
    )
    submit = SubmitField(_("Actualizar Perfil"))


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

    codigo_empleado = StringField(
        _("Código de empleado"),
        validators=[
            Optional(),
            Length(max=20),
            Regexp(
                r"^[A-Za-z0-9\-]+$",
                message=_("El código solo puede contener letras, números y guiones."),
            ),
        ],
        description=_(
            "Código único del empleado. Si no se proporciona, se genera automáticamente."
        ),
    )
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
    tipo_identificacion = SelectField(
        _("Tipo de identificación"),
        choices=[
            ("", _("Seleccionar...")),
            ("cedula", _("Cédula")),
            ("pasaporte", _("Pasaporte")),
            ("carnet_residente", _("Carnet de residente")),
            ("otro", _("Otro")),
        ],
        validators=[Optional()],
    )
    identificacion_personal = StringField(
        _("Identificación personal"), validators=[DataRequired(), Length(max=50)]
    )
    id_seguridad_social = StringField(
        _("ID Seguridad Social"), validators=[Optional(), Length(max=50)]
    )
    id_fiscal = StringField(_("ID Fiscal"), validators=[Optional(), Length(max=50)])
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
    # Datos iniciales de implementación
    anio_implementacion_inicial = IntegerField(
        _("Año de implementación inicial"),
        validators=[Optional(), NumberRange(min=1900, max=2100)],
        description=_("Año fiscal cuando se implementó el sistema por primera vez"),
    )
    mes_ultimo_cierre = SelectField(
        _("Último mes cerrado"),
        choices=[
            ("", _("Seleccionar...")),
            ("1", _("Enero")),
            ("2", _("Febrero")),
            ("3", _("Marzo")),
            ("4", _("Abril")),
            ("5", _("Mayo")),
            ("6", _("Junio")),
            ("7", _("Julio")),
            ("8", _("Agosto")),
            ("9", _("Septiembre")),
            ("10", _("Octubre")),
            ("11", _("Noviembre")),
            ("12", _("Diciembre")),
        ],
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        description=_("Último mes cerrado antes de pasar al nuevo sistema"),
    )
    salario_acumulado = DecimalField(
        _("Salario acumulado"),
        validators=[Optional()],
        places=2,
        description=_("Suma de salarios del año fiscal antes del sistema"),
    )
    impuesto_acumulado = DecimalField(
        _("Impuesto acumulado"),
        validators=[Optional()],
        places=2,
        description=_("Suma de impuestos pagados en el año fiscal antes del sistema"),
    )
    ultimo_salario_1 = DecimalField(
        _("Penúltimo salario mensual"),
        validators=[Optional()],
        places=2,
        description=_("Salario del mes anterior al último"),
    )
    ultimo_salario_2 = DecimalField(
        _("Antepenúltimo salario mensual"),
        validators=[Optional()],
        places=2,
        description=_("Salario de 2 meses antes del último"),
    )
    ultimo_salario_3 = DecimalField(
        _("Tercer salario anterior"),
        validators=[Optional()],
        places=2,
        description=_("Salario de 3 meses antes del último"),
    )
    submit = SubmitField(_("Guardar"))


class CustomFieldForm(FlaskForm):
    """Form for creating and editing custom employee fields."""

    nombre_campo = StringField(
        _("Nombre del campo"),
        validators=[DataRequired(), Length(max=100)],
        description=_(
            "Nombre interno único del campo (sin espacios ni caracteres especiales)"
        ),
    )
    etiqueta = StringField(
        _("Etiqueta"),
        validators=[DataRequired(), Length(max=150)],
        description=_("Nombre visible del campo en el formulario"),
    )
    tipo_dato = SelectField(
        _("Tipo de dato"),
        choices=[
            ("texto", _("Texto")),
            ("entero", _("Número entero")),
            ("decimal", _("Número decimal")),
            ("booleano", _("Verdadero/Falso")),
        ],
        validators=[DataRequired()],
    )
    descripcion = StringField(
        _("Descripción"), validators=[Optional(), Length(max=255)]
    )
    orden = DecimalField(
        _("Orden de visualización"),
        validators=[Optional()],
        places=0,
        default=0,
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class ReglaCalculoForm(FlaskForm):
    """Form for creating and editing calculation rules."""

    codigo = StringField(
        _("Código"),
        validators=[DataRequired(), Length(max=50)],
        description=_("Código único de la regla (ej: IR_NICARAGUA)"),
    )
    nombre = StringField(
        _("Nombre"),
        validators=[DataRequired(), Length(max=150)],
        description=_("Nombre descriptivo de la regla"),
    )
    descripcion = StringField(
        _("Descripción"),
        validators=[Optional(), Length(max=500)],
    )
    jurisdiccion = StringField(
        _("Jurisdicción"),
        validators=[Optional(), Length(max=100)],
        description=_("País o región donde aplica (ej: Nicaragua)"),
    )
    moneda_referencia = StringField(
        _("Moneda de Referencia"),
        validators=[Optional(), Length(max=10)],
        description=_(
            "Moneda base para cálculos de la regla (ej: NIO). "
            "La moneda de la planilla se define en el Tipo de Planilla."
        ),
    )
    version = StringField(
        _("Versión"),
        validators=[DataRequired(), Length(max=20)],
        default="1.0.0",
        description=_("Versión semántica (ej: 1.0.0)"),
    )
    tipo_regla = SelectField(
        _("Tipo de regla"),
        choices=[
            ("impuesto", _("Impuesto")),
            ("deduccion", _("Deducción")),
            ("percepcion", _("Percepción")),
            ("prestacion", _("Prestación")),
        ],
        validators=[DataRequired()],
    )
    vigente_desde = DateField(
        _("Vigente desde"),
        validators=[DataRequired()],
        description=_("Fecha desde la cual la regla es válida"),
    )
    vigente_hasta = DateField(
        _("Vigente hasta"),
        validators=[Optional()],
        description=_("Fecha hasta la cual la regla es válida (vacío = indefinido)"),
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


# ============================================================================
# PAYROLL CONCEPTS FORMS (Percepciones, Deducciones, Prestaciones)
# ============================================================================


class PercepcionForm(FlaskForm):
    """Form for creating and editing perceptions (income items).

    Percepciones are income items that ADD to employee's pay.
    Only Percepciones and Deducciones affect the employee's net salary.
    """

    codigo = StringField(
        _("Código"),
        validators=[DataRequired(), Length(max=50)],
        description=_("Código único de la percepción (ej: SALARIO_BASE)"),
    )
    nombre = StringField(
        _("Nombre"),
        validators=[DataRequired(), Length(max=150)],
        description=_("Nombre descriptivo de la percepción"),
    )
    descripcion = StringField(
        _("Descripción"),
        validators=[Optional(), Length(max=255)],
    )
    formula_tipo = SelectField(
        _("Tipo de Cálculo"),
        choices=[
            ("fijo", _("Monto Fijo")),
            ("porcentaje_salario", _("Porcentaje del Salario Base")),
            ("porcentaje_bruto", _("Porcentaje del Salario Bruto")),
            ("formula", _("Fórmula Personalizada")),
            ("horas", _("Por Horas")),
            ("dias", _("Por Días")),
        ],
        validators=[DataRequired()],
    )
    monto_default = DecimalField(
        _("Monto Predeterminado"),
        validators=[Optional()],
        description=_("Monto fijo cuando aplica"),
    )
    porcentaje = DecimalField(
        _("Porcentaje"),
        validators=[Optional(), NumberRange(min=0, max=100)],
        description=_("Porcentaje para cálculos (0-100)"),
    )
    base_calculo = SelectField(
        _("Base de Cálculo"),
        choices=[
            ("", _("-- Seleccionar --")),
            ("salario_base", _("Salario Base")),
            ("salario_bruto", _("Salario Bruto")),
            ("salario_gravable", _("Salario Gravable")),
            ("salario_neto", _("Salario Neto")),
        ],
        validators=[Optional()],
    )
    unidad_calculo = SelectField(
        _("Unidad de Cálculo"),
        choices=[
            ("", _("-- Ninguna --")),
            ("hora", _("Por Hora")),
            ("dia", _("Por Día")),
            ("mes", _("Por Mes")),
        ],
        validators=[Optional()],
    )
    gravable = BooleanField(
        _("Gravable"),
        default=True,
        description=_("¿Esta percepción está sujeta a impuestos?"),
    )
    recurrente = BooleanField(
        _("Recurrente"),
        default=False,
        description=_("¿Se aplica automáticamente en cada nómina?"),
    )
    # Vigencia
    vigente_desde = DateField(
        _("Vigente Desde"),
        validators=[Optional()],
        description=_("Fecha desde la cual esta percepción es válida"),
    )
    valido_hasta = DateField(
        _("Válido Hasta"),
        validators=[Optional()],
        description=_(
            "Fecha hasta la cual esta percepción es válida (vacío = indefinido)"
        ),
    )
    # Contabilidad
    contabilizable = BooleanField(
        _("Contabilizable"),
        default=True,
    )
    codigo_cuenta_debe = StringField(
        _("Cuenta Contable (Debe)"),
        validators=[Optional(), Length(max=64)],
    )
    codigo_cuenta_haber = StringField(
        _("Cuenta Contable (Haber)"),
        validators=[Optional(), Length(max=64)],
    )
    editable_en_nomina = BooleanField(
        _("Editable en Nómina"),
        default=False,
        description=_("¿Permitir modificar el monto durante la nómina?"),
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class DeduccionForm(FlaskForm):
    """Form for creating and editing deductions."""

    codigo = StringField(
        _("Código"),
        validators=[DataRequired(), Length(max=50)],
        description=_("Código único de la deducción (ej: INSS_LABORAL)"),
    )
    nombre = StringField(
        _("Nombre"),
        validators=[DataRequired(), Length(max=150)],
        description=_("Nombre descriptivo de la deducción"),
    )
    descripcion = StringField(
        _("Descripción"),
        validators=[Optional(), Length(max=255)],
    )
    tipo = SelectField(
        _("Tipo de Deducción"),
        choices=[
            ("general", _("General")),
            ("impuesto", _("Impuesto")),
            ("seguro_social", _("Seguro Social")),
            ("prestamo", _("Préstamo")),
            ("adelanto", _("Adelanto")),
            ("pension_alimenticia", _("Pensión Alimenticia")),
            ("ahorro", _("Ahorro Voluntario")),
            ("sindical", _("Cuota Sindical")),
            ("otro", _("Otro")),
        ],
        validators=[DataRequired()],
    )
    es_impuesto = BooleanField(
        _("Es Impuesto"),
        default=False,
        description=_("¿Esta deducción es un impuesto (IR, ISR)?"),
    )
    formula_tipo = SelectField(
        _("Tipo de Cálculo"),
        choices=[
            ("fijo", _("Monto Fijo")),
            ("porcentaje_salario", _("Porcentaje del Salario Base")),
            ("porcentaje_bruto", _("Porcentaje del Salario Bruto")),
            ("porcentaje_gravable", _("Porcentaje del Salario Gravable")),
            ("formula", _("Fórmula Personalizada")),
            ("tabla", _("Tabla de Impuestos")),
        ],
        validators=[DataRequired()],
    )
    monto_default = DecimalField(
        _("Monto Predeterminado"),
        validators=[Optional()],
        description=_("Monto fijo cuando aplica"),
    )
    porcentaje = DecimalField(
        _("Porcentaje"),
        validators=[Optional(), NumberRange(min=0, max=100)],
        description=_("Porcentaje para cálculos (0-100)"),
    )
    base_calculo = SelectField(
        _("Base de Cálculo"),
        choices=[
            ("", _("-- Seleccionar --")),
            ("salario_base", _("Salario Base")),
            ("salario_bruto", _("Salario Bruto")),
            ("salario_gravable", _("Salario Gravable")),
            ("salario_neto", _("Salario Neto")),
        ],
        validators=[Optional()],
    )
    unidad_calculo = SelectField(
        _("Unidad de Cálculo"),
        choices=[
            ("", _("-- Ninguna --")),
            ("hora", _("Por Hora")),
            ("dia", _("Por Día")),
            ("mes", _("Por Mes")),
        ],
        validators=[Optional()],
    )
    antes_impuesto = BooleanField(
        _("Antes de Impuesto"),
        default=True,
        description=_("¿Se deduce antes de calcular impuestos?"),
    )
    recurrente = BooleanField(
        _("Recurrente"),
        default=False,
        description=_("¿Se aplica automáticamente en cada nómina?"),
    )
    # Vigencia
    vigente_desde = DateField(
        _("Vigente Desde"),
        validators=[Optional()],
        description=_("Fecha desde la cual esta deducción es válida"),
    )
    valido_hasta = DateField(
        _("Válido Hasta"),
        validators=[Optional()],
        description=_(
            "Fecha hasta la cual esta deducción es válida (vacío = indefinido)"
        ),
    )
    # Contabilidad
    contabilizable = BooleanField(
        _("Contabilizable"),
        default=True,
    )
    codigo_cuenta_debe = StringField(
        _("Cuenta Contable (Debe)"),
        validators=[Optional(), Length(max=64)],
    )
    codigo_cuenta_haber = StringField(
        _("Cuenta Contable (Haber)"),
        validators=[Optional(), Length(max=64)],
    )
    editable_en_nomina = BooleanField(
        _("Editable en Nómina"),
        default=False,
        description=_("¿Permitir modificar el monto durante la nómina?"),
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class PlanillaForm(FlaskForm):
    """Form for creating and editing payroll master records (Planilla).

    A Planilla is the central hub that connects employees, perceptions,
    deductions, benefits, and calculation rules.
    """

    nombre = StringField(
        _("Nombre"),
        validators=[DataRequired(), Length(max=150)],
        description=_("Nombre único de la planilla (ej: Planilla Quincenal Córdobas)"),
    )
    descripcion = StringField(
        _("Descripción"),
        validators=[Optional(), Length(max=255)],
    )
    tipo_planilla_id = SelectField(
        _("Tipo de Planilla"),
        validators=[DataRequired()],
        coerce=str,
        description=_("Define periodicidad, período fiscal y configuración de cálculo"),
    )
    moneda_id = SelectField(
        _("Moneda"),
        validators=[DataRequired()],
        coerce=str,
        description=_("Moneda en la que se pagarán los salarios"),
    )
    periodo_fiscal_inicio = DateField(
        _("Inicio Período Fiscal"),
        validators=[Optional()],
        description=_("Fecha de inicio del período fiscal actual"),
    )
    periodo_fiscal_fin = DateField(
        _("Fin Período Fiscal"),
        validators=[Optional()],
        description=_("Fecha de fin del período fiscal actual"),
    )
    # Automatic deduction priorities
    prioridad_prestamos = IntegerField(
        _("Prioridad Préstamos"),
        validators=[Optional(), NumberRange(min=1, max=999)],
        default=250,
        description=_("Prioridad para deducir cuotas de préstamos (menor = primero)"),
    )
    prioridad_adelantos = IntegerField(
        _("Prioridad Adelantos"),
        validators=[Optional(), NumberRange(min=1, max=999)],
        default=251,
        description=_("Prioridad para deducir adelantos salariales (menor = primero)"),
    )
    aplicar_prestamos_automatico = BooleanField(
        _("Aplicar Préstamos Automáticamente"),
        default=True,
        description=_("¿Deducir automáticamente las cuotas de préstamos?"),
    )
    aplicar_adelantos_automatico = BooleanField(
        _("Aplicar Adelantos Automáticamente"),
        default=True,
        description=_("¿Deducir automáticamente los adelantos salariales?"),
    )
    # Accounting fields for base salary
    codigo_cuenta_debe_salario = StringField(
        _("Cuenta Débito (Salario Base)"),
        validators=[Optional(), Length(max=64)],
        description=_("Cuenta de débito para contabilizar el salario base (gasto)"),
    )
    codigo_cuenta_haber_salario = StringField(
        _("Cuenta Crédito (Salario Base)"),
        validators=[Optional(), Length(max=64)],
        description=_("Cuenta de crédito para contabilizar el salario base (pasivo)"),
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class TipoPlanillaForm(FlaskForm):
    """Form for creating and editing payroll types (TipoPlanilla).

    Defines the type of payroll (monthly, biweekly, weekly, etc.) and its
    fiscal period parameters.
    """

    codigo = StringField(
        _("Código"),
        validators=[DataRequired(), Length(max=20)],
        description=_("Código único del tipo de planilla (ej: MENSUAL)"),
    )
    descripcion = StringField(
        _("Descripción"),
        validators=[Optional(), Length(max=150)],
        description=_("Descripción del tipo de planilla"),
    )
    periodicidad = SelectField(
        _("Periodicidad"),
        choices=[
            ("mensual", _("Mensual")),
            ("quincenal", _("Quincenal")),
            ("semanal", _("Semanal")),
        ],
        validators=[DataRequired()],
        description=_("Frecuencia de pago de la planilla"),
    )
    dias = IntegerField(
        _("Días"),
        validators=[DataRequired(), NumberRange(min=1, max=365)],
        default=30,
        description=_("Número de días usados para prorrateos"),
    )
    mes_inicio_fiscal = SelectField(
        _("Mes Inicio Fiscal"),
        choices=[
            ("1", _("Enero")),
            ("2", _("Febrero")),
            ("3", _("Marzo")),
            ("4", _("Abril")),
            ("5", _("Mayo")),
            ("6", _("Junio")),
            ("7", _("Julio")),
            ("8", _("Agosto")),
            ("9", _("Septiembre")),
            ("10", _("Octubre")),
            ("11", _("Noviembre")),
            ("12", _("Diciembre")),
        ],
        validators=[DataRequired()],
        coerce=int,
        default=1,
        description=_("Mes en que inicia el año fiscal"),
    )
    dia_inicio_fiscal = IntegerField(
        _("Día Inicio Fiscal"),
        validators=[DataRequired(), NumberRange(min=1, max=31)],
        default=1,
        description=_("Día del mes en que inicia el año fiscal"),
    )
    acumula_anual = BooleanField(
        _("Acumula Anual"),
        default=True,
        description=_("¿Los valores se acumulan anualmente?"),
    )
    periodos_por_anio = IntegerField(
        _("Períodos por Año"),
        validators=[DataRequired(), NumberRange(min=1, max=365)],
        default=12,
        description=_("Número de períodos de nómina por año fiscal"),
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class PrestacionForm(FlaskForm):
    """Form for creating and editing benefits (employer contributions).

    Prestaciones are employer costs that do NOT affect the employee's net pay.
    Examples: INSS patronal, vacation provisions, aguinaldo provisions.
    """

    codigo = StringField(
        _("Código"),
        validators=[DataRequired(), Length(max=50)],
        description=_("Código único de la prestación (ej: INSS_PATRONAL)"),
    )
    nombre = StringField(
        _("Nombre"),
        validators=[DataRequired(), Length(max=150)],
        description=_("Nombre descriptivo de la prestación"),
    )
    descripcion = StringField(
        _("Descripción"),
        validators=[Optional(), Length(max=255)],
    )
    tipo = SelectField(
        _("Tipo de Prestación"),
        choices=[
            ("patronal", _("Aporte Patronal")),
            ("seguro_social", _("Seguro Social Patronal")),
            ("vacaciones", _("Vacaciones")),
            ("aguinaldo", _("Aguinaldo / Treceavo Mes")),
            ("indemnizacion", _("Indemnización")),
            ("capacitacion", _("Capacitación")),
            ("otro", _("Otro")),
        ],
        validators=[DataRequired()],
    )
    formula_tipo = SelectField(
        _("Tipo de Cálculo"),
        choices=[
            ("fijo", _("Monto Fijo")),
            ("porcentaje_salario", _("Porcentaje del Salario Base")),
            ("porcentaje_bruto", _("Porcentaje del Salario Bruto")),
            ("formula", _("Fórmula Personalizada")),
            ("provision", _("Provisión Mensual")),
        ],
        validators=[DataRequired()],
    )
    monto_default = DecimalField(
        _("Monto Predeterminado"),
        validators=[Optional()],
        description=_("Monto fijo cuando aplica"),
    )
    porcentaje = DecimalField(
        _("Porcentaje"),
        validators=[Optional(), NumberRange(min=0, max=100)],
        description=_("Porcentaje para cálculos (0-100)"),
    )
    base_calculo = SelectField(
        _("Base de Cálculo"),
        choices=[
            ("", _("-- Seleccionar --")),
            ("salario_base", _("Salario Base")),
            ("salario_bruto", _("Salario Bruto")),
            ("salario_gravable", _("Salario Gravable")),
        ],
        validators=[Optional()],
    )
    unidad_calculo = SelectField(
        _("Unidad de Cálculo"),
        choices=[
            ("", _("-- Ninguna --")),
            ("hora", _("Por Hora")),
            ("dia", _("Por Día")),
            ("mes", _("Por Mes")),
        ],
        validators=[Optional()],
    )
    tope_aplicacion = DecimalField(
        _("Tope de Aplicación"),
        validators=[Optional()],
        description=_(
            "Monto máximo sobre el cual se aplica el cálculo (ej: techo salarial INSS)"
        ),
    )
    recurrente = BooleanField(
        _("Recurrente"),
        default=True,
        description=_("¿Se provisiona automáticamente en cada nómina?"),
    )
    # Vigencia
    vigente_desde = DateField(
        _("Vigente Desde"),
        validators=[Optional()],
        description=_("Fecha desde la cual esta prestación es válida"),
    )
    valido_hasta = DateField(
        _("Válido Hasta"),
        validators=[Optional()],
        description=_(
            "Fecha hasta la cual esta prestación es válida (vacío = indefinido)"
        ),
    )
    # Contabilidad
    contabilizable = BooleanField(
        _("Contabilizable"),
        default=True,
    )
    codigo_cuenta_debe = StringField(
        _("Cuenta Contable (Debe)"),
        validators=[Optional(), Length(max=64)],
    )
    codigo_cuenta_haber = StringField(
        _("Cuenta Contable (Haber)"),
        validators=[Optional(), Length(max=64)],
    )
    editable_en_nomina = BooleanField(
        _("Editable en Nómina"),
        default=False,
        description=_("¿Permitir modificar el monto durante la nómina?"),
    )
    activo = BooleanField(_("Activo"), default=True)
    submit = SubmitField(_("Guardar"))


class NominaNovedadForm(FlaskForm):
    """Form for adding novelties (novedades) to a nomina.

    Novedades are adjustments or events that affect an employee's payroll
    for a specific period. They can be associated with:
    - Percepciones (income items like bonuses, overtime)
    - Deducciones (deductions like absences, loans)

    The novedad is linked to a specific employee and a concept (percepcion or deduccion).
    """

    empleado_id = SelectField(
        _("Empleado"),
        validators=[DataRequired()],
        coerce=str,
        description=_("Empleado al que se aplicará la novedad"),
    )
    tipo_concepto = SelectField(
        _("Tipo de Concepto"),
        choices=[
            ("percepcion", _("Percepción (Ingreso)")),
            ("deduccion", _("Deducción (Egreso)")),
        ],
        validators=[DataRequired()],
        description=_("Tipo de concepto al que se asocia la novedad"),
    )
    percepcion_id = SelectField(
        _("Percepción"),
        validators=[Optional()],
        coerce=str,
        description=_("Percepción a la que se asocia la novedad (si aplica)"),
    )
    deduccion_id = SelectField(
        _("Deducción"),
        validators=[Optional()],
        coerce=str,
        description=_("Deducción a la que se asocia la novedad (si aplica)"),
    )
    codigo_concepto = StringField(
        _("Código del Concepto"),
        validators=[DataRequired(), Length(max=50)],
        description=_("Código del concepto que se modifica o aplica"),
    )
    tipo_valor = SelectField(
        _("Tipo de Valor"),
        choices=[
            ("monto", _("Monto Fijo")),
            ("horas", _("Horas")),
            ("dias", _("Días")),
            ("cantidad", _("Cantidad")),
            ("porcentaje", _("Porcentaje")),
        ],
        validators=[DataRequired()],
        description=_("Tipo de valor de la novedad"),
    )
    valor_cantidad = DecimalField(
        _("Valor / Cantidad"),
        validators=[DataRequired()],
        places=2,
        description=_("Valor numérico de la novedad (ej: 5 horas, 1500 de bono)"),
    )
    fecha_novedad = DateField(
        _("Fecha de la Novedad"),
        validators=[Optional()],
        description=_("Fecha en que ocurrió el evento (opcional, para auditoría)"),
    )
    submit = SubmitField(_("Guardar"))
