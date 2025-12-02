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
    Nomina,
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


class TestNominaRecalculation:
    """Tests for payroll recalculation functionality."""

    def test_recalculate_nomina_in_generado_status(self, app, authenticated_client):
        """Test that a nomina in 'generado' status can be recalculated."""
        with app.app_context():
            # Create currencies
            nio = Moneda(
                codigo="NIO_RECALC",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create payroll type
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL_RECALC",
                descripcion="Planilla Mensual Recalculo",
                dias=30,
                periodicidad="mensual",
                periodos_por_anio=12,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Recalculo Test",
                descripcion="Planilla para test de recalculo",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee
            empleado = Empleado(
                primer_nombre="Test",
                primer_apellido="Recalculo",
                identificacion_personal="001-RECALC-0001A",
                salario_base=Decimal("15000.00"),
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

            # Execute initial payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 11, 1),
                periodo_fin=date(2024, 11, 30),
                fecha_calculo=date(2024, 11, 30),
                usuario="test",
            )
            nomina = engine.ejecutar()

            assert nomina is not None
            assert nomina.estado == "generado"
            original_nomina_id = nomina.id

            # Recalculate the nomina via the route
            response = authenticated_client.post(
                f"/planilla/{planilla.id}/nomina/{nomina.id}/recalcular",
                follow_redirects=False,
            )

            # Should redirect after recalculation
            assert response.status_code == 302

            # The original nomina should no longer exist
            old_nomina = db.session.get(Nomina, original_nomina_id)
            assert old_nomina is None

    def test_cannot_recalculate_aplicado_nomina(self, app, authenticated_client):
        """Test that a nomina in 'aplicado' (paid) status cannot be recalculated."""
        with app.app_context():
            # Create currencies
            nio = Moneda(
                codigo="NIO_PAID",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create payroll type
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL_PAID",
                descripcion="Planilla Mensual Pagada",
                dias=30,
                periodicidad="mensual",
                periodos_por_anio=12,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Pagada Test",
                descripcion="Planilla para test de pagada",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee
            empleado = Empleado(
                primer_nombre="Test",
                primer_apellido="Pagado",
                identificacion_personal="001-PAID-0002B",
                salario_base=Decimal("20000.00"),
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

            # Execute payroll and set to aplicado status
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 11, 1),
                periodo_fin=date(2024, 11, 30),
                fecha_calculo=date(2024, 11, 30),
                usuario="test",
            )
            nomina = engine.ejecutar()

            assert nomina is not None
            nomina.estado = "aplicado"
            db.session.commit()

            original_nomina_id = nomina.id

            # Try to recalculate the applied nomina
            response = authenticated_client.post(
                f"/planilla/{planilla.id}/nomina/{nomina.id}/recalcular",
                follow_redirects=False,
            )

            # Should redirect (to ver_nomina with error message)
            assert response.status_code == 302

            # The nomina should still exist and unchanged
            existing_nomina = db.session.get(Nomina, original_nomina_id)
            assert existing_nomina is not None
            assert existing_nomina.estado == "aplicado"

    def test_recalculate_nomina_in_aprobado_status(self, app, authenticated_client):
        """Test that a nomina in 'aprobado' status can be recalculated."""
        with app.app_context():
            # Create currencies
            nio = Moneda(
                codigo="NIO_APROB",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(nio)
            db.session.flush()

            # Create payroll type
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL_APROB",
                descripcion="Planilla Mensual Aprobada",
                dias=30,
                periodicidad="mensual",
                periodos_por_anio=12,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Aprobada Test",
                descripcion="Planilla para test de aprobada",
                activo=True,
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=nio.id,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create employee
            empleado = Empleado(
                primer_nombre="Test",
                primer_apellido="Aprobado",
                identificacion_personal="001-APROB-0003C",
                salario_base=Decimal("18000.00"),
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

            # Execute payroll and set to aprobado status
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2024, 11, 1),
                periodo_fin=date(2024, 11, 30),
                fecha_calculo=date(2024, 11, 30),
                usuario="test",
            )
            nomina = engine.ejecutar()

            assert nomina is not None
            nomina.estado = "aprobado"
            db.session.commit()

            original_nomina_id = nomina.id

            # Recalculate the approved nomina
            response = authenticated_client.post(
                f"/planilla/{planilla.id}/nomina/{nomina.id}/recalcular",
                follow_redirects=False,
            )

            # Should redirect after recalculation
            assert response.status_code == 302

            # The original nomina should no longer exist
            old_nomina = db.session.get(Nomina, original_nomina_id)
            assert old_nomina is None
