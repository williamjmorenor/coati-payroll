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
"""Tests for monthly accumulated salary feature.

This module tests the requirement that the system must store:
1. Salary of the current payroll
2. Accumulated salary for the year
3. Accumulated salary for the current month (for biweekly/weekly payrolls)
4. Make the monthly accumulated salary available for calculations
"""

from datetime import date
from decimal import Decimal

import pytest

from coati_payroll.model import (
    db,
    Moneda,
    Empleado,
    Planilla,
    PlanillaEmpleado,
    TipoPlanilla,
    AcumuladoAnual,
)
from coati_payroll.nomina_engine import NominaEngine


class TestMonthlyAccumulatedSalary:
    """Test monthly accumulated salary tracking for different pay periods."""

    @pytest.fixture
    def setup_payroll_components(self, app, request):
        """Setup basic payroll components with unique employee for each test."""
        with app.app_context():
            # Create currency
            nio = db.session.execute(db.select(Moneda).filter_by(codigo="NIO")).scalar_one_or_none()
            if not nio:
                nio = Moneda(
                    codigo="NIO",
                    nombre="Córdoba Nicaragüense",
                    simbolo="C$",
                    activo=True,
                )
                db.session.add(nio)
                db.session.flush()

            # Create biweekly payroll type - check if exists
            tipo_planilla = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="QUINCENAL_TEST")
            ).scalar_one_or_none()
            if not tipo_planilla:
                tipo_planilla = TipoPlanilla(
                    codigo="QUINCENAL_TEST",
                    descripcion="Planilla Quincenal de Prueba",
                    dias=15,
                    periodicidad="quincenal",
                    periodos_por_anio=24,
                )
                db.session.add(tipo_planilla)
                db.session.flush()

            # Create unique employee for each test using test name
            test_name = request.node.name
            unique_id = str(hash(test_name))[-8:]  # Last 8 chars of hash
            empleado = Empleado(
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal=f"001-010101-{unique_id}",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=nio.id,
                activo=True,
            )
            db.session.add(empleado)
            db.session.flush()

            # Create unique planilla for each test
            planilla = Planilla(
                nombre=f"Planilla Quincenal Test {unique_id}",
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
                activo=True,
            )
            db.session.add(planilla)
            db.session.flush()

            # Assign employee to planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True,
            )
            db.session.add(planilla_empleado)
            db.session.commit()

            # Return IDs instead of objects to avoid detached instance issues
            return {
                "nio_id": nio.id,
                "tipo_planilla_id": tipo_planilla.id,
                "empleado_id": empleado.id,
                "planilla_id": planilla.id,
            }

    def test_first_payroll_of_month_initializes_monthly_accumulation(self, app, setup_payroll_components):
        """Test that the first payroll of a month initializes monthly accumulation.

        Scenario:
        - Run first biweekly payroll of January (Jan 1-15)
        - Employee salary: 10,000 NIO/month, prorated to 5,000 for 15 days
        - Expected: salario_acumulado_mes should be 5,000
        """
        with app.app_context():
            components = setup_payroll_components
            planilla = db.session.get(Planilla, components["planilla_id"])
            empleado = db.session.get(Empleado, components["empleado_id"])

            # Run first payroll of January (first fortnight)
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 15),
                fecha_calculo=date(2024, 1, 15),
                usuario="test_user",
            )
            nomina = engine.ejecutar()

            assert nomina is not None, "Nomina should be created"
            assert len(nomina.nomina_empleados) == 1, "Should have 1 employee"

            # Check that monthly accumulation was initialized
            acumulado = db.session.execute(
                db.select(AcumuladoAnual).filter_by(
                    empleado_id=empleado.id,
                    tipo_planilla_id=planilla.tipo_planilla_id,
                )
            ).scalar_one()

            assert acumulado is not None, "AcumuladoAnual record should exist"
            assert acumulado.mes_actual == 1, "Should track January (month 1)"
            # Expected: 10000 / 30 = 333.33 per day, 333.33 * 15 = 4999.95
            assert acumulado.salario_acumulado_mes == Decimal(
                "4999.95"
            ), "Monthly accumulated salary should be 4999.95 for 15-day period (with rounding)"

    def test_second_payroll_of_month_adds_to_monthly_accumulation(self, app, setup_payroll_components):
        """Test that the second payroll of a month adds to monthly accumulation.

        Scenario:
        - Run first biweekly payroll of January (Jan 1-15) -> 5,000
        - Run second biweekly payroll of January (Jan 16-31) -> 5,333.33
        - Expected: salario_acumulado_mes should be 10,333.33 (sum of both)
        """
        with app.app_context():
            components = setup_payroll_components
            planilla = db.session.get(Planilla, components["planilla_id"])
            empleado = db.session.get(Empleado, components["empleado_id"])

            # Run first payroll of January (first fortnight: 15 days)
            engine1 = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 15),
                fecha_calculo=date(2024, 1, 15),
                usuario="test_user",
            )
            nomina1 = engine1.ejecutar()
            assert nomina1 is not None

            # Check first accumulation
            acumulado = db.session.execute(
                db.select(AcumuladoAnual).filter_by(
                    empleado_id=empleado.id,
                    tipo_planilla_id=planilla.tipo_planilla_id,
                )
            ).scalar_one()

            first_payment = acumulado.salario_acumulado_mes
            assert first_payment == Decimal("4999.95"), "First payment should be 4999.95 for 15 days (with rounding)"

            # Run second payroll of January (second fortnight: 16 days)
            engine2 = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 1, 16),
                periodo_fin=date(2024, 1, 31),
                fecha_calculo=date(2024, 1, 31),
                usuario="test_user",
            )
            nomina2 = engine2.ejecutar()
            assert nomina2 is not None

            # Refresh the acumulado record
            db.session.refresh(acumulado)

            # Expected second payment: 10000 / 30 = 333.33, 333.33 * 16 = 5333.28
            # Total monthly: 4999.95 + 5333.28 = 10333.23
            assert acumulado.mes_actual == 1, "Should still be January"
            assert acumulado.salario_acumulado_mes == Decimal(
                "10333.23"
            ), "Monthly accumulated should be sum of both fortnights (10333.23)"

    def test_new_month_resets_monthly_accumulation(self, app, setup_payroll_components):
        """Test that starting a new month resets the monthly accumulation.

        Scenario:
        - Run second payroll of January (Jan 16-31) -> sets accumulated to 5,333.33
        - Run first payroll of February (Feb 1-15) -> should reset and start at 5,000
        - Expected: salario_acumulado_mes should be 5,000 (not added to January's)
        """
        with app.app_context():
            components = setup_payroll_components
            planilla = db.session.get(Planilla, components["planilla_id"])
            empleado = db.session.get(Empleado, components["empleado_id"])

            # Run second payroll of January
            engine1 = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 1, 16),
                periodo_fin=date(2024, 1, 31),
                fecha_calculo=date(2024, 1, 31),
                usuario="test_user",
            )
            nomina1 = engine1.ejecutar()
            assert nomina1 is not None

            # Get accumulation after January
            acumulado = db.session.execute(
                db.select(AcumuladoAnual).filter_by(
                    empleado_id=empleado.id,
                    tipo_planilla_id=planilla.tipo_planilla_id,
                )
            ).scalar_one()

            january_accumulation = acumulado.salario_acumulado_mes
            assert acumulado.mes_actual == 1, "Should be tracking January"
            assert january_accumulation == Decimal(
                "5333.28"
            ), "January accumulation should be 5333.28 for 16 days (with rounding)"

            # Run first payroll of February
            engine2 = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 2, 1),
                periodo_fin=date(2024, 2, 15),
                fecha_calculo=date(2024, 2, 15),
                usuario="test_user",
            )
            nomina2 = engine2.ejecutar()
            assert nomina2 is not None

            # Refresh and check February accumulation
            db.session.refresh(acumulado)

            assert acumulado.mes_actual == 2, "Should now be tracking February"
            # February should start fresh: 10000 / 30 * 15 = 4999.95
            assert acumulado.salario_acumulado_mes == Decimal(
                "4999.95"
            ), "February should start with fresh accumulation of 4999.95"

    def test_monthly_accumulated_salary_available_in_calculations(self, app, setup_payroll_components):
        """Test that salario_acumulado_mes is available for use in formula calculations.

        This verifies requirement #4: The monthly accumulated salary must be
        available as a variable for calculations.
        """
        with app.app_context():
            components = setup_payroll_components
            planilla = db.session.get(Planilla, components["planilla_id"])
            empleado = db.session.get(Empleado, components["empleado_id"])

            # Run first payroll to establish accumulation
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 15),
                fecha_calculo=date(2024, 1, 15),
                usuario="test_user",
            )

            # Create an employee calculation object to test variable construction
            from coati_payroll.nomina_engine import EmpleadoCalculo

            emp_calculo = EmpleadoCalculo(empleado, planilla)

            # Build calculation variables
            variables = engine._construir_variables(emp_calculo)

            # Verify that salario_acumulado_mes is available
            assert (
                "salario_acumulado_mes" in variables
            ), "salario_acumulado_mes should be available in calculation variables"

            # Initially should be 0 (before first payroll)
            assert variables["salario_acumulado_mes"] == Decimal(
                "0.00"
            ), "Initial value should be 0 before any payroll processing"

    def test_annual_accumulation_still_works(self, app, setup_payroll_components):
        """Test that annual accumulated salary still works alongside monthly accumulation.

        Scenario:
        - Run payrolls for January and February
        - Verify both monthly and annual accumulations are tracked correctly
        """
        with app.app_context():
            components = setup_payroll_components
            planilla = db.session.get(Planilla, components["planilla_id"])
            empleado = db.session.get(Empleado, components["empleado_id"])

            # Run January first fortnight
            engine1 = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 15),
                fecha_calculo=date(2024, 1, 15),
                usuario="test_user",
            )
            nomina1 = engine1.ejecutar()
            assert nomina1 is not None

            # Run January second fortnight
            engine2 = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 1, 16),
                periodo_fin=date(2024, 1, 31),
                fecha_calculo=date(2024, 1, 31),
                usuario="test_user",
            )
            nomina2 = engine2.ejecutar()
            assert nomina2 is not None

            # Run February first fortnight
            engine3 = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 2, 1),
                periodo_fin=date(2024, 2, 15),
                fecha_calculo=date(2024, 2, 15),
                usuario="test_user",
            )
            nomina3 = engine3.ejecutar()
            assert nomina3 is not None

            # Check final accumulations
            acumulado = db.session.execute(
                db.select(AcumuladoAnual).filter_by(
                    empleado_id=empleado.id,
                    tipo_planilla_id=planilla.tipo_planilla_id,
                )
            ).scalar_one()

            # Monthly should be just February's first fortnight
            assert acumulado.salario_acumulado_mes == Decimal(
                "4999.95"
            ), "Monthly accumulation should be only February (4999.95)"

            # Annual should be sum of all three payrolls
            # Jan 1-15: 4999.95, Jan 16-31: 5333.28, Feb 1-15: 4999.95 = 15333.18
            assert acumulado.salario_bruto_acumulado == Decimal(
                "15333.18"
            ), "Annual accumulation should be sum of all payrolls (15333.18)"

            # Should have processed 3 periods
            assert acumulado.periodos_procesados == 3, "Should have processed 3 payroll periods"
