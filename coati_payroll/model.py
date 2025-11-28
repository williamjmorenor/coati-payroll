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
from decimal import Decimal
from datetime import date, datetime, timezone

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableDict
from ulid import ULID

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #

db = SQLAlchemy()
database = db


# Funciones de ayuda
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


# Clase base para todas las tablas
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
    timestamp = database.Column(database.DateTime, default=utc_now, nullable=False)
    creado = database.Column(database.Date, default=date.today, nullable=False)
    creado_por = database.Column(database.String(150), nullable=True)
    modificado = database.Column(database.DateTime, onupdate=utc_now, nullable=True)
    modificado_por = database.Column(database.String(150), nullable=True)


# Gestión de usuarios con acceso a la aplicación
class Usuario(database.Model, BaseTabla, UserMixin):
    __tablename__ = "usuario"
    __table_args__ = (
        database.UniqueConstraint("usuario", name="id_usuario_unico"),
        database.UniqueConstraint("correo_electronico", name="correo_usuario_unico"),
    )

    usuario = database.Column(
        database.String(150), nullable=False, index=True, unique=True
    )
    acceso = database.Column(database.LargeBinary(), nullable=False)
    nombre = database.Column(database.String(100))
    apellido = database.Column(database.String(100))
    correo_electronico = database.Column(database.String(150))
    tipo = database.Column(database.String(20))
    activo = database.Column(database.Boolean(), default=True)


# Gestión de monedas y tipos de cambio
class Moneda(database.Model, BaseTabla):
    __tablename__ = "moneda"

    codigo = database.Column(
        database.String(10), unique=True, nullable=False, index=True
    )
    nombre = database.Column(database.String(100), nullable=False)
    simbolo = database.Column(database.String(10), nullable=True)
    activo = database.Column(database.Boolean(), default=True)

    # relaciones
    planillas = database.relationship("Planilla", back_populates="moneda")
    empleados = database.relationship("Empleado", back_populates="moneda")
    tipo_cambio_origen = database.relationship(
        "TipoCambio",
        back_populates="moneda_origen",
        foreign_keys="TipoCambio.moneda_origen_id",
    )
    tipo_cambio_destino = database.relationship(
        "TipoCambio",
        back_populates="moneda_destino",
        foreign_keys="TipoCambio.moneda_destino_id",
    )


class TipoCambio(database.Model, BaseTabla):
    __tablename__ = "tipo_cambio"
    __table_args__ = (
        database.UniqueConstraint(
            "moneda_origen_id",
            "moneda_destino_id",
            "fecha",
            name="uq_tc_origen_destino_fecha",
        ),
    )

    fecha = database.Column(
        database.Date, nullable=False, default=date.today, index=True
    )
    moneda_origen_id = database.Column(
        database.String(26), database.ForeignKey("moneda.id"), nullable=False
    )
    moneda_destino_id = database.Column(
        database.String(26), database.ForeignKey("moneda.id"), nullable=False
    )
    tasa = database.Column(database.Numeric(24, 10), nullable=False)

    moneda_origen = database.relationship(
        "Moneda", back_populates="tipo_cambio_origen", foreign_keys=[moneda_origen_id]
    )
    moneda_destino = database.relationship(
        "Moneda", back_populates="tipo_cambio_destino", foreign_keys=[moneda_destino_id]
    )


# Registro maestro de empleados
class Empleado(database.Model, BaseTabla):
    __tablename__ = "empleado"
    __table_args__ = (
        database.UniqueConstraint(
            "identificacion_personal", name="uq_empleado_identificacion"
        ),
    )

    primer_nombre = database.Column(database.String(100), nullable=False)
    segundo_nombre = database.Column(database.String(100), nullable=True)
    primer_apellido = database.Column(database.String(100), nullable=False)
    segundo_apellido = database.Column(database.String(100), nullable=True)

    genero = database.Column(database.String(20), nullable=True)
    nacionalidad = database.Column(database.String(100), nullable=True)
    tipo_identificacion = database.Column(database.String(50), nullable=True)
    identificacion_personal = database.Column(
        database.String(50), unique=True, nullable=False
    )
    id_seguridad_social = database.Column(database.String(50), nullable=True)
    id_fiscal = database.Column(database.String(50), nullable=True)
    tipo_sangre = database.Column(database.String(10), nullable=True)
    fecha_nacimiento = database.Column(database.Date, nullable=True)

    fecha_alta = database.Column(database.Date, nullable=False, default=date.today)
    fecha_baja = database.Column(database.Date, nullable=True)
    activo = database.Column(database.Boolean(), default=True, nullable=False)

    cargo = database.Column(database.String(150), nullable=True)
    area = database.Column(database.String(150), nullable=True)
    centro_costos = database.Column(database.String(150), nullable=True)

    salario_base = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    # Moneda del sueldo: FK hacia moneda.id (consistencia)
    moneda_id = database.Column(
        database.String(26), database.ForeignKey("moneda.id"), nullable=True
    )
    moneda = database.relationship("Moneda", back_populates="empleados")

    correo = database.Column(database.String(150), nullable=True, index=True)
    telefono = database.Column(database.String(50), nullable=True)
    direccion = database.Column(database.String(255), nullable=True)
    estado_civil = database.Column(database.String(50), nullable=True)
    banco = database.Column(database.String(100), nullable=True)
    numero_cuenta_bancaria = database.Column(database.String(100), nullable=True)

    tipo_contrato = database.Column(database.String(50), nullable=True)
    fecha_ultimo_aumento = database.Column(database.Date, nullable=True)

    # Datos iniciales de implementación
    # Estos campos almacenan saldos acumulados cuando el sistema se implementa
    # a mitad de un período fiscal
    anio_implementacion_inicial = database.Column(database.Integer, nullable=True)
    mes_ultimo_cierre = database.Column(database.Integer, nullable=True)
    salario_acumulado = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    impuesto_acumulado = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    ultimos_tres_salarios = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )

    # relaciones
    planilla_asociaciones = database.relationship(
        "PlanillaEmpleado",
        back_populates="empleado",
    )
    nominas = database.relationship(
        "NominaEmpleado",
        back_populates="empleado",
    )
    novedades_registradas = database.relationship(
        "NominaNovedad", back_populates="empleado", cascade="all,delete-orphan"
    )
    historial_salarios = database.relationship(
        "HistorialSalario", back_populates="empleado", cascade="all,delete-orphan"
    )
    vacaciones = database.relationship(
        "VacacionEmpleado", back_populates="empleado", cascade="all,delete-orphan"
    )
    vacaciones_descansadas = database.relationship(
        "VacacionDescansada", back_populates="empleado", cascade="all,delete-orphan"
    )
    adelantos = database.relationship(
        "Adelanto", back_populates="empleado", cascade="all,delete-orphan"
    )

    # Datos adicionales (JSON)
    datos_adicionales = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )


# Gestión de planillas
class TipoPlanilla(database.Model, BaseTabla):
    """Payroll type configuration.

    Defines the type of payroll (monthly, biweekly, weekly, etc.) and its
    fiscal period parameters. The fiscal period can be different from the
    calendar year (Jan-Dec) and is defined here to support various accounting
    requirements.
    """

    __tablename__ = "tipo_planilla"

    codigo = database.Column(database.String(20), unique=True, nullable=False)
    descripcion = database.Column(database.String(150), nullable=True)
    dias = database.Column(
        database.Integer, nullable=False, default=30
    )  # días usados para prorrateos
    periodicidad = database.Column(
        database.String(20), nullable=False, default="mensual"
    )  # ej. mensual, quincenal, semanal

    # Fiscal period configuration
    # mes_inicio_fiscal: Month when the fiscal year starts (1-12)
    mes_inicio_fiscal = database.Column(
        database.Integer, nullable=False, default=1
    )  # 1 = January
    # dia_inicio_fiscal: Day of month when fiscal year starts
    dia_inicio_fiscal = database.Column(database.Integer, nullable=False, default=1)

    # Accumulated calculation settings
    # acumula_anual: Whether this payroll type accumulates values annually
    acumula_anual = database.Column(database.Boolean(), default=True, nullable=False)
    # periodos_por_anio: Number of payroll periods per fiscal year
    periodos_por_anio = database.Column(database.Integer, nullable=False, default=12)

    # Tax calculation parameters (stored as JSON for flexibility)
    parametros_calculo = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )

    activo = database.Column(database.Boolean(), default=True, nullable=False)

    planillas = database.relationship("Planilla", back_populates="tipo_planilla")
    acumulados = database.relationship("AcumuladoAnual", back_populates="tipo_planilla")


class Planilla(database.Model, BaseTabla):
    """Master payroll record that connects employees, perceptions, deductions, and benefits.

    The Planilla acts as the central hub for payroll configuration:
    - Employees assigned via PlanillaEmpleado
    - Perceptions via PlanillaIngreso
    - Deductions via PlanillaDeduccion (with priority order)
    - Benefits via PlanillaPrestacion
    - Calculation rules via PlanillaReglaCalculo

    Automatic Deductions:
    The payroll engine automatically applies loan installments and salary advances
    from the Adelanto table for employees with active loans, regardless of whether
    those deductions are explicitly configured in planilla_deducciones.
    The priority for these automatic deductions is controlled by:
    - prioridad_prestamos: Priority for loan installments
    - prioridad_adelantos: Priority for salary advances
    """

    __tablename__ = "planilla"

    nombre = database.Column(database.String(150), nullable=False, unique=True)
    descripcion = database.Column(database.String(255), nullable=True)
    activo = database.Column(database.Boolean(), default=True, nullable=False)

    parametros = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )

    tipo_planilla_id = database.Column(
        database.String(26), database.ForeignKey("tipo_planilla.id"), nullable=False
    )
    tipo_planilla = database.relationship("TipoPlanilla", back_populates="planillas")

    moneda_id = database.Column(
        database.String(26), database.ForeignKey("moneda.id"), nullable=False
    )
    moneda = database.relationship("Moneda", back_populates="planillas")

    # Período Fiscal
    periodo_fiscal_inicio = database.Column(database.Date, nullable=True)
    periodo_fiscal_fin = database.Column(database.Date, nullable=True)

    # Ultima ejecución
    ultima_ejecucion = database.Column(database.DateTime, nullable=True)

    # Automatic deduction priorities (applied even if not in planilla_deducciones)
    # Loans and advances from Adelanto table are automatically deducted
    # Lower number = higher priority (applied first)
    prioridad_prestamos = database.Column(
        database.Integer, nullable=False, default=250
    )  # Default: after mandatory deductions
    prioridad_adelantos = database.Column(
        database.Integer, nullable=False, default=251
    )  # Default: right after loans

    # Whether to apply automatic loan/advance deductions
    aplicar_prestamos_automatico = database.Column(
        database.Boolean(), default=True, nullable=False
    )
    aplicar_adelantos_automatico = database.Column(
        database.Boolean(), default=True, nullable=False
    )

    # relaciones con componentes configurados
    planilla_percepciones = database.relationship(
        "PlanillaIngreso",
        back_populates="planilla",
    )
    planilla_deducciones = database.relationship(
        "PlanillaDeduccion",
        back_populates="planilla",
    )
    planilla_prestaciones = database.relationship(
        "PlanillaPrestacion",
        back_populates="planilla",
    )

    # reglas de cálculo asociadas (impuestos, fórmulas complejas)
    planilla_reglas_calculo = database.relationship(
        "PlanillaReglaCalculo",
        back_populates="planilla",
    )

    # empleados asignados a la planilla (config)
    planilla_empleados = database.relationship(
        "PlanillaEmpleado",
        back_populates="planilla",
    )

    # ejecuciones históricas (nominas)
    nominas = database.relationship(
        "Nomina",
        back_populates="planilla",
    )


# Percepciones y deducciones - THESE AFFECT EMPLOYEE'S NET PAY
# Percepciones (ingresos) se SUMAN al salario
# Deducciones se RESTAN del salario
class Percepcion(database.Model, BaseTabla):
    """Income items that ADD to employee's pay.

    Percepciones are income items that increase the employee's gross salary.
    Examples: base salary, overtime, bonuses, commissions, allowances.

    Together with Deducciones, these determine the employee's net pay.
    (Prestaciones do NOT affect employee pay - they are employer costs.)
    """

    __tablename__ = "percepcion"

    codigo = database.Column(
        database.String(50), unique=True, nullable=False, index=True
    )
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(255), nullable=True)
    unidad_calculo = database.Column(
        database.String(20), nullable=True
    )  # ej. 'hora', 'dia', 'mes', etc.

    # tipo de cálculo: 'fijo', 'porcentaje_salario', 'porcentaje_bruto', 'formula', 'horas', etc.
    formula_tipo = database.Column(database.String(50), nullable=False, default="fijo")
    monto_default = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    formula = database.Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)
    condicion = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )
    porcentaje = database.Column(database.Numeric(5, 2), nullable=True)
    gravable = database.Column(database.Boolean(), default=True)
    recurrente = database.Column(database.Boolean(), default=False)
    activo = database.Column(database.Boolean(), default=True)

    # Vigencia: hasta cuándo es válida esta percepción (opcional)
    vigente_desde = database.Column(
        database.Date, nullable=True
    )  # opcional, si quieres rango
    valido_hasta = database.Column(database.Date, nullable=True)

    # Especificidad de cálculo
    base_calculo = database.Column(  # ej: 'salario_base', 'gravable', 'bruto', 'neto'
        database.String(50), nullable=True
    )
    unidad_calculo = database.Column(  # ej: 'horas', 'dias', None
        database.String(20), nullable=True
    )

    # Control contable
    contabilizable = database.Column(database.Boolean(), default=True, nullable=False)
    codigo_cuenta_debe = database.Column(database.String(64), nullable=True)
    codigo_cuenta_haber = database.Column(database.String(64), nullable=True)

    # Control edición en nómina
    editable_en_nomina = database.Column(
        database.Boolean(), default=False, nullable=False
    )

    planillas = database.relationship(
        "PlanillaIngreso",
        back_populates="percepcion",
    )
    nomina_detalles = database.relationship(
        "NominaDetalle", back_populates="percepcion"
    )


class Deduccion(database.Model, BaseTabla):
    __tablename__ = "deduccion"

    codigo = database.Column(
        database.String(50), unique=True, nullable=False, index=True
    )
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(255), nullable=True)

    tipo = database.Column(database.String(30), nullable=False, default="general")
    es_impuesto = database.Column(database.Boolean(), default=False)

    formula_tipo = database.Column(database.String(50), nullable=False, default="fijo")
    monto_default = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    formula = database.Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)
    condicion = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )
    porcentaje = database.Column(database.Numeric(5, 2), nullable=True)
    antes_impuesto = database.Column(database.Boolean(), default=True)
    recurrente = database.Column(database.Boolean(), default=False)
    activo = database.Column(database.Boolean(), default=True)

    # Vigencia
    vigente_desde = database.Column(database.Date, nullable=True)
    valido_hasta = database.Column(database.Date, nullable=True)

    # Base y unidad de cálculo
    base_calculo = database.Column(database.String(50), nullable=True)
    unidad_calculo = database.Column(database.String(20), nullable=True)

    # Control contable
    contabilizable = database.Column(database.Boolean(), default=True, nullable=False)
    codigo_cuenta_debe = database.Column(database.String(64), nullable=True)
    codigo_cuenta_haber = database.Column(database.String(64), nullable=True)

    # Control edición en nómina
    editable_en_nomina = database.Column(
        database.Boolean(), default=False, nullable=False
    )

    planillas = database.relationship(
        "PlanillaDeduccion",
        back_populates="deduccion",
    )
    nomina_detalles = database.relationship("NominaDetalle", back_populates="deduccion")
    tablas_impuesto = database.relationship("TablaImpuesto", back_populates="deduccion")
    adelantos = database.relationship("Adelanto", back_populates="deduccion")


# Prestaciones (aportes del empleador: seguridad social, etc.)
# NOTA: Las prestaciones son costos patronales que NO afectan el pago al empleado.
# Solo las percepciones y deducciones afectan el salario neto del empleado.
# Ejemplos de prestaciones: INSS patronal, provisión de vacaciones, aguinaldo, indemnización.
class Prestacion(database.Model, BaseTabla):
    """Employer contributions and provisions.

    Prestaciones are employer costs that do NOT affect the employee's net pay.
    They represent the company's obligations such as:
    - Social security employer contributions (INSS patronal)
    - Vacation provisions
    - 13th month (aguinaldo) provisions
    - Severance provisions (indemnización)

    Only Percepciones (income) and Deducciones affect the employee's net salary.
    """

    __tablename__ = "prestacion"

    codigo = database.Column(
        database.String(50), unique=True, nullable=False, index=True
    )
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(255), nullable=True)

    tipo = database.Column(database.String(30), nullable=False, default="patronal")

    formula_tipo = database.Column(database.String(50), nullable=False, default="fijo")
    monto_default = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    formula = database.Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)
    condicion = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )
    porcentaje = database.Column(database.Numeric(5, 2), nullable=True)
    recurrente = database.Column(database.Boolean(), default=False)
    activo = database.Column(database.Boolean(), default=True)

    vigente_desde = database.Column(database.Date, nullable=True)
    valido_hasta = database.Column(database.Date, nullable=True)

    base_calculo = database.Column(database.String(50), nullable=True)
    unidad_calculo = database.Column(database.String(20), nullable=True)

    tope_aplicacion = database.Column(database.Numeric(14, 2), nullable=True)

    contabilizable = database.Column(database.Boolean(), default=True, nullable=False)
    codigo_cuenta_debe = database.Column(database.String(64), nullable=True)
    codigo_cuenta_haber = database.Column(database.String(64), nullable=True)

    editable_en_nomina = database.Column(
        database.Boolean(), default=False, nullable=False
    )

    planillas = database.relationship(
        "PlanillaPrestacion",
        back_populates="prestacion",
    )
    nomina_detalles = database.relationship(
        "NominaDetalle", back_populates="prestacion"
    )


# Definición de componentes de planilla
class PlanillaIngreso(database.Model, BaseTabla):
    __tablename__ = "planilla_ingreso"
    __table_args__ = (
        database.UniqueConstraint(
            "planilla_id", "percepcion_id", name="uq_planilla_percepcion"
        ),
    )

    planilla_id = database.Column(
        database.String(26), database.ForeignKey("planilla.id"), nullable=False
    )
    percepcion_id = database.Column(
        database.String(26), database.ForeignKey("percepcion.id"), nullable=False
    )

    orden = database.Column(database.Integer, nullable=True, default=0)
    editable = database.Column(database.Boolean(), default=True)
    monto_predeterminado = database.Column(database.Numeric(14, 2), nullable=True)
    porcentaje = database.Column(database.Numeric(5, 2), nullable=True)
    activo = database.Column(database.Boolean(), default=True)

    planilla = database.relationship("Planilla", back_populates="planilla_percepciones")
    percepcion = database.relationship("Percepcion", back_populates="planillas")


class PlanillaDeduccion(database.Model, BaseTabla):
    """Association between Planilla and Deduccion with priority ordering.

    The 'prioridad' field determines the order in which deductions are applied.
    This is critical when the net salary doesn't cover all deductions.

    Priority guidelines:
    - 1-100: Legal/mandatory deductions (taxes, social security)
    - 101-200: Court-ordered deductions (alimony, garnishments)
    - 201-300: Company loans and salary advances
    - 301-400: Voluntary deductions (savings, insurance)
    - 401+: Other deductions

    Note: Loan installments from the Adelanto table are handled automatically
    by the payroll engine, not through JSON calculation rules.
    """

    __tablename__ = "planilla_deduccion"
    __table_args__ = (
        database.UniqueConstraint(
            "planilla_id", "deduccion_id", name="uq_planilla_deduccion"
        ),
    )

    planilla_id = database.Column(
        database.String(26), database.ForeignKey("planilla.id"), nullable=False
    )
    deduccion_id = database.Column(
        database.String(26), database.ForeignKey("deduccion.id"), nullable=False
    )

    # Priority order for applying deductions (lower = higher priority)
    prioridad = database.Column(database.Integer, nullable=False, default=100)

    # Legacy field kept for backward compatibility, use 'prioridad' instead
    orden = database.Column(database.Integer, nullable=True, default=0)

    editable = database.Column(database.Boolean(), default=True)
    monto_predeterminado = database.Column(database.Numeric(14, 2), nullable=True)
    porcentaje = database.Column(database.Numeric(5, 2), nullable=True)
    activo = database.Column(database.Boolean(), default=True)

    # Whether this deduction is mandatory (cannot be skipped if salary insufficient)
    es_obligatoria = database.Column(database.Boolean(), default=False)

    # Whether to stop processing if salary is insufficient for this deduction
    detener_si_insuficiente = database.Column(database.Boolean(), default=False)

    planilla = database.relationship("Planilla", back_populates="planilla_deducciones")
    deduccion = database.relationship("Deduccion", back_populates="planillas")


class PlanillaPrestacion(database.Model, BaseTabla):
    __tablename__ = "planilla_prestacion"
    __table_args__ = (
        database.UniqueConstraint(
            "planilla_id", "prestacion_id", name="uq_planilla_prestacion"
        ),
    )

    planilla_id = database.Column(
        database.String(26), database.ForeignKey("planilla.id"), nullable=False
    )
    prestacion_id = database.Column(
        database.String(26), database.ForeignKey("prestacion.id"), nullable=False
    )

    orden = database.Column(database.Integer, nullable=True, default=0)
    editable = database.Column(database.Boolean(), default=True)
    monto_predeterminado = database.Column(database.Numeric(14, 2), nullable=True)
    porcentaje = database.Column(database.Numeric(5, 2), nullable=True)
    activo = database.Column(database.Boolean(), default=True)

    planilla = database.relationship("Planilla", back_populates="planilla_prestaciones")
    prestacion = database.relationship("Prestacion", back_populates="planillas")


class PlanillaReglaCalculo(database.Model, BaseTabla):
    """Association between Planilla and ReglaCalculo (calculation rules/tax tables).

    This allows a payroll to have multiple calculation rules associated,
    such as income tax rules, social security rules, etc.
    """

    __tablename__ = "planilla_regla_calculo"
    __table_args__ = (
        database.UniqueConstraint(
            "planilla_id", "regla_calculo_id", name="uq_planilla_regla"
        ),
    )

    planilla_id = database.Column(
        database.String(26), database.ForeignKey("planilla.id"), nullable=False
    )
    regla_calculo_id = database.Column(
        database.String(26), database.ForeignKey("regla_calculo.id"), nullable=False
    )

    # Order of execution (important for dependent calculations)
    orden = database.Column(database.Integer, nullable=False, default=0)

    # Whether this rule is active for this payroll
    activo = database.Column(database.Boolean(), default=True)

    # Optional: override parameters for this specific payroll
    parametros_override = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )

    planilla = database.relationship(
        "Planilla", back_populates="planilla_reglas_calculo"
    )
    regla_calculo = database.relationship("ReglaCalculo", back_populates="planillas")


class PlanillaEmpleado(database.Model, BaseTabla):
    __tablename__ = "planilla_empleado"
    __table_args__ = (
        database.UniqueConstraint(
            "planilla_id", "empleado_id", name="uq_planilla_empleado"
        ),
    )

    planilla_id = database.Column(
        database.String(26), database.ForeignKey("planilla.id"), nullable=False
    )
    empleado_id = database.Column(
        database.String(26), database.ForeignKey("empleado.id"), nullable=False
    )

    activo = database.Column(database.Boolean(), default=True)
    fecha_inicio = database.Column(database.Date, nullable=False, default=date.today)
    fecha_fin = database.Column(
        database.Date, nullable=True
    )  # si deja de estar en la planilla

    planilla = database.relationship("Planilla", back_populates="planilla_empleados")
    empleado = database.relationship("Empleado", back_populates="planilla_asociaciones")


# Nominas (ejecuciones de planillas)
class Nomina(database.Model, BaseTabla):
    __tablename__ = "nomina"

    planilla_id = database.Column(
        database.String(26), database.ForeignKey("planilla.id"), nullable=False
    )
    fecha_generacion = database.Column(
        database.DateTime, nullable=False, default=utc_now
    )
    periodo_inicio = database.Column(database.Date, nullable=False)
    periodo_fin = database.Column(database.Date, nullable=False)
    generado_por = database.Column(database.String(150), nullable=True)
    estado = database.Column(
        database.String(30), nullable=False, default="generado"
    )  # generado, aprobado, aplicado

    total_bruto = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    total_deducciones = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    total_neto = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )

    planilla = database.relationship("Planilla", back_populates="nominas")
    nomina_empleados = database.relationship(
        "NominaEmpleado",
        back_populates="nomina",
    )
    novedades = database.relationship(
        "NominaNovedad",
        back_populates="nomina",
    )


class NominaEmpleado(database.Model, BaseTabla):
    __tablename__ = "nomina_empleado"

    nomina_id = database.Column(
        database.String(26), database.ForeignKey("nomina.id"), nullable=False
    )
    empleado_id = database.Column(
        database.String(26), database.ForeignKey("empleado.id"), nullable=False
    )

    salario_bruto = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    total_ingresos = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    total_deducciones = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    salario_neto = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )

    # datos para auditoria/moneda
    moneda_origen_id = database.Column(
        database.String(26), database.ForeignKey("moneda.id"), nullable=True
    )
    tipo_cambio_aplicado = database.Column(database.Numeric(24, 10), nullable=True)

    nomina = database.relationship("Nomina", back_populates="nomina_empleados")
    empleado = database.relationship("Empleado", back_populates="nominas")

    nomina_detalles = database.relationship(
        "NominaDetalle",
        back_populates="nomina_empleado",
    )

    # Backup de datos del empleado al momento de la generación de la nómina
    cargo_snapshot = database.Column(database.String(150), nullable=True)
    area_snapshot = database.Column(database.String(150), nullable=True)
    centro_costos_snapshot = database.Column(database.String(150), nullable=True)
    sueldo_base_historico = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )


class NominaDetalle(database.Model, BaseTabla):
    __tablename__ = "nomina_detalle"

    nomina_empleado_id = database.Column(
        database.String(26), database.ForeignKey("nomina_empleado.id"), nullable=False
    )
    tipo = database.Column(
        database.String(15), nullable=False
    )  # 'ingreso' | 'deduccion' | 'prestacion'
    codigo = database.Column(database.String(50), nullable=False)
    descripcion = database.Column(database.String(255), nullable=True)
    monto = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    orden = database.Column(database.Integer, nullable=True, default=0)

    # referencias opcionales a catálogo original (si aplica)
    percepcion_id = database.Column(
        database.String(26), database.ForeignKey("percepcion.id"), nullable=True
    )
    deduccion_id = database.Column(
        database.String(26), database.ForeignKey("deduccion.id"), nullable=True
    )
    prestacion_id = database.Column(
        database.String(26), database.ForeignKey("prestacion.id"), nullable=True
    )

    nomina_empleado = database.relationship(
        "NominaEmpleado", back_populates="nomina_detalles"
    )
    percepcion = database.relationship(
        "Percepcion", back_populates="nomina_detalles", foreign_keys=[percepcion_id]
    )
    deduccion = database.relationship(
        "Deduccion", back_populates="nomina_detalles", foreign_keys=[deduccion_id]
    )
    prestacion = database.relationship(
        "Prestacion", back_populates="nomina_detalles", foreign_keys=[prestacion_id]
    )


class NominaNovedad(database.Model, BaseTabla):
    __tablename__ = "nomina_novedad"

    # FK a la ejecución de Nómina (el ID que solicitaste)
    nomina_id = database.Column(
        database.String(26), database.ForeignKey("nomina.id"), nullable=False
    )
    # FK al empleado afectado
    empleado_id = database.Column(
        database.String(26), database.ForeignKey("empleado.id"), nullable=False
    )

    tipo_valor = database.Column(
        database.String(20), nullable=True
    )  # horas | dias | cantidad | monto | porcentaje

    # El código del concepto que se está modificando/aplicando
    codigo_concepto = database.Column(database.String(50), nullable=False)

    # Valor/cantidad de la novedad (ej. 5 horas, 1500 de comisión, 1 día de ausencia)
    valor_cantidad = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    # Fecha de ocurrencia del evento (útil para auditoría y prorrateo)
    fecha_novedad = database.Column(database.Date, nullable=True)

    # Referencia opcional al maestro para saber qué regla aplica
    percepcion_id = database.Column(
        database.String(26), database.ForeignKey("percepcion.id"), nullable=True
    )
    deduccion_id = database.Column(
        database.String(26), database.ForeignKey("deduccion.id"), nullable=True
    )

    nomina = database.relationship("Nomina", back_populates="novedades")
    empleado = database.relationship("Empleado", back_populates="novedades_registradas")


# Historial de cambios de salario
class HistorialSalario(database.Model, BaseTabla):
    __tablename__ = "historial_salario"

    empleado_id = database.Column(
        database.String(26),
        database.ForeignKey("empleado.id"),
        nullable=False,
        index=True,
    )
    fecha_efectiva = database.Column(database.Date, nullable=False, index=True)
    salario_anterior = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    salario_nuevo = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    motivo = database.Column(database.String(255), nullable=True)
    autorizado_por = database.Column(database.String(150), nullable=True)

    empleado = database.relationship("Empleado", back_populates="historial_salarios")


# Configuración de vacaciones por país/empresa
class ConfiguracionVacaciones(database.Model, BaseTabla):
    __tablename__ = "configuracion_vacaciones"

    codigo = database.Column(
        database.String(50), unique=True, nullable=False, index=True
    )
    descripcion = database.Column(database.String(255), nullable=True)
    dias_por_mes = database.Column(
        database.Numeric(5, 2), nullable=False, default=Decimal("2.50")
    )
    dias_minimos_descanso = database.Column(database.Integer, nullable=False, default=1)
    dias_maximos_acumulables = database.Column(database.Integer, nullable=True)
    meses_minimos_para_devengar = database.Column(
        database.Integer, nullable=False, default=1
    )
    activo = database.Column(database.Boolean(), default=True)

    vacaciones_empleados = database.relationship(
        "VacacionEmpleado", back_populates="configuracion"
    )


# Saldo y control de vacaciones por empleado
class VacacionEmpleado(database.Model, BaseTabla):
    __tablename__ = "vacacion_empleado"
    __table_args__ = (
        database.UniqueConstraint(
            "empleado_id", "anio", name="uq_vacacion_empleado_anio"
        ),
    )

    empleado_id = database.Column(
        database.String(26),
        database.ForeignKey("empleado.id"),
        nullable=False,
        index=True,
    )
    configuracion_id = database.Column(
        database.String(26),
        database.ForeignKey("configuracion_vacaciones.id"),
        nullable=False,
    )
    anio = database.Column(database.Integer, nullable=False)
    dias_devengados = database.Column(
        database.Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    dias_tomados = database.Column(
        database.Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    dias_pendientes = database.Column(
        database.Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    dias_pagados = database.Column(
        database.Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    fecha_ultimo_calculo = database.Column(database.Date, nullable=True)

    empleado = database.relationship("Empleado", back_populates="vacaciones")
    configuracion = database.relationship(
        "ConfiguracionVacaciones", back_populates="vacaciones_empleados"
    )


# Registro de vacaciones descansadas
class VacacionDescansada(database.Model, BaseTabla):
    __tablename__ = "vacacion_descansada"

    empleado_id = database.Column(
        database.String(26),
        database.ForeignKey("empleado.id"),
        nullable=False,
        index=True,
    )
    fecha_inicio = database.Column(database.Date, nullable=False)
    fecha_fin = database.Column(database.Date, nullable=False)
    dias_tomados = database.Column(
        database.Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    estado = database.Column(database.String(30), nullable=False, default="pendiente")
    autorizado_por = database.Column(database.String(150), nullable=True)
    fecha_autorizacion = database.Column(database.Date, nullable=True)
    observaciones = database.Column(database.String(500), nullable=True)

    empleado = database.relationship(
        "Empleado", back_populates="vacaciones_descansadas"
    )


# Tabla de impuestos (tramos fiscales)
class TablaImpuesto(database.Model, BaseTabla):
    __tablename__ = "tabla_impuesto"
    __table_args__ = (
        database.UniqueConstraint(
            "deduccion_id",
            "limite_inferior",
            "vigente_desde",
            name="uq_impuesto_tramo_vigencia",
        ),
    )

    deduccion_id = database.Column(
        database.String(26),
        database.ForeignKey("deduccion.id"),
        nullable=False,
        index=True,
    )
    limite_inferior = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    limite_superior = database.Column(database.Numeric(14, 2), nullable=True)
    porcentaje = database.Column(
        database.Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    cuota_fija = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    sobre_excedente_de = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    vigente_desde = database.Column(database.Date, nullable=False)
    vigente_hasta = database.Column(database.Date, nullable=True)
    activo = database.Column(database.Boolean(), default=True)

    deduccion = database.relationship("Deduccion", back_populates="tablas_impuesto")


# Adelantos de salario
class Adelanto(database.Model, BaseTabla):
    __tablename__ = "adelanto"

    empleado_id = database.Column(
        database.String(26),
        database.ForeignKey("empleado.id"),
        nullable=False,
        index=True,
    )
    deduccion_id = database.Column(
        database.String(26), database.ForeignKey("deduccion.id"), nullable=True
    )
    fecha_solicitud = database.Column(database.Date, nullable=False, default=date.today)
    fecha_aprobacion = database.Column(database.Date, nullable=True)
    monto_solicitado = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    monto_aprobado = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    saldo_pendiente = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    cuotas_pactadas = database.Column(database.Integer, nullable=True)
    monto_por_cuota = database.Column(
        database.Numeric(14, 2), nullable=True, default=Decimal("0.00")
    )
    estado = database.Column(database.String(30), nullable=False, default="pendiente")
    motivo = database.Column(database.String(500), nullable=True)
    aprobado_por = database.Column(database.String(150), nullable=True)

    empleado = database.relationship("Empleado", back_populates="adelantos")
    deduccion = database.relationship("Deduccion", back_populates="adelantos")
    abonos = database.relationship(
        "AdelantoAbono", back_populates="adelanto", cascade="all,delete-orphan"
    )


# Control de abonos/pagos a adelantos
class AdelantoAbono(database.Model, BaseTabla):
    __tablename__ = "adelanto_abono"

    adelanto_id = database.Column(
        database.String(26),
        database.ForeignKey("adelanto.id"),
        nullable=False,
        index=True,
    )
    nomina_id = database.Column(
        database.String(26), database.ForeignKey("nomina.id"), nullable=True
    )
    fecha_abono = database.Column(database.Date, nullable=False, default=date.today)
    monto_abonado = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    saldo_anterior = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    saldo_posterior = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    tipo_abono = database.Column(database.String(30), nullable=False, default="nomina")
    observaciones = database.Column(database.String(255), nullable=True)

    adelanto = database.relationship("Adelanto", back_populates="abonos")
    nomina = database.relationship("Nomina")


# Definición de campos personalizados para empleados
class CampoPersonalizado(database.Model, BaseTabla):
    """Custom field definition for employee records.

    Stores the definition of custom fields that can be added to employee records.
    The actual values are stored in the `datos_adicionales` JSON column of Empleado.

    Field types:
    - texto: String/text field
    - entero: Integer field
    - decimal: Decimal/float field
    - booleano: Boolean (true/false) field
    """

    __tablename__ = "campo_personalizado"
    __table_args__ = (
        database.UniqueConstraint("nombre_campo", name="uq_campo_nombre"),
    )

    nombre_campo = database.Column(
        database.String(100), unique=True, nullable=False, index=True
    )
    etiqueta = database.Column(database.String(150), nullable=False)
    tipo_dato = database.Column(
        database.String(20), nullable=False, default="texto"
    )  # texto, entero, decimal, booleano
    descripcion = database.Column(database.String(255), nullable=True)
    orden = database.Column(database.Integer, nullable=False, default=0)
    activo = database.Column(database.Boolean(), default=True, nullable=False)


# Reglas de cálculo (impuestos, percepciones, deducciones complejas)
class ReglaCalculo(database.Model, BaseTabla):
    """Calculation rules for taxes, perceptions, and deductions.

    Stores the complete JSON schema for calculating complex rules like
    income tax (IR), social security deductions, etc. The schema defines
    variables, conditions, formulas, and tax lookup tables.

    This allows country-agnostic configuration of tax rules that can be
    versioned and applied based on effective dates.
    """

    __tablename__ = "regla_calculo"
    __table_args__ = (
        database.UniqueConstraint("codigo", "version", name="uq_regla_codigo_version"),
    )

    codigo = database.Column(
        database.String(50), nullable=False, index=True
    )  # e.g., 'IR_NICARAGUA', 'INSS_LABORAL'
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.Text, nullable=True)
    jurisdiccion = database.Column(
        database.String(100), nullable=True
    )  # e.g., 'Nicaragua', 'Costa Rica'

    # Reference currency for the tax rule calculations.
    # The rule is currency-agnostic - the actual payroll currency is defined
    # in TipoPlanilla. When the payroll currency differs from the reference
    # currency, exchange rates are applied during calculation.
    # Example: IR Nicaragua uses NIO as reference, but payroll can be in USD.
    moneda_referencia = database.Column(
        database.String(10), nullable=True
    )  # e.g., 'NIO', 'USD' - reference currency for rule calculations

    version = database.Column(
        database.String(20), nullable=False, default="1.0.0"
    )  # Semantic versioning

    # Type of rule: 'impuesto', 'deduccion', 'percepcion', 'prestacion'
    tipo_regla = database.Column(
        database.String(30), nullable=False, default="impuesto"
    )

    # The complete JSON schema defining the calculation logic
    # Structure includes: meta, inputs, steps, tax_tables, output
    esquema_json = database.Column(
        MutableDict.as_mutable(JSON), nullable=False, default=dict
    )

    # Validity period
    vigente_desde = database.Column(database.Date, nullable=False)
    vigente_hasta = database.Column(database.Date, nullable=True)

    activo = database.Column(database.Boolean(), default=True, nullable=False)

    # Optional relationship to specific deduction/perception/benefit
    deduccion_id = database.Column(
        database.String(26), database.ForeignKey("deduccion.id"), nullable=True
    )
    percepcion_id = database.Column(
        database.String(26), database.ForeignKey("percepcion.id"), nullable=True
    )
    prestacion_id = database.Column(
        database.String(26), database.ForeignKey("prestacion.id"), nullable=True
    )

    # Relationship to planillas that use this rule
    planillas = database.relationship(
        "PlanillaReglaCalculo",
        back_populates="regla_calculo",
    )


# Acumulados anuales por empleado (para cálculos como IR en Nicaragua)
class AcumuladoAnual(database.Model, BaseTabla):
    """Annual accumulated values per employee per payroll type.

    Stores running totals of salary, deductions, and taxes for each employee
    per fiscal year and payroll type. This is essential for progressive tax
    calculations like Nicaragua's IR which requires annual accumulated values.

    The fiscal year period is defined in the TipoPlanilla (payroll type) to
    support different fiscal periods (not just Jan-Dec).

    Updated after each payroll run to maintain accurate year-to-date totals.
    """

    __tablename__ = "acumulado_anual"
    __table_args__ = (
        database.UniqueConstraint(
            "empleado_id",
            "tipo_planilla_id",
            "periodo_fiscal_inicio",
            name="uq_acumulado_empleado_tipo_periodo",
        ),
    )

    empleado_id = database.Column(
        database.String(26),
        database.ForeignKey("empleado.id"),
        nullable=False,
        index=True,
    )

    # Reference to payroll type (which defines the fiscal period)
    tipo_planilla_id = database.Column(
        database.String(26),
        database.ForeignKey("tipo_planilla.id"),
        nullable=False,
        index=True,
    )

    # Fiscal period start date (calculated from TipoPlanilla settings)
    # This allows tracking accumulated values per fiscal year
    periodo_fiscal_inicio = database.Column(database.Date, nullable=False, index=True)
    periodo_fiscal_fin = database.Column(database.Date, nullable=False)

    # Accumulated salary values
    salario_bruto_acumulado = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    salario_gravable_acumulado = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    # Accumulated deductions (before tax)
    deducciones_antes_impuesto_acumulado = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    # Accumulated taxes
    impuesto_retenido_acumulado = database.Column(
        database.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    # Number of payrolls processed
    periodos_procesados = database.Column(database.Integer, nullable=False, default=0)

    # Last processed period
    ultimo_periodo_procesado = database.Column(database.Date, nullable=True)

    # Additional accumulated data (JSON for flexibility)
    # Can store: inss_acumulado, otras_deducciones_acumuladas, percepciones_acumuladas, etc.
    datos_adicionales = database.Column(
        MutableDict.as_mutable(JSON), nullable=True, default=dict
    )

    empleado = database.relationship("Empleado", backref="acumulados_anuales")
    tipo_planilla = database.relationship("TipoPlanilla", back_populates="acumulados")
