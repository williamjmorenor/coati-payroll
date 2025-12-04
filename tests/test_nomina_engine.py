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
"""Tests for the payroll engine (nomina_engine)."""

from datetime import date
from decimal import Decimal

import pytest

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


class TestCurrencyConversion:
    """Tests for currency conversion when employee salary differs from payroll currency."""

    def test_converts_employee_salary_to_planilla_currency(self, app):
        """Test that employee salary in USD is converted to NIO using exchange rate.

        This test verifies the fix for the currency conversion bug where an employee
        with salary in USD was showing the same amount in Cordobas instead of being
        converted using the exchange rate.

        Scenario:
        - Employee salary: 1000 USD
        - Exchange rate: 36.6243 NIO per USD
        - Expected salary in planilla: 36624.30 NIO
        """
        with app.app_context():
            # Create currencies
            usd = Moneda(
                codigo="USD",
                nombre="Dólar Estadounidense",
                simbolo="$",
                activo=True,
            )
            nio = Moneda(
                codigo="NIO",
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
                fecha=date(2024, 11, 30),
                tasa=Decimal("36.6243"),
            )
            db.session.add(tipo_cambio)
            db.session.flush()

            # Create payroll type
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Planilla Mensual",
                dias=30,
                periodicidad="mensual",
                periodos_por_anio=12,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla in NIO
            planilla = Planilla(
                nombre="Planilla Noviembre 2024",
                descripcion="Planilla de prueba",
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
                identificacion_personal="001-123456-0001X",
                salario_base=Decimal("1000.00"),
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

            # Execute the payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 11, 1),
                periodo_fin=date(2024, 11, 30),
                fecha_calculo=date(2024, 11, 30),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created
            assert nomina is not None
            assert len(engine.errors) == 0

            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]

            # The salary base should be converted: 1000 USD * 36.6243 = 36624.30 NIO
            expected_salary = Decimal("36624.30")
            assert emp_calculo.salario_base == expected_salary, (
                f"Expected salary base {expected_salary} NIO, "
                f"got {emp_calculo.salario_base} NIO. "
                f"Exchange rate: {emp_calculo.tipo_cambio}"
            )

            # The gross salary should also reflect the conversion
            assert emp_calculo.salario_bruto == expected_salary

            # The net salary should be the converted amount minus deductions
            assert emp_calculo.salario_neto == expected_salary

    def test_same_currency_no_conversion(self, app):
        """Test that salary is not converted when employee and planilla use same currency."""
        with app.app_context():
            # Create currency
            nio = Moneda(
                codigo="NIO2",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create payroll type
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL2",
                descripcion="Planilla Mensual",
                dias=30,
                periodicidad="mensual",
                periodos_por_anio=12,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla in NIO
            planilla = Planilla(
                nombre="Planilla NIO",
                descripcion="Planilla en Córdobas",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee with salary in NIO (same as planilla)
            empleado = Empleado(
                primer_nombre="María",
                primer_apellido="López",
                identificacion_personal="001-654321-0002Y",
                salario_base=Decimal("25000.00"),
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

            # Execute the payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 11, 1),
                periodo_fin=date(2024, 11, 30),
                fecha_calculo=date(2024, 11, 30),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created
            assert nomina is not None
            assert len(engine.errors) == 0

            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]

            # No conversion should be applied
            assert emp_calculo.tipo_cambio == Decimal("1.00")
            assert emp_calculo.salario_base == Decimal("25000.00")
            assert emp_calculo.salario_bruto == Decimal("25000.00")

    def test_no_exchange_rate_error(self, app):
        """Test that an error is generated when no exchange rate is found."""
        with app.app_context():
            # Create currencies
            eur = Moneda(
                codigo="EUR",
                nombre="Euro",
                simbolo="€",
                activo=True,
            )
            nio = Moneda(
                codigo="NIO3",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(eur)
            db.session.add(nio)
            db.session.flush()

            # Do NOT create exchange rate - simulate missing data

            # Create payroll type
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL3",
                descripcion="Planilla Mensual",
                dias=30,
                periodicidad="mensual",
                periodos_por_anio=12,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla in NIO
            planilla = Planilla(
                nombre="Planilla EUR Test",
                descripcion="Planilla para test sin tipo de cambio",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee with salary in EUR (no exchange rate to NIO)
            empleado = Empleado(
                primer_nombre="Carlos",
                primer_apellido="García",
                identificacion_personal="001-999888-0003Z",
                salario_base=Decimal("2000.00"),
                moneda_id=eur.id,
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

            # Execute the payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 11, 1),
                periodo_fin=date(2024, 11, 30),
                fecha_calculo=date(2024, 11, 30),
                usuario="test",
            )

            nomina = engine.ejecutar()

            # Verify the nomina was created but with errors
            assert nomina is not None

            # Verify an error was generated about missing exchange rate
            assert len(engine.errors) > 0
            error_text = " ".join(engine.errors)
            assert "tipo de cambio" in error_text.lower()

            # The employee should not have been processed due to the error
            assert len(engine.empleados_calculo) == 0
