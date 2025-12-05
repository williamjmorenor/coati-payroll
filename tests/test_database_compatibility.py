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
"""Tests for database compatibility across SQLite, PostgreSQL, and MySQL.

This test suite ensures that the application schema and queries work correctly
across different database engines: SQLite (development), PostgreSQL (production),
and MySQL (production alternative).
"""

from decimal import Decimal
from datetime import date, datetime, timezone
import pytest

from coati_payroll.model import (
    db,
    Usuario,
    Moneda,
    Empleado,
    TipoPlanilla,
    Planilla,
    Percepcion,
    Deduccion,
    Prestacion,
    PlanillaEmpleado,
    PlanillaIngreso,
    PlanillaDeduccion,
    PlanillaPrestacion,
    TipoCambio,
    generador_de_codigos_unicos,
    generador_codigo_empleado,
    utc_now,
)


class TestDatabaseCompatibility:
    """Test database compatibility features across engines."""

    def test_ulid_primary_keys(self, app):
        """Test ULID-based String(26) primary keys work across databases."""
        with app.app_context():
            # Use or create a currency with ULID ID
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="USD")
            ).scalar_one_or_none()
            
            if moneda is None:
                moneda = Moneda(
                    codigo="USD",
                    nombre="US Dollar",
                    simbolo="$",
                )
                db.session.add(moneda)
                db.session.commit()

            # Verify ID is 26 characters
            assert len(moneda.id) == 26
            assert isinstance(moneda.id, str)

            # Retrieve and verify
            retrieved = db.session.execute(
                db.select(Moneda).filter_by(codigo="USD")
            ).scalar_one()
            assert retrieved.id == moneda.id
            assert retrieved.codigo == "USD"

    def test_numeric_decimal_columns(self, app):
        """Test Numeric/Decimal columns work consistently across databases."""
        with app.app_context():
            # Use or create currency
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one_or_none()
            
            if moneda is None:
                moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$")
                db.session.add(moneda)
                db.session.commit()

            # Create employee with decimal salary
            empleado = Empleado(
                codigo_empleado="TEST-001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001X",
                salario_base=Decimal("15750.50"),
                moneda_id=moneda.id,
            )
            db.session.add(empleado)
            db.session.commit()

            # Retrieve and verify decimal precision
            retrieved = db.session.execute(
                db.select(Empleado).filter_by(codigo_empleado="TEST-001")
            ).scalar_one()
            assert retrieved.salario_base == Decimal("15750.50")
            assert isinstance(retrieved.salario_base, Decimal)

    def test_json_column_storage(self, app):
        """Test JSON column storage works across databases."""
        with app.app_context():
            # Create currency
            moneda = Moneda(codigo="EUR", nombre="Euro", simbolo="€")
            db.session.add(moneda)
            db.session.commit()

            # Create employee with JSON data
            empleado = Empleado(
                codigo_empleado="TEST-002",
                primer_nombre="Test",
                primer_apellido="JSON",
                identificacion_personal="001-010180-0002X",
                salario_base=Decimal("20000.00"),
                moneda_id=moneda.id,
                datos_adicionales={
                    "campo1": "valor1",
                    "campo2": 123,
                    "campo3": True,
                    "campo4": ["lista", "de", "valores"],
                },
            )
            db.session.add(empleado)
            db.session.commit()

            # Retrieve and verify JSON data
            retrieved = db.session.execute(
                db.select(Empleado).filter_by(codigo_empleado="TEST-002")
            ).scalar_one()
            assert retrieved.datos_adicionales["campo1"] == "valor1"
            assert retrieved.datos_adicionales["campo2"] == 123
            assert retrieved.datos_adicionales["campo3"] is True
            assert retrieved.datos_adicionales["campo4"] == ["lista", "de", "valores"]

    def test_unique_constraints(self, app):
        """Test unique constraints work across databases."""
        with app.app_context():
            # Create first currency
            moneda1 = Moneda(codigo="GBP", nombre="Pound Sterling", simbolo="£")
            db.session.add(moneda1)
            db.session.commit()

            # Try to create duplicate codigo
            moneda2 = Moneda(codigo="GBP", nombre="British Pound", simbolo="£")
            db.session.add(moneda2)

            # Should raise integrity error
            with pytest.raises(Exception):  # IntegrityError in SQLAlchemy
                db.session.commit()
            db.session.rollback()

    def test_foreign_key_constraints(self, app):
        """Test foreign key relationships work across databases."""
        with app.app_context():
            # Create currency and employee
            moneda = Moneda(codigo="JPY", nombre="Yen", simbolo="¥")
            db.session.add(moneda)
            db.session.commit()

            empleado = Empleado(
                codigo_empleado="TEST-003",
                primer_nombre="Test",
                primer_apellido="FK",
                identificacion_personal="001-010180-0003X",
                salario_base=Decimal("25000.00"),
                moneda_id=moneda.id,
            )
            db.session.add(empleado)
            db.session.commit()

            # Verify relationship works
            retrieved = db.session.execute(
                db.select(Empleado).filter_by(codigo_empleado="TEST-003")
            ).scalar_one()
            assert retrieved.moneda.codigo == "JPY"
            assert retrieved.moneda.nombre == "Yen"

    def test_date_and_datetime_columns(self, app):
        """Test Date and DateTime columns work across databases."""
        with app.app_context():
            # Use or create currency
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="CAD")
            ).scalar_one_or_none()
            
            if moneda is None:
                moneda = Moneda(codigo="CAD", nombre="Canadian Dollar", simbolo="C$")
                db.session.add(moneda)
                db.session.commit()

            # Create employee with dates
            fecha_alta = date(2025, 1, 15)
            empleado = Empleado(
                codigo_empleado="TEST-004",
                primer_nombre="Test",
                primer_apellido="Dates",
                identificacion_personal="001-010180-0004X",
                salario_base=Decimal("30000.00"),
                fecha_alta=fecha_alta,
                fecha_nacimiento=date(1990, 5, 20),
                moneda_id=moneda.id,
            )
            db.session.add(empleado)
            db.session.commit()

            # Retrieve and verify dates
            retrieved = db.session.execute(
                db.select(Empleado).filter_by(codigo_empleado="TEST-004")
            ).scalar_one()
            assert retrieved.fecha_alta == fecha_alta
            assert retrieved.fecha_nacimiento == date(1990, 5, 20)
            assert isinstance(retrieved.creado, date)
            assert isinstance(retrieved.timestamp, datetime)

    def test_boolean_columns(self, app):
        """Test Boolean columns work across databases."""
        with app.app_context():
            # Create active currency
            moneda1 = Moneda(codigo="AUD", nombre="Australian Dollar", simbolo="A$", activo=True)
            db.session.add(moneda1)

            # Create inactive currency
            moneda2 = Moneda(codigo="NZD", nombre="New Zealand Dollar", simbolo="NZ$", activo=False)
            db.session.add(moneda2)
            db.session.commit()

            # Retrieve and verify booleans
            active = db.session.execute(
                db.select(Moneda).filter_by(codigo="AUD")
            ).scalar_one()
            inactive = db.session.execute(
                db.select(Moneda).filter_by(codigo="NZD")
            ).scalar_one()

            assert active.activo is True
            assert inactive.activo is False

    def test_multiple_unique_constraints_in_one_table(self, app):
        """Test tables with multiple unique constraints work across databases."""
        with app.app_context():
            # Create first employee
            moneda = Moneda(codigo="CHF", nombre="Swiss Franc", simbolo="Fr")
            db.session.add(moneda)
            db.session.commit()

            emp1 = Empleado(
                codigo_empleado="TEST-005",
                primer_nombre="Test",
                primer_apellido="Multi",
                identificacion_personal="001-010180-0005X",
                salario_base=Decimal("35000.00"),
                moneda_id=moneda.id,
            )
            db.session.add(emp1)
            db.session.commit()

            # Try duplicate codigo_empleado (should fail)
            emp2 = Empleado(
                codigo_empleado="TEST-005",
                primer_nombre="Different",
                primer_apellido="Person",
                identificacion_personal="001-010180-0006X",
                salario_base=Decimal("40000.00"),
                moneda_id=moneda.id,
            )
            db.session.add(emp2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

            # Try duplicate identificacion_personal (should fail)
            emp3 = Empleado(
                codigo_empleado="TEST-006",
                primer_nombre="Another",
                primer_apellido="Person",
                identificacion_personal="001-010180-0005X",
                salario_base=Decimal("45000.00"),
                moneda_id=moneda.id,
            )
            db.session.add(emp3)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_composite_unique_constraints(self, app):
        """Test composite unique constraints work across databases."""
        with app.app_context():
            # Create monedas
            nio = Moneda(codigo="NIO2", nombre="Córdoba", simbolo="C$")
            usd = Moneda(codigo="USD2", nombre="US Dollar", simbolo="$")
            db.session.add_all([nio, usd])
            db.session.commit()

            # Create first exchange rate
            tc1 = TipoCambio(
                fecha=date(2025, 1, 1),
                moneda_origen_id=nio.id,
                moneda_destino_id=usd.id,
                tasa=Decimal("0.027"),
            )
            db.session.add(tc1)
            db.session.commit()

            # Try to create duplicate (same date, same currencies) - should fail
            tc2 = TipoCambio(
                fecha=date(2025, 1, 1),
                moneda_origen_id=nio.id,
                moneda_destino_id=usd.id,
                tasa=Decimal("0.028"),
            )
            db.session.add(tc2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

            # Different date should work
            tc3 = TipoCambio(
                fecha=date(2025, 1, 2),
                moneda_origen_id=nio.id,
                moneda_destino_id=usd.id,
                tasa=Decimal("0.028"),
            )
            db.session.add(tc3)
            db.session.commit()  # Should succeed

    def test_count_queries_with_select(self, app):
        """Test that count queries work with modern select() syntax across databases."""
        with app.app_context():
            from sqlalchemy import func, select

            # Create test data
            moneda = Moneda(codigo="SEK", nombre="Swedish Krona", simbolo="kr")
            db.session.add(moneda)
            db.session.commit()

            tipo_planilla = TipoPlanilla(
                codigo="TEST-MENSUAL",
                descripcion="Planilla Test Mensual",
                dias=30,
                periodicidad="mensual",
            )
            db.session.add(tipo_planilla)
            db.session.commit()

            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=moneda.id,
            )
            db.session.add(planilla)
            db.session.commit()

            # Create multiple employees
            NUM_TEST_EMPLOYEES = 5
            for i in range(NUM_TEST_EMPLOYEES):
                emp = Empleado(
                    codigo_empleado=f"COUNT-{i:03d}",
                    primer_nombre=f"Test{i}",
                    primer_apellido="Count",
                    identificacion_personal=f"001-010180-00{i}0X",
                    salario_base=Decimal("10000.00"),
                    moneda_id=moneda.id,
                )
                db.session.add(emp)
                db.session.commit()

                # Associate with planilla
                pe = PlanillaEmpleado(
                    planilla_id=planilla.id,
                    empleado_id=emp.id,
                )
                db.session.add(pe)
            db.session.commit()

            # Test count using modern select() syntax
            count = db.session.execute(
                select(func.count()).select_from(PlanillaEmpleado).filter_by(planilla_id=planilla.id)
            ).scalar()
            assert count == NUM_TEST_EMPLOYEES

    def test_order_by_queries(self, app):
        """Test ORDER BY queries work across databases."""
        with app.app_context():
            # Create multiple currencies
            currencies = [
                Moneda(codigo="AAA", nombre="Currency A", simbolo="A"),
                Moneda(codigo="ZZZ", nombre="Currency Z", simbolo="Z"),
                Moneda(codigo="MMM", nombre="Currency M", simbolo="M"),
            ]
            for curr in currencies:
                db.session.add(curr)
            db.session.commit()

            # Query ordered by codigo
            ordered = db.session.execute(
                db.select(Moneda).filter(
                    Moneda.codigo.in_(["AAA", "ZZZ", "MMM"])
                ).order_by(Moneda.codigo)
            ).scalars().all()

            assert len(ordered) == 3
            assert ordered[0].codigo == "AAA"
            assert ordered[1].codigo == "MMM"
            assert ordered[2].codigo == "ZZZ"

    def test_filter_by_date_range(self, app):
        """Test date range filtering works across databases."""
        with app.app_context():
            # Create monedas for date range testing
            nio = Moneda(codigo="NIO_DATE_TEST", nombre="Córdoba", simbolo="C$")
            usd = Moneda(codigo="USD_DATE_TEST", nombre="US Dollar", simbolo="$")
            db.session.add_all([nio, usd])
            db.session.commit()

            # Create exchange rates for different dates
            dates_rates = [
                (date(2025, 1, 1), Decimal("0.027")),
                (date(2025, 1, 15), Decimal("0.028")),
                (date(2025, 2, 1), Decimal("0.029")),
            ]
            for fecha, tasa in dates_rates:
                tc = TipoCambio(
                    fecha=fecha,
                    moneda_origen_id=nio.id,
                    moneda_destino_id=usd.id,
                    tasa=tasa,
                )
                db.session.add(tc)
            db.session.commit()

            # Query for January rates only
            jan_rates = db.session.execute(
                db.select(TipoCambio).filter(
                    TipoCambio.fecha >= date(2025, 1, 1),
                    TipoCambio.fecha < date(2025, 2, 1),
                    TipoCambio.moneda_origen_id == nio.id,
                )
            ).scalars().all()

            assert len(jan_rates) == 2
            assert all(rate.fecha.month == 1 for rate in jan_rates)
