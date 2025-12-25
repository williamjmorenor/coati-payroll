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
"""Unit tests for nomina_engine.py - CRITICAL payroll calculation engine.

This module tests the core payroll processing engine that handles:
- Salary calculations
- Perceptions (income additions)
- Deductions (salary subtractions)
- Benefits (employer costs)
- Exchange rates
- Accumulated annual values
- Automatic loan/advance deductions

These tests are CRITICAL as they validate money calculations affecting employees.
"""

from datetime import date
from decimal import Decimal


from coati_payroll.enums import FormulaType
from coati_payroll.nomina_engine import (
    NominaEngine,
    EmpleadoCalculo,
)
from coati_payroll.nomina_engine.calculators.concept_calculator import ConceptCalculator
from coati_payroll.nomina_engine.calculators.salary_calculator import SalaryCalculator
from coati_payroll.nomina_engine.repositories.config_repository import ConfigRepository
from coati_payroll.model import db


class TestEmpleadoCalculo:
    """Tests for EmpleadoCalculo container class."""

    def test_empleado_calculo_initialization(self, app, db_session):
        """Test EmpleadoCalculo initializes with correct default values."""
        from coati_payroll.model import Empleado, Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            # Create minimal required entities
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            # Test EmpleadoCalculo initialization
            emp_calculo = EmpleadoCalculo(empleado, planilla)

            assert emp_calculo.empleado == empleado
            assert emp_calculo.planilla == planilla
            assert emp_calculo.salario_base == Decimal("15000.00")
            assert emp_calculo.salario_mensual == Decimal("15000.00")
            assert len(emp_calculo.percepciones) == 0
            assert len(emp_calculo.deducciones) == 0
            assert len(emp_calculo.prestaciones) == 0
            assert emp_calculo.total_percepciones == Decimal("0.00")
            assert emp_calculo.total_deducciones == Decimal("0.00")
            assert emp_calculo.total_prestaciones == Decimal("0.00")
            assert emp_calculo.salario_bruto == Decimal("0.00")
            assert emp_calculo.salario_neto == Decimal("0.00")
            assert emp_calculo.tipo_cambio == Decimal("1.00")
            assert emp_calculo.moneda_origen_id == moneda.id
            assert isinstance(emp_calculo.novedades, dict)
            assert isinstance(emp_calculo.variables_calculo, dict)


class TestNominaEngineInitialization:
    """Tests for NominaEngine initialization."""

    def test_nomina_engine_initialization(self, app, db_session):
        """Test NominaEngine initializes correctly."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            moneda = Moneda(codigo="USD", nombre="Dollar", simbolo="$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="QUINCENAL",
                descripcion="Quincenal",
                periodicidad="quincenal",
                dias=15,
                periodos_por_anio=24,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Planilla Quincenal",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()
            db_session.commit()

            periodo_inicio = date(2025, 1, 1)
            periodo_fin = date(2025, 1, 15)

            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                fecha_calculo=date(2025, 1, 15),
                usuario="testuser",
            )

            assert engine.planilla == planilla
            assert engine.periodo_inicio == periodo_inicio
            assert engine.periodo_fin == periodo_fin
            assert engine.fecha_calculo == date(2025, 1, 15)
            assert engine.usuario == "testuser"
            assert engine.nomina is None
            assert len(engine.empleados_calculo) == 0
            assert len(engine.errors) == 0
            assert len(engine.warnings) == 0

    def test_nomina_engine_default_fecha_calculo(self, app, db_session):
        """Test that fecha_calculo defaults to today."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            moneda = Moneda(codigo="USD", nombre="Dollar", simbolo="$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()
            db_session.commit()

            engine = NominaEngine(planilla=planilla, periodo_inicio=date(2025, 1, 1), periodo_fin=date(2025, 1, 31))

            assert engine.fecha_calculo == date.today()


class TestPlanillaValidation:
    """Tests for planilla validation before execution."""

    def test_validar_planilla_inactive(self, app, db_session):
        """Test validation fails for inactive planilla."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            moneda = Moneda(codigo="USD", nombre="Dollar", simbolo="$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Inactive Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=False,  # Inactive!
            )
            db_session.add(planilla)
            db_session.flush()
            db_session.commit()

            engine = NominaEngine(planilla=planilla, periodo_inicio=date(2025, 1, 1), periodo_fin=date(2025, 1, 31))

            is_valid = engine.validar_planilla()
            assert is_valid is False
            assert len(engine.errors) >= 1
            # The validator may return multiple errors (inactive + no employees)
            assert any("no está activa" in e for e in engine.errors)

    def test_validar_planilla_no_employees(self, app, db_session):
        """Test validation fails when planilla has no employees."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            moneda = Moneda(codigo="USD", nombre="Dollar", simbolo="$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Empty Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()
            db_session.commit()

            engine = NominaEngine(planilla=planilla, periodo_inicio=date(2025, 1, 1), periodo_fin=date(2025, 1, 31))

            is_valid = engine.validar_planilla()
            assert is_valid is False
            assert len(engine.errors) == 1
            assert "no tiene empleados" in engine.errors[0]


class TestSalarioPeriodoCalculation:
    """Tests for salary period calculation (_calcular_salario_periodo)."""

    def test_calcular_salario_periodo_mensual_30_dias(self, app, db_session):
        """Test monthly salary for full 30-day period."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Planilla Mensual",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()
            db_session.commit()

            salario_mensual = Decimal("15000.00")

            # Use SalaryCalculator directly
            config_repo = ConfigRepository(db.session)
            calculator = SalaryCalculator(config_repo)

            salario_periodo = calculator.calculate_period_salary(
                salario_mensual, planilla, date(2025, 1, 1), date(2025, 1, 30), date(2025, 1, 30)
            )

            # Full month should return full salary
            assert salario_periodo == Decimal("15000.00")

    def test_calcular_salario_periodo_quincenal(self, app, db_session):
        """Test biweekly salary calculation."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="QUINCENAL",
                descripcion="Quincenal",
                periodicidad="quincenal",
                dias=15,
                periodos_por_anio=24,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Planilla Quincenal",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()
            db_session.commit()

            salario_mensual = Decimal("30000.00")

            # Use SalaryCalculator directly
            config_repo = ConfigRepository(db.session)
            calculator = SalaryCalculator(config_repo)

            salario_periodo = calculator.calculate_period_salary(
                salario_mensual, planilla, date(2025, 1, 1), date(2025, 1, 15), date(2025, 1, 15)
            )

            # 15 days = half month: 30000 / 30 * 15 = 15000
            assert salario_periodo == Decimal("15000.00")

    def test_calcular_salario_periodo_partial_month(self, app, db_session):
        """Test salary calculation for partial month (new hire)."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Planilla Mensual",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()
            db_session.commit()

            salario_mensual = Decimal("30000.00")

            # Use SalaryCalculator directly
            config_repo = ConfigRepository(db.session)
            calculator = SalaryCalculator(config_repo)

            salario_periodo = calculator.calculate_period_salary(
                salario_mensual, planilla, date(2025, 1, 20), date(2025, 1, 30), date(2025, 1, 30)
            )

            # 11 days: 30000 / 30 * 11 = 11000
            assert salario_periodo == Decimal("11000.00")


class TestCalculoConcepto:
    """Tests for _calcular_concepto method - calculates perception/deduction amounts."""

    def test_calcular_concepto_fijo(self, app, db_session):
        """Test fixed amount calculation."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("10000.00")
            emp_calculo.salario_mensual = Decimal("10000.00")
            emp_calculo.variables_calculo = {}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("500.00"),
                porcentaje=None,
                formula=None,
                monto_override=None,
                porcentaje_override=None,
            )

            assert monto == Decimal("500.00")

    def test_calcular_concepto_porcentaje_salario(self, app, db_session):
        """Test percentage of salary calculation."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("10000.00")
            emp_calculo.salario_mensual = Decimal("10000.00")
            emp_calculo.variables_calculo = {}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                monto_default=None,
                porcentaje=Decimal("10.00"),  # 10%
                formula=None,
                monto_override=None,
                porcentaje_override=None,
            )

            # 10% of 10000 = 1000
            assert monto == Decimal("1000.00")

    def test_calcular_concepto_with_override(self, app, db_session):
        """Test that override values take precedence."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("10000.00")
            emp_calculo.salario_mensual = Decimal("10000.00")
            emp_calculo.variables_calculo = {}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            # Override should take precedence
            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("500.00"),
                porcentaje=None,
                formula=None,
                monto_override=Decimal("750.00"),  # Override!
                porcentaje_override=None,
            )

            assert monto == Decimal("750.00")


class TestHorasYDiasCalculation:
    """Tests for hours and days based calculations."""

    def test_calcular_concepto_horas(self, app, db_session):
        """Test calculation based on hours (overtime)."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("24000.00"),  # Monthly salary
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("24000.00")
            emp_calculo.salario_mensual = Decimal("24000.00")
            emp_calculo.novedades = {"HORAS_EXTRA": Decimal("10")}  # 10 overtime hours
            emp_calculo.variables_calculo = {"novedad_HORAS_EXTRA": Decimal("10")}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.HORAS,
                monto_default=None,
                porcentaje=Decimal("150.00"),  # 150% overtime rate
                formula=None,
                monto_override=None,
                porcentaje_override=None,
                codigo_concepto="HORAS_EXTRA",
            )

            # Hourly rate: 24000 / 30 / 8 = 100 per hour
            # 150% overtime: 100 * 1.5 = 150 per hour
            # 10 hours: 150 * 10 = 1500
            assert monto == Decimal("1500.00")

    def test_calcular_concepto_horas_no_novedad(self, app, db_session):
        """Test hours calculation returns 0 when no novedad exists."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("24000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("24000.00")
            emp_calculo.salario_mensual = Decimal("24000.00")
            emp_calculo.novedades = {}  # No hours recorded
            emp_calculo.variables_calculo = {}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.HORAS,
                monto_default=None,
                porcentaje=Decimal("150.00"),
                formula=None,
                monto_override=None,
                porcentaje_override=None,
                codigo_concepto="HORAS_EXTRA",
            )

            assert monto == Decimal("0.00")

    def test_calcular_concepto_dias(self, app, db_session):
        """Test calculation based on days (absences, vacations)."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("30000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("30000.00")
            emp_calculo.salario_mensual = Decimal("30000.00")
            emp_calculo.novedades = {"VACACIONES": Decimal("5")}  # 5 vacation days
            emp_calculo.variables_calculo = {"novedad_VACACIONES": Decimal("5")}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.DIAS,
                monto_default=None,
                porcentaje=Decimal("100.00"),  # 100% of daily rate
                formula=None,
                monto_override=None,
                porcentaje_override=None,
                codigo_concepto="VACACIONES",
            )

            # Daily rate: 30000 / 30 = 1000 per day
            # 5 days: 1000 * 5 = 5000
            assert monto == Decimal("5000.00")


class TestBadInputNominaEngine:
    """Tests for handling bad input in nomina_engine - CRITICAL for production."""

    def test_calcular_concepto_with_none_porcentaje(self, app, db_session):
        """Test calculation handles None porcentaje gracefully."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("10000.00")
            emp_calculo.salario_mensual = Decimal("10000.00")
            emp_calculo.variables_calculo = {}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            # None porcentaje should return 0
            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                monto_default=None,
                porcentaje=None,  # None!
                formula=None,
                monto_override=None,
                porcentaje_override=None,
            )

            assert monto == Decimal("0.00")

    def test_calcular_concepto_with_zero_salario_base(self, app, db_session):
        """Test calculation with zero salary base."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("0.00"),  # Zero salary!
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("0.00")
            emp_calculo.salario_mensual = Decimal("0.00")
            emp_calculo.variables_calculo = {}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                monto_default=None,
                porcentaje=Decimal("10.00"),
                formula=None,
                monto_override=None,
                porcentaje_override=None,
            )

            # 10% of 0 = 0
            assert monto == Decimal("0.00")

    def test_calcular_concepto_with_negative_hours(self, app, db_session):
        """Test calculation handles negative hours (should return 0)."""
        from coati_payroll.model import Planilla, TipoPlanilla, Moneda, Empresa, Empleado

        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="TEST",
                descripcion="Test",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)

            db_session.flush()

            planilla = Planilla(
                nombre="Test Planilla",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("24000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            db_session.commit()

            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("24000.00")
            emp_calculo.salario_mensual = Decimal("24000.00")
            emp_calculo.novedades = {"HORAS_EXTRA": Decimal("-5")}  # Negative hours!
            emp_calculo.variables_calculo = {"novedad_HORAS_EXTRA": Decimal("-5")}

            # Use ConceptCalculator directly
            config_repo = ConfigRepository(db.session)
            warnings = []
            calculator = ConceptCalculator(config_repo, warnings)

            monto = calculator.calculate(
                emp_calculo=emp_calculo,
                formula_tipo=FormulaType.HORAS,
                monto_default=None,
                porcentaje=Decimal("150.00"),
                formula=None,
                monto_override=None,
                porcentaje_override=None,
                codigo_concepto="HORAS_EXTRA",
            )

            # Negative hours should return 0 (calculator should handle this)
            assert monto == Decimal("0.00")
