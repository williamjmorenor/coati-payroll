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
"""Pytest configuration and fixtures for Coati Payroll tests."""

import pytest
import sys

# Ensure test mode is active
sys.modules["pytest"]


@pytest.fixture(scope="module")
def app():
    """Create and configure a new app instance for each test module.

    Using module scope to avoid SQLAlchemy metadata conflicts with session table.
    """
    import os
    from coati_payroll import create_app
    from coati_payroll.model import db

    # Set environment variable to use filesystem session before app creation
    os.environ["SESSION_REDIS_URL"] = ""

    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    }

    app = create_app(test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def sample_tax_schema():
    """Sample tax calculation schema for testing."""
    return {
        "meta": {
            "name": "Test IR",
            "jurisdiction": "Test",
            "reference_currency": "USD",
            "version": "1.0.0",
        },
        "inputs": [
            {"name": "salario_mensual", "type": "decimal", "default": 0},
            {"name": "inss_laboral", "type": "decimal", "default": 0},
        ],
        "steps": [
            {
                "name": "salario_neto",
                "type": "calculation",
                "formula": "salario_mensual - inss_laboral",
            },
            {
                "name": "impuesto",
                "type": "tax_lookup",
                "table": "tabla_ir",
                "input": "salario_neto",
            },
        ],
        "tax_tables": {
            "tabla_ir": [
                {"min": 0, "max": 1000, "rate": 0, "fixed": 0, "over": 0},
                {"min": 1000.01, "max": 5000, "rate": 0.10, "fixed": 0, "over": 1000},
                {"min": 5000.01, "max": None, "rate": 0.20, "fixed": 400, "over": 5000},
            ]
        },
        "output": "impuesto",
    }


@pytest.fixture
def simple_formula_schema():
    """Simple formula schema for basic tests."""
    return {
        "inputs": [
            {"name": "base", "type": "decimal", "default": 100},
            {"name": "rate", "type": "decimal", "default": 0.1},
        ],
        "steps": [
            {
                "name": "result",
                "type": "calculation",
                "formula": "base * rate",
            },
        ],
        "output": "result",
    }


@pytest.fixture
def authenticated_client(app, client):
    """Create an authenticated test client with a logged-in user.

    This fixture creates a test user (if one doesn't exist) and logs them in,
    returning a test client that can access protected routes.
    """
    with app.app_context():
        from coati_payroll.model import Usuario, db
        from coati_payroll.auth import proteger_passwd

        # Check if the test user already exists (from a previous test in the module)
        existing_user = db.session.execute(
            db.select(Usuario).filter_by(usuario="testuser")
        ).scalar_one_or_none()

        if not existing_user:
            # Create a test user
            user = Usuario()
            user.usuario = "testuser"
            user.acceso = proteger_passwd("testpassword")
            user.nombre = "Test"
            user.apellido = "User"
            user.tipo = "admin"
            user.activo = True
            db.session.add(user)
            db.session.commit()

    # Log in the user
    client.post(
        "/auth/login",
        data={"email": "testuser", "password": "testpassword"},
        follow_redirects=True,
    )
    return client
