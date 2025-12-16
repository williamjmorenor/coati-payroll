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
"""Tests for application initialization and basic functionality."""


def test_app_is_created(app):
    """
    Test that the Flask application is created successfully.

    Setup:
        - Use the app fixture

    Action:
        - Verify app exists and is in testing mode

    Verification:
        - App is not None
        - TESTING flag is True
    """
    assert app is not None
    assert app.config["TESTING"] is True


def test_database_is_sqlite_memory(app):
    """
    Test that the database is configured to use SQLite in memory.

    Setup:
        - Use the app fixture

    Action:
        - Check the database URI

    Verification:
        - Database URI uses SQLite in-memory
    """
    assert "sqlite:///:memory:" in app.config["SQLALCHEMY_DATABASE_URI"]


def test_database_tables_exist(app, db_session):
    """
    Test that database tables are created.

    Setup:
        - Use app and db_session fixtures

    Action:
        - Query table names from database

    Verification:
        - Usuario table exists
        - Other essential tables exist
    """
    from coati_payroll.model import db

    with app.app_context():
        # Get all table names
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()

        # Verify essential tables exist
        assert "usuario" in tables
        assert "empresa" in tables
        assert "empleado" in tables


def test_csrf_is_disabled_in_testing(app):
    """
    Test that CSRF protection is disabled for testing.

    Setup:
        - Use the app fixture

    Action:
        - Check CSRF configuration

    Verification:
        - WTF_CSRF_ENABLED is False
    """
    assert app.config["WTF_CSRF_ENABLED"] is False


def test_session_isolation(app, db_session):
    """
    Test that each test has isolated database session.

    Setup:
        - Use app and db_session fixtures

    Action:
        - Create a user in the session
        - Don't commit

    Verification:
        - User exists in current session
        - Will be rolled back after test
    """
    from coati_payroll.model import Usuario
    from coati_payroll.auth import proteger_passwd

    with app.app_context():
        user = Usuario()
        user.usuario = "test-isolation"
        user.acceso = proteger_passwd("password")
        user.nombre = "Test"
        user.apellido = "Isolation"
        user.tipo = "user"
        user.activo = True

        db_session.add(user)
        db_session.flush()

        # Verify user exists in current session
        found = db_session.query(Usuario).filter_by(usuario="test-isolation").first()
        assert found is not None
        assert found.usuario == "test-isolation"
