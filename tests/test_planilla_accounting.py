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

"""Test accounting fields for Planilla base salary."""

from datetime import date
from decimal import Decimal

from coati_payroll.model import (
    db,
    Planilla,
    TipoPlanilla,
    Moneda,
    Empleado,
    PlanillaEmpleado,
)
from coati_payroll.nomina_engine import NominaEngine


class TestPlanillaAccountingFields:
    """Test accounting fields for base salary in Planilla."""

    def test_planilla_has_accounting_fields(self, app):
        """Test that Planilla model has the new accounting fields."""
        with app.app_context():
            # Create currency
            moneda = Moneda(
                codigo="NIO1",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db.session.add(moneda)

            # Create tipo planilla
            tipo = TipoPlanilla(
                codigo="MENSUAL1",
                descripcion="Planilla Mensual",
                dias=30,
                periodicidad="mensual",
                activo=True,
            )
            db.session.add(tipo)
            db.session.commit()

            # Create planilla with accounting fields
            planilla = Planilla(
                nombre="Test Planilla",
                descripcion="Planilla de prueba",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
                codigo_cuenta_debe_salario="610-001",
                codigo_cuenta_haber_salario="210-001",
                activo=True,
            )
            db.session.add(planilla)
            db.session.commit()

            # Verify fields were saved
            planilla_loaded = db.session.get(Planilla, planilla.id)
            assert planilla_loaded.codigo_cuenta_debe_salario == "610-001"
            assert planilla_loaded.codigo_cuenta_haber_salario == "210-001"

    def test_planilla_accounting_fields_can_be_none(self, app):
        """Test that accounting fields can be None (optional)."""
        with app.app_context():
            # Create currency
            moneda = Moneda(
                codigo="USD1",
                nombre="US Dollar",
                simbolo="$",
                activo=True,
            )
            db.session.add(moneda)

            # Create tipo planilla
            tipo = TipoPlanilla(
                codigo="QUINCENAL1",
                descripcion="Planilla Quincenal",
                dias=15,
                periodicidad="quincenal",
                activo=True,
            )
            db.session.add(tipo)
            db.session.commit()

            # Create planilla without accounting fields
            planilla = Planilla(
                nombre="Test Planilla Without Accounts",
                descripcion="Planilla sin cuentas contables",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db.session.add(planilla)
            db.session.commit()

            # Verify fields are None
            planilla_loaded = db.session.get(Planilla, planilla.id)
            assert planilla_loaded.codigo_cuenta_debe_salario is None
            assert planilla_loaded.codigo_cuenta_haber_salario is None

    def test_planilla_accounting_fields_in_nomina_context(self, app):
        """Test that accounting fields are accessible in nomina generation context."""
        with app.app_context():
            # Create currency
            moneda = Moneda(
                codigo="CRC",
                nombre="Colón Costarricense",
                simbolo="₡",
                activo=True,
            )
            db.session.add(moneda)

            # Create tipo planilla
            tipo = TipoPlanilla(
                codigo="MENSUAL_TEST1",
                descripcion="Planilla Mensual Test",
                dias=30,
                periodicidad="mensual",
                activo=True,
            )
            db.session.add(tipo)
            db.session.commit()

            # Create planilla with accounting fields
            planilla = Planilla(
                nombre="Test Planilla Nomina",
                descripcion="Planilla para test de nómina",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
                codigo_cuenta_debe_salario="610-100",
                codigo_cuenta_haber_salario="210-100",
                activo=True,
            )
            db.session.add(planilla)

            # Create employee
            empleado = Empleado(
                codigo_empleado="EMP-001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010186-0001P",
                fecha_alta=date.today(),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                activo=True,
            )
            db.session.add(empleado)
            db.session.commit()

            # Associate employee with planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True,
            )
            db.session.add(planilla_empleado)
            db.session.commit()

            # Initialize nomina engine
            periodo_inicio = date(2025, 1, 1)
            periodo_fin = date(2025, 1, 31)
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
            )

            # Verify planilla accounting fields are accessible
            assert engine.planilla.codigo_cuenta_debe_salario == "610-100"
            assert engine.planilla.codigo_cuenta_haber_salario == "210-100"

            # Generate nomina
            nomina = engine.ejecutar()

            # Verify nomina was created
            assert nomina is not None
            assert len(nomina.nomina_empleados) == 1

            # Verify accounting fields are still available through the planilla
            assert nomina.planilla.codigo_cuenta_debe_salario == "610-100"
            assert nomina.planilla.codigo_cuenta_haber_salario == "210-100"
