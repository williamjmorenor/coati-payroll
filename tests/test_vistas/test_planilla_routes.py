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
"""Comprehensive tests for planilla (payroll) routes."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from tests.helpers.auth import login_user


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def tipo_planilla(app, db_session):
    """Create a TipoPlanilla for testing."""
    with app.app_context():
        from coati_payroll.model import TipoPlanilla

        tipo = TipoPlanilla(
            codigo="MENSUAL",
            descripcion="Planilla Mensual",
            periodicidad="mensual",
            activo=True,
        )
        db_session.add(tipo)
        db_session.commit()
        db_session.refresh(tipo)
        return tipo


@pytest.fixture
def moneda(app, db_session):
    """Create a Moneda for testing."""
    with app.app_context():
        from coati_payroll.model import Moneda

        moneda = Moneda(codigo="USD", nombre="Dolar", simbolo="$", activo=True)
        db_session.add(moneda)
        db_session.commit()
        db_session.refresh(moneda)
        return moneda


@pytest.fixture
def empresa(app, db_session):
    """Create an Empresa for testing."""
    with app.app_context():
        from coati_payroll.model import Empresa

        empresa = Empresa(
            codigo="TEST",
            razon_social="Test Company S.A.",
            ruc="123456789",
            activo=True,
        )
        db_session.add(empresa)
        db_session.commit()
        db_session.refresh(empresa)
        return empresa


@pytest.fixture
def planilla(app, db_session, tipo_planilla, moneda, empresa, admin_user):
    """Create a Planilla for testing."""
    with app.app_context():
        from coati_payroll.model import Planilla

        planilla = Planilla(
            nombre="Test Planilla",
            descripcion="Planilla de prueba",
            tipo_planilla_id=tipo_planilla.id,
            moneda_id=moneda.id,
            empresa_id=empresa.id,
            periodo_fiscal_inicio=date(2024, 1, 1),
            periodo_fiscal_fin=date(2024, 12, 31),
            prioridad_prestamos=250,
            prioridad_adelantos=251,
            aplicar_prestamos_automatico=True,
            aplicar_adelantos_automatico=True,
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(planilla)
        db_session.commit()
        db_session.refresh(planilla)
        return planilla


@pytest.fixture
def empleado(app, db_session, empresa):
    """Create an Empleado for testing."""
    with app.app_context():
        from tests.factories.employee_factory import create_employee

        empleado = create_employee(
            db_session,
            empresa.id,
            codigo="EMP001",
            primer_nombre="Juan",
            primer_apellido="Perez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("1000.00"),
        )
        return empleado


@pytest.fixture
def percepcion(app, db_session):
    """Create a Percepcion for testing."""
    with app.app_context():
        from coati_payroll.model import Percepcion

        percepcion = Percepcion(
            codigo="BONO",
            nombre="Bono Mensual",
            descripcion="Bono mensual por desempeño",
            formula_tipo="fijo",
            activo=True,
        )
        db_session.add(percepcion)
        db_session.commit()
        db_session.refresh(percepcion)
        return percepcion


@pytest.fixture
def deduccion(app, db_session):
    """Create a Deduccion for testing."""
    with app.app_context():
        from coati_payroll.model import Deduccion

        deduccion = Deduccion(
            codigo="INSS",
            nombre="INSS Laboral",
            descripcion="Seguro Social Laboral",
            formula_tipo="porcentaje",
            activo=True,
        )
        db_session.add(deduccion)
        db_session.commit()
        db_session.refresh(deduccion)
        return deduccion


@pytest.fixture
def prestacion(app, db_session):
    """Create a Prestacion for testing."""
    with app.app_context():
        from coati_payroll.model import Prestacion

        prestacion = Prestacion(
            codigo="VAC",
            nombre="Vacaciones",
            descripcion="Acumulación de vacaciones",
            formula_tipo="porcentaje_salario",
            activo=True,
        )
        db_session.add(prestacion)
        db_session.commit()
        db_session.refresh(prestacion)
        return prestacion


@pytest.fixture
def regla_calculo(app, db_session):
    """Create a ReglaCalculo for testing."""
    with app.app_context():
        from coati_payroll.model import ReglaCalculo

        regla = ReglaCalculo(
            codigo="IR",
            nombre="Impuesto sobre la Renta",
            descripcion="Cálculo de IR",
            vigente_desde=date(2024, 1, 1),
            activo=True,
        )
        db_session.add(regla)
        db_session.commit()
        db_session.refresh(regla)
        return regla


# ============================================================================
# AUTHENTICATION & AUTHORIZATION TESTS
# ============================================================================


def test_planilla_index_requires_authentication(app, client, db_session):
    """Test that planilla index requires authentication."""
    with app.app_context():
        response = client.get("/planilla/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_index_for_admin(app, client, admin_user, db_session):
    """Test that admin can access planilla index."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get("/planilla/")
        assert response.status_code == 200


def test_planilla_new_requires_authentication(app, client, db_session):
    """Test that creating a new planilla requires authentication."""
    with app.app_context():
        response = client.get("/planilla/new", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_new_requires_write_access(app, client, db_session):
    """Test that creating a new planilla requires write access."""
    with app.app_context():
        from coati_payroll.enums import TipoUsuario
        from tests.factories.user_factory import create_user

        # Create AUDIT user (read-only)
        audit_user = create_user(db_session, "auditor", "password", tipo=TipoUsuario.AUDIT)
        login_user(client, audit_user.usuario, "password")

        response = client.get("/planilla/new", follow_redirects=False)
        # Should not allow access (403 or redirect)
        assert response.status_code in [302, 403]


def test_planilla_edit_requires_authentication(app, client, db_session):
    """Test that editing a planilla requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/edit", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_config_requires_authentication(app, client, db_session):
    """Test that accessing planilla config requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/config", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_nomina_list_requires_authentication(app, client, db_session):
    """Test that nomina list requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/nominas", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_nomina_view_requires_authentication(app, client, db_session):
    """Test that viewing nomina requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/nomina/888", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_ejecutar_requires_authentication(app, client, db_session):
    """Test that executing planilla requires authentication."""
    with app.app_context():
        response = client.post("/planilla/999/ejecutar", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


# ============================================================================
# PLANILLA CRUD TESTS
# ============================================================================


def test_planilla_new_get_displays_form(app, client, admin_user, db_session, tipo_planilla, moneda):
    """Test that GET /planilla/new displays the form."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get("/planilla/new")
        assert response.status_code == 200
        assert b"nombre" in response.data or b"Nombre" in response.data


def test_planilla_new_post_creates_planilla(
    app, client, admin_user, db_session, tipo_planilla, moneda, empresa
):
    """Test that POST /planilla/new creates a new planilla."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        data = {
            "nombre": "Nueva Planilla",
            "descripcion": "Descripción de prueba",
            "tipo_planilla_id": tipo_planilla.id,
            "moneda_id": moneda.id,
            "empresa_id": empresa.id,
            "periodo_fiscal_inicio": "2024-01-01",
            "periodo_fiscal_fin": "2024-12-31",
            "prioridad_prestamos": 250,
            "prioridad_adelantos": 251,
            "aplicar_prestamos_automatico": True,
            "aplicar_adelantos_automatico": True,
            "activo": True,
        }

        response = client.post("/planilla/new", data=data, follow_redirects=False)
        assert response.status_code == 302  # Redirect after successful creation

        # Verify planilla was created
        from coati_payroll.model import Planilla, db

        planilla = db_session.execute(
            db.select(Planilla).filter_by(nombre="Nueva Planilla")
        ).scalar_one_or_none()
        assert planilla is not None
        assert planilla.descripcion == "Descripción de prueba"


def test_planilla_edit_get_displays_form(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/edit displays the edit form."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/edit")
        assert response.status_code == 200
        assert planilla.nombre.encode() in response.data


def test_planilla_edit_post_updates_planilla(app, client, admin_user, db_session, planilla):
    """Test that POST /planilla/<id>/edit updates the planilla."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        planilla_id = planilla.id
        data = {
            "nombre": "Planilla Actualizada",
            "descripcion": planilla.descripcion,
            "tipo_planilla_id": planilla.tipo_planilla_id,
            "moneda_id": planilla.moneda_id,
            "empresa_id": planilla.empresa_id,
            "periodo_fiscal_inicio": "2024-01-01",
            "periodo_fiscal_fin": "2024-12-31",
            "prioridad_prestamos": 250,
            "prioridad_adelantos": 251,
            "aplicar_prestamos_automatico": True,
            "aplicar_adelantos_automatico": True,
            "activo": True,
        }

        response = client.post(f"/planilla/{planilla_id}/edit", data=data, follow_redirects=False)
        assert response.status_code == 302

        # Fetch and verify update
        from coati_payroll.model import Planilla

        updated_planilla = db_session.get(Planilla, planilla_id)
        assert updated_planilla.nombre == "Planilla Actualizada"


def test_planilla_config_displays_summary(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/config displays configuration summary."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/config")
        assert response.status_code == 200
        assert planilla.nombre.encode() in response.data


def test_planilla_delete_removes_planilla(app, client, admin_user, db_session, planilla):
    """Test that POST /planilla/<id>/delete removes the planilla."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        planilla_id = planilla.id

        response = client.post(f"/planilla/{planilla_id}/delete", follow_redirects=False)
        assert response.status_code == 302

        # Verify planilla was deleted
        from coati_payroll.model import Planilla

        deleted = db_session.get(Planilla, planilla_id)
        assert deleted is None


# ============================================================================
# CONFIGURATION PAGE TESTS
# ============================================================================


def test_config_empleados_displays(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/config/empleados displays employee config."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/config/empleados")
        assert response.status_code == 200


def test_config_percepciones_displays(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/config/percepciones displays perception config."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/config/percepciones")
        assert response.status_code == 200


def test_config_deducciones_displays(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/config/deducciones displays deduction config."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/config/deducciones")
        assert response.status_code == 200


def test_config_prestaciones_displays(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/config/prestaciones displays benefits config."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/config/prestaciones")
        assert response.status_code == 200


def test_config_reglas_displays(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/config/reglas displays calculation rules config."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/config/reglas")
        assert response.status_code == 200


# ============================================================================
# ASSOCIATION MANAGEMENT TESTS
# ============================================================================


def test_add_empleado_to_planilla(app, client, admin_user, db_session, planilla, empleado):
    """Test that POST /planilla/<id>/empleado/add adds an employee."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        data = {"empleado_id": empleado.id}
        response = client.post(f"/planilla/{planilla.id}/empleado/add", data=data, follow_redirects=False)
        assert response.status_code == 302

        # Verify association was created
        from coati_payroll.model import PlanillaEmpleado, db

        association = db_session.execute(
            db.select(PlanillaEmpleado).filter_by(planilla_id=planilla.id, empleado_id=empleado.id)
        ).scalar_one_or_none()
        assert association is not None


def test_remove_empleado_from_planilla(app, client, admin_user, db_session, planilla, empleado):
    """Test that POST /planilla/<id>/empleado/<assoc_id>/remove removes an employee."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # First add the employee
        from coati_payroll.model import PlanillaEmpleado

        association = PlanillaEmpleado(
            planilla_id=planilla.id,
            empleado_id=empleado.id,
            fecha_inicio=date.today(),
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()
        db_session.refresh(association)

        # Now remove it
        response = client.post(
            f"/planilla/{planilla.id}/empleado/{association.id}/remove", follow_redirects=False
        )
        assert response.status_code == 302

        # Verify it was removed
        removed = db_session.get(PlanillaEmpleado, association.id)
        assert removed is None


def test_add_percepcion_to_planilla(app, client, admin_user, db_session, planilla, percepcion):
    """Test that POST /planilla/<id>/percepcion/add adds a perception."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        data = {"percepcion_id": percepcion.id, "orden": 1}
        response = client.post(f"/planilla/{planilla.id}/percepcion/add", data=data, follow_redirects=False)
        assert response.status_code == 302

        # Verify association was created
        from coati_payroll.model import PlanillaIngreso, db

        association = db_session.execute(
            db.select(PlanillaIngreso).filter_by(planilla_id=planilla.id, percepcion_id=percepcion.id)
        ).scalar_one_or_none()
        assert association is not None


def test_remove_percepcion_from_planilla(app, client, admin_user, db_session, planilla, percepcion):
    """Test that POST /planilla/<id>/percepcion/<assoc_id>/remove removes a perception."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # First add the perception
        from coati_payroll.model import PlanillaIngreso

        association = PlanillaIngreso(
            planilla_id=planilla.id,
            percepcion_id=percepcion.id,
            orden=1,
            editable=True,
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()
        db_session.refresh(association)

        # Now remove it
        response = client.post(
            f"/planilla/{planilla.id}/percepcion/{association.id}/remove", follow_redirects=False
        )
        assert response.status_code == 302

        # Verify it was removed
        removed = db_session.get(PlanillaIngreso, association.id)
        assert removed is None


def test_add_deduccion_to_planilla(app, client, admin_user, db_session, planilla, deduccion):
    """Test that POST /planilla/<id>/deduccion/add adds a deduction."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        data = {"deduccion_id": deduccion.id, "prioridad": 100, "es_obligatoria": "on"}
        response = client.post(f"/planilla/{planilla.id}/deduccion/add", data=data, follow_redirects=False)
        assert response.status_code == 302

        # Verify association was created
        from coati_payroll.model import PlanillaDeduccion, db

        association = db_session.execute(
            db.select(PlanillaDeduccion).filter_by(planilla_id=planilla.id, deduccion_id=deduccion.id)
        ).scalar_one_or_none()
        assert association is not None
        assert association.prioridad == 100


def test_remove_deduccion_from_planilla(app, client, admin_user, db_session, planilla, deduccion):
    """Test that POST /planilla/<id>/deduccion/<assoc_id>/remove removes a deduction."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # First add the deduction
        from coati_payroll.model import PlanillaDeduccion

        association = PlanillaDeduccion(
            planilla_id=planilla.id,
            deduccion_id=deduccion.id,
            prioridad=100,
            es_obligatoria=True,
            editable=True,
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()
        db_session.refresh(association)

        # Now remove it
        response = client.post(
            f"/planilla/{planilla.id}/deduccion/{association.id}/remove", follow_redirects=False
        )
        assert response.status_code == 302

        # Verify it was removed
        removed = db_session.get(PlanillaDeduccion, association.id)
        assert removed is None


def test_update_deduccion_priority(app, client, admin_user, db_session, planilla, deduccion):
    """Test that POST /planilla/<id>/deduccion/<assoc_id>/update-priority updates priority."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # First add the deduction
        from coati_payroll.model import PlanillaDeduccion

        association = PlanillaDeduccion(
            planilla_id=planilla.id,
            deduccion_id=deduccion.id,
            prioridad=100,
            es_obligatoria=True,
            editable=True,
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()
        db_session.refresh(association)

        # Update priority
        data = {"prioridad": 200}
        response = client.post(
            f"/planilla/{planilla.id}/deduccion/{association.id}/update-priority",
            data=data,
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify priority was updated
        db_session.refresh(association)
        assert association.prioridad == 200


def test_add_prestacion_to_planilla(app, client, admin_user, db_session, planilla, prestacion):
    """Test that POST /planilla/<id>/prestacion/add adds a benefit."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        data = {"prestacion_id": prestacion.id, "orden": 1}
        response = client.post(f"/planilla/{planilla.id}/prestacion/add", data=data, follow_redirects=False)
        assert response.status_code == 302

        # Verify association was created
        from coati_payroll.model import PlanillaPrestacion, db

        association = db_session.execute(
            db.select(PlanillaPrestacion).filter_by(
                planilla_id=planilla.id, prestacion_id=prestacion.id
            )
        ).scalar_one_or_none()
        assert association is not None


def test_remove_prestacion_from_planilla(app, client, admin_user, db_session, planilla, prestacion):
    """Test that POST /planilla/<id>/prestacion/<assoc_id>/remove removes a benefit."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # First add the benefit
        from coati_payroll.model import PlanillaPrestacion

        association = PlanillaPrestacion(
            planilla_id=planilla.id,
            prestacion_id=prestacion.id,
            orden=1,
            editable=True,
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()
        db_session.refresh(association)

        # Now remove it
        response = client.post(
            f"/planilla/{planilla.id}/prestacion/{association.id}/remove", follow_redirects=False
        )
        assert response.status_code == 302

        # Verify it was removed
        removed = db_session.get(PlanillaPrestacion, association.id)
        assert removed is None


def test_add_regla_to_planilla(app, client, admin_user, db_session, planilla, regla_calculo):
    """Test that POST /planilla/<id>/regla/add adds a calculation rule."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        data = {"regla_calculo_id": regla_calculo.id, "orden": 1}
        response = client.post(f"/planilla/{planilla.id}/regla/add", data=data, follow_redirects=False)
        assert response.status_code == 302

        # Verify association was created
        from coati_payroll.model import PlanillaReglaCalculo, db

        association = db_session.execute(
            db.select(PlanillaReglaCalculo).filter_by(
                planilla_id=planilla.id, regla_calculo_id=regla_calculo.id
            )
        ).scalar_one_or_none()
        assert association is not None


def test_remove_regla_from_planilla(app, client, admin_user, db_session, planilla, regla_calculo):
    """Test that POST /planilla/<id>/regla/<assoc_id>/remove removes a calculation rule."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # First add the rule
        from coati_payroll.model import PlanillaReglaCalculo

        association = PlanillaReglaCalculo(
            planilla_id=planilla.id,
            regla_calculo_id=regla_calculo.id,
            orden=1,
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()
        db_session.refresh(association)

        # Now remove it
        response = client.post(
            f"/planilla/{planilla.id}/regla/{association.id}/remove", follow_redirects=False
        )
        assert response.status_code == 302

        # Verify it was removed
        removed = db_session.get(PlanillaReglaCalculo, association.id)
        assert removed is None


# ============================================================================
# NOMINA EXECUTION TESTS
# ============================================================================


def test_ejecutar_nomina_get_displays_form(app, client, admin_user, db_session, planilla, empleado):
    """Test that GET /planilla/<id>/ejecutar displays the execution form."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Add employee to planilla
        from coati_payroll.model import PlanillaEmpleado

        association = PlanillaEmpleado(
            planilla_id=planilla.id,
            empleado_id=empleado.id,
            fecha_inicio=date.today(),
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()

        response = client.get(f"/planilla/{planilla.id}/ejecutar")
        assert response.status_code == 200


def test_listar_nominas_displays_list(app, client, admin_user, db_session, planilla):
    """Test that GET /planilla/<id>/nominas displays nomina list."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/nominas")
        assert response.status_code == 200


# ============================================================================
# NOVEDADES (NOVELTIES) CRUD TESTS
# ============================================================================


@pytest.fixture
def nomina(app, db_session, planilla, admin_user):
    """Create a Nomina for testing novedades."""
    with app.app_context():
        from coati_payroll.model import Nomina

        nomina = Nomina(
            planilla_id=planilla.id,
            periodo_inicio=date.today(),
            periodo_fin=date.today() + timedelta(days=14),
            generado_por=admin_user.usuario,
            estado="generado",
        )
        db_session.add(nomina)
        db_session.commit()
        db_session.refresh(nomina)
        return nomina


@pytest.fixture
def nomina_empleado(app, db_session, nomina, empleado):
    """Create a NominaEmpleado for testing novedades."""
    with app.app_context():
        from coati_payroll.model import NominaEmpleado

        nomina_empleado = NominaEmpleado(
            nomina_id=nomina.id,
            empleado_id=empleado.id,
            salario_bruto=Decimal("1000.00"),
            total_ingresos=Decimal("1000.00"),
            total_deducciones=Decimal("100.00"),
            salario_neto=Decimal("900.00"),
            sueldo_base_historico=Decimal("1000.00"),
        )
        db_session.add(nomina_empleado)
        db_session.commit()
        db_session.refresh(nomina_empleado)
        return nomina_empleado


def test_listar_novedades_displays(app, client, admin_user, db_session, planilla, nomina, empleado):
    """Test that GET /planilla/<id>/nomina/<nomina_id>/novedades displays novedades list."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Add employee to planilla
        from coati_payroll.model import PlanillaEmpleado

        association = PlanillaEmpleado(
            planilla_id=planilla.id,
            empleado_id=empleado.id,
            fecha_inicio=date.today(),
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(association)
        db_session.commit()

        response = client.get(f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades")
        assert response.status_code == 200


def test_nueva_novedad_get_displays_form(
    app, client, admin_user, db_session, planilla, nomina, nomina_empleado
):
    """Test that GET /planilla/<id>/nomina/<nomina_id>/novedades/new displays form."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get(f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/new")
        assert response.status_code == 200


def test_nueva_novedad_post_creates_novedad(
    app, client, admin_user, db_session, planilla, nomina, nomina_empleado, percepcion
):
    """Test that POST /planilla/<id>/nomina/<nomina_id>/novedades/new creates a novedad."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        data = {
            "empleado_id": nomina_empleado.empleado_id,
            "codigo_concepto": "BONO",
            "tipo_concepto": "percepcion",
            "percepcion_id": percepcion.id,
            "tipo_valor": "monto",
            "valor_cantidad": 500,
            "fecha_novedad": date.today().isoformat(),
        }

        response = client.post(
            f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/new",
            data=data,
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify novedad was created
        from coati_payroll.model import NominaNovedad, db

        novedad = db_session.execute(
            db.select(NominaNovedad).filter_by(nomina_id=nomina.id, codigo_concepto="BONO")
        ).scalar_one_or_none()
        assert novedad is not None
        assert novedad.empleado_id == nomina_empleado.empleado_id


def test_nueva_novedad_blocked_for_applied_nomina(
    app, client, admin_user, db_session, planilla, empleado
):
    """Test that novedades cannot be added to an applied nomina."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create a nomina with "aplicado" state
        from coati_payroll.model import Nomina, NominaEmpleado

        nomina = Nomina(
            planilla_id=planilla.id,
            periodo_inicio=date.today(),
            periodo_fin=date.today() + timedelta(days=14),
            generado_por=admin_user.usuario,
            estado="aplicado",  # Set to aplicado from the start
        )
        db_session.add(nomina)
        db_session.commit()
        db_session.refresh(nomina)

        # Create nomina empleado
        nomina_empleado = NominaEmpleado(
            nomina_id=nomina.id,
            empleado_id=empleado.id,
            salario_bruto=Decimal("1000.00"),
            total_ingresos=Decimal("1000.00"),
            total_deducciones=Decimal("100.00"),
            salario_neto=Decimal("900.00"),
            sueldo_base_historico=Decimal("1000.00"),
        )
        db_session.add(nomina_empleado)
        db_session.commit()

        response = client.get(
            f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/new",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "No se pueden agregar novedades".encode() in response.data or "aplicada".encode() in response.data


def test_editar_novedad_get_displays_form(
    app, client, admin_user, db_session, planilla, nomina, nomina_empleado, percepcion
):
    """Test that GET /planilla/<id>/nomina/<nomina_id>/novedades/<novedad_id>/edit displays form."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create a novedad first
        from coati_payroll.model import NominaNovedad
        from decimal import Decimal

        novedad = NominaNovedad(
            nomina_id=nomina.id,
            empleado_id=nomina_empleado.empleado_id,
            codigo_concepto="BONO",
            tipo_valor="monto",
            valor_cantidad=Decimal("500.00"),
            fecha_novedad=date.today(),
            percepcion_id=percepcion.id,
            creado_por=admin_user.usuario,
        )
        db_session.add(novedad)
        db_session.commit()
        db_session.refresh(novedad)

        response = client.get(f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/{novedad.id}/edit")
        assert response.status_code == 200


def test_editar_novedad_post_updates_novedad(
    app, client, admin_user, db_session, planilla, nomina, nomina_empleado, percepcion
):
    """Test that POST /planilla/<id>/nomina/<nomina_id>/novedades/<novedad_id>/edit updates novedad."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create a novedad first
        from coati_payroll.model import NominaNovedad
        from decimal import Decimal

        novedad = NominaNovedad(
            nomina_id=nomina.id,
            empleado_id=nomina_empleado.empleado_id,
            codigo_concepto="BONO",
            tipo_valor="monto",
            valor_cantidad=Decimal("500.00"),
            fecha_novedad=date.today(),
            percepcion_id=percepcion.id,
            creado_por=admin_user.usuario,
        )
        db_session.add(novedad)
        db_session.commit()
        db_session.refresh(novedad)

        novedad_id = novedad.id

        # Update the novedad
        data = {
            "empleado_id": nomina_empleado.empleado_id,
            "codigo_concepto": "BONO_ACT",
            "tipo_concepto": "percepcion",
            "percepcion_id": percepcion.id,
            "tipo_valor": "monto",
            "valor_cantidad": 750,
            "fecha_novedad": date.today().isoformat(),
        }

        response = client.post(
            f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/{novedad_id}/edit",
            data=data,
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify novedad was updated
        updated_novedad = db_session.get(NominaNovedad, novedad_id)
        assert updated_novedad.codigo_concepto == "BONO_ACT"
        assert updated_novedad.valor_cantidad == Decimal("750.00")


def test_editar_novedad_blocked_for_applied_nomina(
    app, client, admin_user, db_session, planilla, empleado, percepcion
):
    """Test that novedades cannot be edited in an applied nomina."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create a nomina with "aplicado" state
        from coati_payroll.model import Nomina, NominaEmpleado, NominaNovedad

        nomina = Nomina(
            planilla_id=planilla.id,
            periodo_inicio=date.today(),
            periodo_fin=date.today() + timedelta(days=14),
            generado_por=admin_user.usuario,
            estado="aplicado",  # Set to aplicado from the start
        )
        db_session.add(nomina)
        db_session.commit()

        # Create nomina empleado
        nomina_empleado = NominaEmpleado(
            nomina_id=nomina.id,
            empleado_id=empleado.id,
            salario_bruto=Decimal("1000.00"),
            total_ingresos=Decimal("1000.00"),
            total_deducciones=Decimal("100.00"),
            salario_neto=Decimal("900.00"),
            sueldo_base_historico=Decimal("1000.00"),
        )
        db_session.add(nomina_empleado)
        db_session.commit()

        # Create a novedad
        novedad = NominaNovedad(
            nomina_id=nomina.id,
            empleado_id=nomina_empleado.empleado_id,
            codigo_concepto="BONO",
            tipo_valor="monto",
            valor_cantidad=Decimal("500.00"),
            fecha_novedad=date.today(),
            percepcion_id=percepcion.id,
            creado_por=admin_user.usuario,
        )
        db_session.add(novedad)
        db_session.commit()
        db_session.refresh(novedad)

        response = client.get(
            f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/{novedad.id}/edit",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "No se pueden editar novedades".encode() in response.data or "aplicada".encode() in response.data


def test_eliminar_novedad_removes_novedad(
    app, client, admin_user, db_session, planilla, nomina, nomina_empleado, percepcion
):
    """Test that POST /planilla/<id>/nomina/<nomina_id>/novedades/<novedad_id>/delete removes novedad."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create a novedad
        from coati_payroll.model import NominaNovedad
        from decimal import Decimal

        novedad = NominaNovedad(
            nomina_id=nomina.id,
            empleado_id=nomina_empleado.empleado_id,
            codigo_concepto="BONO",
            tipo_valor="monto",
            valor_cantidad=Decimal("500.00"),
            fecha_novedad=date.today(),
            percepcion_id=percepcion.id,
            creado_por=admin_user.usuario,
        )
        db_session.add(novedad)
        db_session.commit()
        db_session.refresh(novedad)

        novedad_id = novedad.id

        response = client.post(
            f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/{novedad_id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify novedad was deleted
        deleted = db_session.get(NominaNovedad, novedad_id)
        assert deleted is None


def test_eliminar_novedad_blocked_for_applied_nomina(
    app, client, admin_user, db_session, planilla, empleado, percepcion
):
    """Test that novedades cannot be deleted from an applied nomina."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create a nomina with "aplicado" state
        from coati_payroll.model import Nomina, NominaEmpleado, NominaNovedad

        nomina = Nomina(
            planilla_id=planilla.id,
            periodo_inicio=date.today(),
            periodo_fin=date.today() + timedelta(days=14),
            generado_por=admin_user.usuario,
            estado="aplicado",  # Set to aplicado from the start
        )
        db_session.add(nomina)
        db_session.commit()

        # Create nomina empleado
        nomina_empleado = NominaEmpleado(
            nomina_id=nomina.id,
            empleado_id=empleado.id,
            salario_bruto=Decimal("1000.00"),
            total_ingresos=Decimal("1000.00"),
            total_deducciones=Decimal("100.00"),
            salario_neto=Decimal("900.00"),
            sueldo_base_historico=Decimal("1000.00"),
        )
        db_session.add(nomina_empleado)
        db_session.commit()

        # Create a novedad
        novedad = NominaNovedad(
            nomina_id=nomina.id,
            empleado_id=nomina_empleado.empleado_id,
            codigo_concepto="BONO",
            tipo_valor="monto",
            valor_cantidad=Decimal("500.00"),
            fecha_novedad=date.today(),
            percepcion_id=percepcion.id,
            creado_por=admin_user.usuario,
        )
        db_session.add(novedad)
        db_session.commit()
        db_session.refresh(novedad)

        response = client.post(
            f"/planilla/{planilla.id}/nomina/{nomina.id}/novedades/{novedad.id}/delete",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "No se pueden eliminar novedades".encode() in response.data or "aplicada".encode() in response.data
