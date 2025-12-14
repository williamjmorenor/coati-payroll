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
"""Tests for Role-Based Access Control (RBAC) functionality."""

from __future__ import annotations

import pytest
from flask import Flask

from coati_payroll import create_app
from coati_payroll.auth import proteger_passwd
from coati_payroll.enums import TipoUsuario
from coati_payroll.model import Usuario, Empresa, Empleado, Moneda, db


# Note: app and client fixtures are defined in conftest.py


@pytest.fixture
def admin_user(app):
    """Create an admin user."""
    with app.app_context():
        # Check if user already exists
        existing = db.session.execute(db.select(Usuario).filter_by(usuario="admin_test")).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin123"),
            nombre="Admin",
            apellido="User",
            tipo=TipoUsuario.ADMIN,
            activo=True,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        yield user_id

        # Cleanup
        user = db.session.get(Usuario, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()


@pytest.fixture
def hhrr_user(app):
    """Create an HR user."""
    with app.app_context():
        # Check if user already exists
        existing = db.session.execute(db.select(Usuario).filter_by(usuario="hhrr_test")).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        user = Usuario(
            usuario="hhrr_test",
            acceso=proteger_passwd("hhrr123"),
            nombre="HR",
            apellido="User",
            tipo=TipoUsuario.HHRR,
            activo=True,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        yield user_id

        # Cleanup
        user = db.session.get(Usuario, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()


@pytest.fixture
def audit_user(app):
    """Create an audit user."""
    with app.app_context():
        # Check if user already exists
        existing = db.session.execute(db.select(Usuario).filter_by(usuario="audit_test")).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        user = Usuario(
            usuario="audit_test",
            acceso=proteger_passwd("audit123"),
            nombre="Audit",
            apellido="User",
            tipo=TipoUsuario.AUDIT,
            activo=True,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        yield user_id

        # Cleanup
        user = db.session.get(Usuario, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()


@pytest.fixture
def sample_empresa(app):
    """Create a sample company."""
    with app.app_context():
        # Check if empresa already exists
        existing = db.session.execute(db.select(Empresa).filter_by(codigo="TEST-001")).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        empresa = Empresa(
            codigo="TEST-001",
            razon_social="Test Company",
            ruc="J0310000000000",
            activo=True,
        )
        db.session.add(empresa)
        db.session.commit()
        empresa_id = empresa.id

        yield empresa_id

        # Cleanup
        empresa = db.session.get(Empresa, empresa_id)
        if empresa:
            db.session.delete(empresa)
            db.session.commit()


@pytest.fixture
def sample_currency(app):
    """Create a sample currency."""
    with app.app_context():
        # Check if currency already exists
        existing = db.session.execute(db.select(Moneda).filter_by(codigo="NIO")).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        currency = Moneda(
            codigo="NIO",
            nombre="Córdoba",
            simbolo="C$",
            activo=True,
        )
        db.session.add(currency)
        db.session.commit()
        currency_id = currency.id

        yield currency_id

        # Cleanup
        currency = db.session.get(Moneda, currency_id)
        if currency:
            db.session.delete(currency)
            db.session.commit()


def login(client, username, password):
    """Helper function to login a user."""
    return client.post(
        "/auth/login",
        data={"email": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    """Helper function to logout."""
    return client.get("/auth/logout", follow_redirects=True)


class TestCompanyManagement:
    """Test company (empresa) management - admin only."""

    def test_admin_can_list_companies(self, app, client, admin_user, sample_empresa):
        """Admin users can list companies."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/empresa/")
            assert response.status_code == 200

    def test_admin_can_create_company(self, app, client, admin_user):
        """Admin users can create companies."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/empresa/new")
            assert response.status_code == 200

    def test_admin_can_edit_company(self, app, client, admin_user, sample_empresa):
        """Admin users can edit companies."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            empresa_id = sample_empresa
            response = client.get(f"/empresa/{empresa_id}/edit")
            assert response.status_code == 200

    def test_hhrr_can_list_companies(self, app, client, hhrr_user, sample_empresa):
        """HR users can list companies (read-only)."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/empresa/")
            assert response.status_code == 200

    def test_hhrr_cannot_create_company(self, app, client, hhrr_user):
        """HR users cannot create companies."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/empresa/new")
            assert response.status_code == 403

    def test_hhrr_cannot_edit_company(self, app, client, hhrr_user, sample_empresa):
        """HR users cannot edit companies."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            empresa_id = sample_empresa
            response = client.get(f"/empresa/{empresa_id}/edit")
            assert response.status_code == 403

    def test_audit_can_list_companies(self, app, client, audit_user, sample_empresa):
        """Audit users can list companies (read-only)."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/empresa/")
            assert response.status_code == 200

    def test_audit_cannot_create_company(self, app, client, audit_user):
        """Audit users cannot create companies."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/empresa/new")
            assert response.status_code == 403

    def test_audit_cannot_edit_company(self, app, client, audit_user, sample_empresa):
        """Audit users cannot edit companies."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            empresa_id = sample_empresa
            response = client.get(f"/empresa/{empresa_id}/edit")
            assert response.status_code == 403


class TestUserManagement:
    """Test user management - admin only."""

    def test_admin_can_list_users(self, app, client, admin_user):
        """Admin users can list other users."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/user/")
            assert response.status_code == 200

    def test_admin_can_create_user(self, app, client, admin_user):
        """Admin users can create new users."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/user/new")
            assert response.status_code == 200

    def test_hhrr_cannot_list_users(self, app, client, hhrr_user):
        """HR users cannot list users."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/user/")
            assert response.status_code == 403

    def test_hhrr_cannot_create_user(self, app, client, hhrr_user):
        """HR users cannot create users."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/user/new")
            assert response.status_code == 403

    def test_audit_cannot_list_users(self, app, client, audit_user):
        """Audit users cannot list users."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/user/")
            assert response.status_code == 403

    def test_audit_cannot_create_user(self, app, client, audit_user):
        """Audit users cannot create users."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/user/new")
            assert response.status_code == 403


class TestEmployeeManagement:
    """Test employee management - admin and HR can write, audit can read."""

    def test_admin_can_list_employees(self, app, client, admin_user):
        """Admin users can list employees."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/employee/")
            assert response.status_code == 200

    def test_admin_can_create_employee(self, app, client, admin_user):
        """Admin users can create employees."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/employee/new")
            assert response.status_code == 200

    def test_hhrr_can_list_employees(self, app, client, hhrr_user):
        """HR users can list employees."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/employee/")
            assert response.status_code == 200

    def test_hhrr_can_create_employee(self, app, client, hhrr_user):
        """HR users can create employees."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/employee/new")
            assert response.status_code == 200

    def test_audit_can_list_employees(self, app, client, audit_user):
        """Audit users can list employees (read-only)."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/employee/")
            assert response.status_code == 200

    def test_audit_cannot_create_employee(self, app, client, audit_user):
        """Audit users cannot create employees."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/employee/new")
            assert response.status_code == 403


class TestPayrollConcepts:
    """Test payroll concepts (perceptions, deductions, benefits) - admin and HR can write, audit can read."""

    def test_admin_can_list_perceptions(self, app, client, admin_user):
        """Admin users can list perceptions."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/percepciones/")
            assert response.status_code == 200

    def test_admin_can_create_perception(self, app, client, admin_user):
        """Admin users can create perceptions."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/percepciones/new")
            assert response.status_code == 200

    def test_hhrr_can_list_perceptions(self, app, client, hhrr_user):
        """HR users can list perceptions."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/percepciones/")
            assert response.status_code == 200

    def test_hhrr_can_create_perception(self, app, client, hhrr_user):
        """HR users can create perceptions."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/percepciones/new")
            assert response.status_code == 200

    def test_audit_can_list_perceptions(self, app, client, audit_user):
        """Audit users can list perceptions (read-only)."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/percepciones/")
            assert response.status_code == 200

    def test_audit_cannot_create_perception(self, app, client, audit_user):
        """Audit users cannot create perceptions."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/percepciones/new")
            assert response.status_code == 403

    def test_admin_can_list_deductions(self, app, client, admin_user):
        """Admin users can list deductions."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/deducciones/")
            assert response.status_code == 200

    def test_hhrr_can_list_deductions(self, app, client, hhrr_user):
        """HR users can list deductions."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/deducciones/")
            assert response.status_code == 200

    def test_audit_can_list_deductions(self, app, client, audit_user):
        """Audit users can list deductions (read-only)."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/deducciones/")
            assert response.status_code == 200

    def test_audit_cannot_create_deduction(self, app, client, audit_user):
        """Audit users cannot create deductions."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/deducciones/new")
            assert response.status_code == 403

    def test_admin_can_list_benefits(self, app, client, admin_user):
        """Admin users can list benefits."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/prestaciones/")
            assert response.status_code == 200

    def test_hhrr_can_list_benefits(self, app, client, hhrr_user):
        """HR users can list benefits."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/prestaciones/")
            assert response.status_code == 200

    def test_audit_can_list_benefits(self, app, client, audit_user):
        """Audit users can list benefits (read-only)."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/prestaciones/")
            assert response.status_code == 200

    def test_audit_cannot_create_benefit(self, app, client, audit_user):
        """Audit users cannot create benefits."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/prestaciones/new")
            assert response.status_code == 403


class TestLoanManagement:
    """Test loan/advance management - admin and HR can write, audit can read."""

    def test_admin_can_list_loans(self, app, client, admin_user):
        """Admin users can list loans."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/prestamo/")
            assert response.status_code == 200

    def test_admin_can_create_loan(self, app, client, admin_user):
        """Admin users can create loans."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/prestamo/new")
            assert response.status_code == 200

    def test_hhrr_can_list_loans(self, app, client, hhrr_user):
        """HR users can list loans."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/prestamo/")
            assert response.status_code == 200

    def test_hhrr_can_create_loan(self, app, client, hhrr_user):
        """HR users can create loans."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/prestamo/new")
            assert response.status_code == 200

    def test_audit_can_list_loans(self, app, client, audit_user):
        """Audit users can list loans (read-only)."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/prestamo/")
            assert response.status_code == 200

    def test_audit_cannot_create_loan(self, app, client, audit_user):
        """Audit users cannot create loans."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/prestamo/new")
            assert response.status_code == 403


class TestPlanillaManagement:
    """Test planilla (payroll) management - admin and HR can write, audit can read."""

    def test_admin_can_list_planillas(self, app, client, admin_user):
        """Admin users can list planillas."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/planilla/")
            assert response.status_code == 200

    def test_admin_can_create_planilla(self, app, client, admin_user):
        """Admin users can create planillas."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/planilla/new")
            assert response.status_code == 200

    def test_hhrr_can_list_planillas(self, app, client, hhrr_user):
        """HR users can list planillas."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/planilla/")
            assert response.status_code == 200

    def test_hhrr_can_create_planilla(self, app, client, hhrr_user):
        """HR users can create planillas."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/planilla/new")
            assert response.status_code == 200

    def test_audit_can_list_planillas(self, app, client, audit_user):
        """Audit users can list planillas (read-only)."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/planilla/")
            assert response.status_code == 200

    def test_audit_cannot_create_planilla(self, app, client, audit_user):
        """Audit users cannot create planillas."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/planilla/new")
            assert response.status_code == 403


class TestProfileAccess:
    """Test that all users can access their own profile."""

    def test_admin_can_access_profile(self, app, client, admin_user):
        """Admin users can access their profile."""
        with app.app_context():
            login(client, "admin_test", "admin123")
            response = client.get("/user/profile")
            assert response.status_code == 200

    def test_hhrr_can_access_profile(self, app, client, hhrr_user):
        """HR users can access their profile."""
        with app.app_context():
            login(client, "hhrr_test", "hhrr123")
            response = client.get("/user/profile")
            assert response.status_code == 200

    def test_audit_can_access_profile(self, app, client, audit_user):
        """Audit users can access their profile."""
        with app.app_context():
            login(client, "audit_test", "audit123")
            response = client.get("/user/profile")
            assert response.status_code == 200
