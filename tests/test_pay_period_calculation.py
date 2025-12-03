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
"""Tests for pay period salary calculation with different payment frequencies.

These tests verify that employee salaries are correctly prorated based on
the number of days in the pay period, ensuring proper calculation for
monthly, biweekly (quincenal), bimonthly (catorcenal), and weekly payrolls.
"""

from datetime import date
from decimal import Decimal


from coati_payroll.model import (
    db,
    Moneda,
    TipoCambio,
    Empleado,
    Planilla,
    PlanillaEmpleado,
    TipoPlanilla,
)
from coati_payroll.nomina_engine import NominaEngine


class TestPayPeriodCalculation:
    """Tests for salary calculation based on pay period days."""

    def test_biweekly_payroll_with_currency_conversion(self, app):
        """Test biweekly (quincenal) payroll calculation with currency conversion.

        This test verifies the exact scenario from the issue:
        - Employee salary: 800 USD
        - Exchange rate: 36.6243 NIO per USD
        - Pay period: 15 days (biweekly)
        - Expected calculation:
          * Monthly salary in NIO: 800 × 36.6243 = 29,299.44
          * Daily salary: 29,299.44 / 30 = 976.65
          * Biweekly salary: 976.65 × 15 = 14,649.75
        """
        with app.app_context():
            # Create currencies
            usd = Moneda(
                codigo="USD_Q",
                nombre="Dólar Estadounidense",
                simbolo="$",
                activo=True,
            )
            nio = Moneda(
                codigo="NIO_Q",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(usd)
            db.session.add(nio)
            db.session.flush()

            # Create exchange rate: USD to NIO
            tipo_cambio = TipoCambio(
                moneda_origen_id=usd.id,
                moneda_destino_id=nio.id,
                fecha=date(2024, 12, 1),
                tasa=Decimal("36.6243"),
            )
            db.session.add(tipo_cambio)
            db.session.flush()

            # Create biweekly payroll type (quincenal)
            tipo_planilla = TipoPlanilla(
                codigo="QUINCENAL",
                descripcion="Planilla Quincenal",
                dias=30,  # Base days for daily salary calculation
                periodicidad="quincenal",
                periodos_por_anio=24,  # 24 biweekly periods per year
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla in NIO
            planilla = Planilla(
                nombre="Planilla Quincenal Diciembre 2024",
                descripcion="Planilla quincenal de prueba",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee with salary in USD
            empleado = Empleado(
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-123456-0011Q",
                salario_base=Decimal("800.00"),
                moneda_id=usd.id,
                activo=True,
                fecha_alta=date(2020, 1, 1),
            )
            db.session.add(empleado)
            db.session.flush()

            # Associate employee to planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True,
            )
            db.session.add(planilla_empleado)
            db.session.commit()

            # Execute the payroll for 15-day period
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 15),
                fecha_calculo=date(2024, 12, 15),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created
            assert nomina is not None
            assert len(engine.errors) == 0

            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]

            # Expected calculation:
            # Monthly salary in NIO: 800 × 36.6243 = 29,299.44
            # Daily salary: 29,299.44 / 30 = 976.6480 -> 976.65 (rounded)
            # Biweekly salary: 976.65 × 15 = 14,649.75
            expected_biweekly_salary = Decimal("14649.75")

            assert emp_calculo.salario_base == expected_biweekly_salary, (
                f"Expected biweekly salary {expected_biweekly_salary} NIO, "
                f"got {emp_calculo.salario_base} NIO. "
                f"Exchange rate: {emp_calculo.tipo_cambio}"
            )

            # The gross salary should equal the prorated base salary (no perceptions)
            assert emp_calculo.salario_bruto == expected_biweekly_salary

            # The net salary should be the prorated amount minus deductions (none here)
            assert emp_calculo.salario_neto == expected_biweekly_salary

    def test_biweekly_payroll_same_currency(self, app):
        """Test biweekly (quincenal) payroll without currency conversion."""
        with app.app_context():
            # Create currency
            nio = Moneda(
                codigo="NIO_Q2",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create biweekly payroll type
            tipo_planilla = TipoPlanilla(
                codigo="QUINCENAL2",
                descripcion="Planilla Quincenal",
                dias=30,
                periodicidad="quincenal",
                periodos_por_anio=24,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Quincenal NIO",
                descripcion="Planilla quincenal en córdobas",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee with monthly salary of 30,000 NIO
            empleado = Empleado(
                primer_nombre="María",
                primer_apellido="López",
                identificacion_personal="001-654321-0012Q",
                salario_base=Decimal("30000.00"),
                moneda_id=nio.id,
                activo=True,
                fecha_alta=date(2020, 1, 1),
            )
            db.session.add(empleado)
            db.session.flush()

            # Associate employee to planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True,
            )
            db.session.add(planilla_empleado)
            db.session.commit()

            # Execute the payroll for 15-day period
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 15),
                fecha_calculo=date(2024, 12, 15),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created
            assert nomina is not None
            assert len(engine.errors) == 0

            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]

            # Expected: 30,000 / 30 = 1,000 per day × 15 days = 15,000
            expected_biweekly_salary = Decimal("15000.00")
            assert emp_calculo.salario_base == expected_biweekly_salary

    def test_weekly_payroll(self, app):
        """Test weekly (semanal) payroll calculation."""
        with app.app_context():
            # Create currency
            nio = Moneda(
                codigo="NIO_S",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create weekly payroll type
            tipo_planilla = TipoPlanilla(
                codigo="SEMANAL",
                descripcion="Planilla Semanal",
                dias=30,
                periodicidad="semanal",
                periodos_por_anio=52,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Semanal",
                descripcion="Planilla semanal",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee with monthly salary of 30,000 NIO
            empleado = Empleado(
                primer_nombre="Carlos",
                primer_apellido="Martínez",
                identificacion_personal="001-789012-0013S",
                salario_base=Decimal("30000.00"),
                moneda_id=nio.id,
                activo=True,
                fecha_alta=date(2020, 1, 1),
            )
            db.session.add(empleado)
            db.session.flush()

            # Associate employee to planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True,
            )
            db.session.add(planilla_empleado)
            db.session.commit()

            # Execute the payroll for 7-day period
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 7),
                fecha_calculo=date(2024, 12, 7),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created
            assert nomina is not None
            assert len(engine.errors) == 0

            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]

            # Expected: 30,000 / 30 = 1,000 per day × 7 days = 7,000
            expected_weekly_salary = Decimal("7000.00")
            assert emp_calculo.salario_base == expected_weekly_salary

    def test_bimonthly_payroll(self, app):
        """Test bimonthly (catorcenal) payroll calculation."""
        with app.app_context():
            # Create currency
            nio = Moneda(
                codigo="NIO_C",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create bimonthly payroll type (14 days)
            tipo_planilla = TipoPlanilla(
                codigo="CATORCENAL",
                descripcion="Planilla Catorcenal",
                dias=30,
                periodicidad="catorcenal",
                periodos_por_anio=26,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Catorcenal",
                descripcion="Planilla catorcenal",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee with monthly salary of 30,000 NIO
            empleado = Empleado(
                primer_nombre="Ana",
                primer_apellido="García",
                identificacion_personal="001-345678-0014C",
                salario_base=Decimal("30000.00"),
                moneda_id=nio.id,
                activo=True,
                fecha_alta=date(2020, 1, 1),
            )
            db.session.add(empleado)
            db.session.flush()

            # Associate employee to planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True,
            )
            db.session.add(planilla_empleado)
            db.session.commit()

            # Execute the payroll for 14-day period
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 14),
                fecha_calculo=date(2024, 12, 14),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created
            assert nomina is not None
            assert len(engine.errors) == 0

            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]

            # Expected: 30,000 / 30 = 1,000 per day × 14 days = 14,000
            expected_bimonthly_salary = Decimal("14000.00")
            assert emp_calculo.salario_base == expected_bimonthly_salary

    def test_monthly_payroll_still_works(self, app):
        """Test that monthly payroll still works correctly (30 days)."""
        with app.app_context():
            # Create currency
            nio = Moneda(
                codigo="NIO_M",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create monthly payroll type
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL_M",
                descripcion="Planilla Mensual",
                dias=30,
                periodicidad="mensual",
                periodos_por_anio=12,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Mensual",
                descripcion="Planilla mensual",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee with monthly salary of 30,000 NIO
            empleado = Empleado(
                primer_nombre="Luis",
                primer_apellido="Rodríguez",
                identificacion_personal="001-901234-0015M",
                salario_base=Decimal("30000.00"),
                moneda_id=nio.id,
                activo=True,
                fecha_alta=date(2020, 1, 1),
            )
            db.session.add(empleado)
            db.session.flush()

            # Associate employee to planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True,
            )
            db.session.add(planilla_empleado)
            db.session.commit()

            # Execute the payroll for 30-day period
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 30),
                fecha_calculo=date(2024, 12, 30),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created
            assert nomina is not None
            assert len(engine.errors) == 0

            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]

            # Expected: 30,000 / 30 = 1,000 per day × 30 days = 30,000
            # For monthly payroll, the salary should remain the same
            expected_monthly_salary = Decimal("30000.00")
            assert emp_calculo.salario_base == expected_monthly_salary
