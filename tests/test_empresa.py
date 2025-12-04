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
"""Tests for Empresa (Company) functionality."""

import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from coati_payroll.model import (
    Empresa,
    Empleado,
    Planilla,
    PlanillaEmpleado,
    TipoPlanilla,
    Moneda,
    db,
)


class TestEmpresaModel:
    """Test Empresa model."""

    def test_create_empresa(self, app):
        """Test creating a company."""
        with app.app_context():
            empresa = Empresa(
                codigo="EMP001",
                razon_social="Test Company S.A.",
                ruc="J0123456789",
                activo=True,
            )
            db.session.add(empresa)
            db.session.commit()

            assert empresa.id is not None
            assert empresa.codigo == "EMP001"
            assert empresa.razon_social == "Test Company S.A."
            assert empresa.activo is True

    def test_empresa_unique_codigo(self, app):
        """Test that empresa codigo must be unique."""
        with app.app_context():
            empresa1 = Empresa(
                codigo="EMP_UNIQUE_CODE_1",
                razon_social="Company 1",
                ruc="J0123456780",
            )
            empresa2 = Empresa(
                codigo="EMP_UNIQUE_CODE_1",
                razon_social="Company 2",
                ruc="J9876543210",
            )
            db.session.add(empresa1)
            db.session.commit()

            db.session.add(empresa2)
            with pytest.raises(IntegrityError):  # Unique constraint violation
                db.session.commit()
            db.session.rollback()

    def test_empresa_unique_ruc(self, app):
        """Test that empresa RUC must be unique."""
        with app.app_context():
            empresa1 = Empresa(
                codigo="EMP_UNIQUE_RUC_1",
                razon_social="Company 1",
                ruc="J0123456781",
            )
            empresa2 = Empresa(
                codigo="EMP_UNIQUE_RUC_2",
                razon_social="Company 2",
                ruc="J0123456781",
            )
            db.session.add(empresa1)
            db.session.commit()

            db.session.add(empresa2)
            with pytest.raises(IntegrityError):  # Unique constraint violation
                db.session.commit()
            db.session.rollback()


class TestEmpresaEmployeeRelationship:
    """Test Empresa-Employee relationship."""

    def test_employee_belongs_to_empresa(self, app):
        """Test that an employee can belong to a company."""
        with app.app_context():
            empresa = Empresa(
                codigo="EMP_EMP_REL_1",
                razon_social="Test Company",
                ruc="J0123456782",
            )
            db.session.add(empresa)
            db.session.commit()

            empleado = Empleado(
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010101-0001A",
                fecha_alta=date.today(),
                salario_base=Decimal("10000.00"),
                empresa_id=empresa.id,
            )
            db.session.add(empleado)
            db.session.commit()

            assert empleado.empresa_id == empresa.id
            assert empleado.empresa == empresa
            assert empleado in empresa.empleados

    def test_employee_without_empresa(self, app):
        """Test that an employee can exist without a company."""
        with app.app_context():
            empleado = Empleado(
                primer_nombre="Pedro",
                primer_apellido="González",
                identificacion_personal="001-020202-0002B",
                fecha_alta=date.today(),
                salario_base=Decimal("10000.00"),
            )
            db.session.add(empleado)
            db.session.commit()

            assert empleado.empresa_id is None
            assert empleado.empresa is None


class TestEmpresaPlanillaRelationship:
    """Test Empresa-Planilla relationship."""

    def test_planilla_belongs_to_empresa(self, app):
        """Test that a planilla can belong to a company."""
        with app.app_context():
            # Create empresa
            empresa = Empresa(
                codigo="EMP_PLANILLA_REL_1",
                razon_social="Test Company",
                ruc="J0123456783",
            )
            db.session.add(empresa)

            # Create tipo_planilla - check if already exists
            tipo = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="MENSUAL")
            ).scalar_one_or_none()
            if not tipo:
                tipo = TipoPlanilla(
                    codigo="MENSUAL",
                    descripcion="Planilla Mensual",
                    dias=30,
                    periodicidad="mensual",
                )
                db.session.add(tipo)

            # Create moneda - check if already exists
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one_or_none()
            if not moneda:
                moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$")
                db.session.add(moneda)
            db.session.commit()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Test EMP_REL_1",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
                empresa_id=empresa.id,
            )
            db.session.add(planilla)
            db.session.commit()

            assert planilla.empresa_id == empresa.id
            assert planilla.empresa == empresa
            assert planilla in empresa.planillas

    def test_planilla_without_empresa(self, app):
        """Test that a planilla can exist without a company."""
        with app.app_context():
            # Create tipo_planilla - check if already exists
            tipo = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="MENSUAL")
            ).scalar_one_or_none()
            if not tipo:
                tipo = TipoPlanilla(
                    codigo="MENSUAL",
                    descripcion="Planilla Mensual",
                    dias=30,
                    periodicidad="mensual",
                )
                db.session.add(tipo)

            # Create moneda - check if already exists
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one_or_none()
            if not moneda:
                moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$")
                db.session.add(moneda)
            db.session.commit()

            # Create planilla
            planilla = Planilla(
                nombre="Planilla Test WITHOUT_EMP",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
            )
            db.session.add(planilla)
            db.session.commit()

            assert planilla.empresa_id is None
            assert planilla.empresa is None


class TestCrossCompanyValidation:
    """Test that employees and planillas from different companies cannot be mixed."""

    def test_cannot_assign_employee_from_different_company(self, app, authenticated_client):
        """Test that employees from different companies cannot be assigned to a planilla."""
        with app.app_context():
            # Create two companies
            empresa1 = Empresa(
                codigo="EMP_CROSS_1A",
                razon_social="Company 1",
                ruc="J0123456784",
            )
            empresa2 = Empresa(
                codigo="EMP_CROSS_1B",
                razon_social="Company 2",
                ruc="J9876543211",
            )
            db.session.add_all([empresa1, empresa2])

            # Create tipo_planilla and moneda - check if already exists
            tipo = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="MENSUAL")
            ).scalar_one_or_none()
            if not tipo:
                tipo = TipoPlanilla(
                    codigo="MENSUAL",
                    descripcion="Planilla Mensual",
                    dias=30,
                    periodicidad="mensual",
                )
                db.session.add(tipo)
            
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one_or_none()
            if not moneda:
                moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$")
                db.session.add(moneda)
            db.session.commit()

            # Create planilla for company 1
            planilla = Planilla(
                nombre="Planilla Company 1A",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
                empresa_id=empresa1.id,
            )
            db.session.add(planilla)

            # Create employee for company 2
            empleado = Empleado(
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010101-0001A-CROSS1",
                fecha_alta=date.today(),
                salario_base=Decimal("10000.00"),
                empresa_id=empresa2.id,
            )
            db.session.add(empleado)
            db.session.commit()

            # Try to assign employee to planilla (should fail)
            response = authenticated_client.post(
                f"/planilla/{planilla.id}/empleado/add",
                data={"empleado_id": empleado.id},
                follow_redirects=True,
            )

            # Should show error message
            assert response.status_code == 200
            assert "misma empresa" in response.data.decode("utf-8").lower()

            # Verify no association was created
            association = db.session.execute(
                db.select(PlanillaEmpleado).filter_by(
                    planilla_id=planilla.id, empleado_id=empleado.id
                )
            ).scalar_one_or_none()
            assert association is None

    def test_can_assign_employee_from_same_company(self, app, authenticated_client):
        """Test that employees from the same company can be assigned to a planilla."""
        with app.app_context():
            # Create company
            empresa = Empresa(
                codigo="EMP_CROSS_2",
                razon_social="Company 1",
                ruc="J0123456785",
            )
            db.session.add(empresa)

            # Create tipo_planilla and moneda - check if already exists
            tipo = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="MENSUAL")
            ).scalar_one_or_none()
            if not tipo:
                tipo = TipoPlanilla(
                    codigo="MENSUAL",
                    descripcion="Planilla Mensual",
                    dias=30,
                    periodicidad="mensual",
                )
                db.session.add(tipo)
            
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one_or_none()
            if not moneda:
                moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$")
                db.session.add(moneda)
            db.session.commit()

            # Create planilla for company
            planilla = Planilla(
                nombre="Planilla Company 1B",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
                empresa_id=empresa.id,
            )
            db.session.add(planilla)

            # Create employee for same company
            empleado = Empleado(
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010101-0001A-CROSS2",
                fecha_alta=date.today(),
                salario_base=Decimal("10000.00"),
                empresa_id=empresa.id,
            )
            db.session.add(empleado)
            db.session.commit()

            # Assign employee to planilla (should succeed)
            response = authenticated_client.post(
                f"/planilla/{planilla.id}/empleado/add",
                data={"empleado_id": empleado.id},
                follow_redirects=True,
            )

            # Should show success message
            assert response.status_code == 200
            assert "exitosamente" in response.data.decode("utf-8").lower()

            # Verify association was created
            association = db.session.execute(
                db.select(PlanillaEmpleado).filter_by(
                    planilla_id=planilla.id, empleado_id=empleado.id
                )
            ).scalar_one_or_none()
            assert association is not None

    def test_can_assign_employee_without_company_to_any_planilla(self, app, authenticated_client):
        """Test that employees without company can be assigned to any planilla."""
        with app.app_context():
            # Create company
            empresa = Empresa(
                codigo="EMP_CROSS_3",
                razon_social="Company 1",
                ruc="J0123456786",
            )
            db.session.add(empresa)

            # Create tipo_planilla and moneda - check if already exists
            tipo = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="MENSUAL")
            ).scalar_one_or_none()
            if not tipo:
                tipo = TipoPlanilla(
                    codigo="MENSUAL",
                    descripcion="Planilla Mensual",
                    dias=30,
                    periodicidad="mensual",
                )
                db.session.add(tipo)
            
            moneda = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one_or_none()
            if not moneda:
                moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$")
                db.session.add(moneda)
            db.session.commit()

            # Create planilla with company
            planilla = Planilla(
                nombre="Planilla Company 1C",
                tipo_planilla_id=tipo.id,
                moneda_id=moneda.id,
                empresa_id=empresa.id,
            )
            db.session.add(planilla)

            # Create employee without company
            empleado = Empleado(
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010101-0001A-CROSS3",
                fecha_alta=date.today(),
                salario_base=Decimal("10000.00"),
            )
            db.session.add(empleado)
            db.session.commit()

            # Assign employee to planilla (should succeed)
            response = authenticated_client.post(
                f"/planilla/{planilla.id}/empleado/add",
                data={"empleado_id": empleado.id},
                follow_redirects=True,
            )

            # Should show success message
            assert response.status_code == 200
            assert "exitosamente" in response.data.decode("utf-8").lower()

            # Verify association was created
            association = db.session.execute(
                db.select(PlanillaEmpleado).filter_by(
                    planilla_id=planilla.id, empleado_id=empleado.id
                )
            ).scalar_one_or_none()
            assert association is not None
