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
"""
Pytest configuration for parallel-safe testing.

This module provides fixtures for independent, isolated tests that can run
sequentially or in parallel using pytest-xdist.

Key principles:
- Each test gets its own SQLite in-memory database
- Each test runs in a transaction that is rolled back after completion
- No test depends on the state left by another test
- All fixtures use 'function' scope for maximum isolation
"""

import pytest
from cachelib.file import FileSystemCache
from sqlalchemy.orm import scoped_session, sessionmaker

from coati_payroll import create_app
from coati_payroll.model import db as _db


@pytest.fixture(scope="function")
def app():
    """
    Create Flask application for testing.

    Each test gets a fresh app instance with:
    - TESTING mode enabled
    - CSRF protection disabled
    - SQLite in-memory database
    - WTF_CSRF_ENABLED disabled for easier form testing
    - check_same_thread disabled for SQLite (allows parallel access within test)

    Returns:
        Flask: Configured Flask application instance
    """
    # Use a unique temp directory for each test to avoid session conflicts
    import tempfile

    session_dir = tempfile.mkdtemp()

    config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:?check_same_thread=False",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"check_same_thread": False}},
        "SECRET_KEY": "test-secret-key",
        "PRESERVE_CONTEXT_ON_EXCEPTION": False,
        "SESSION_TYPE": "cachelib",
        "SESSION_CACHELIB": FileSystemCache(cache_dir=session_dir, threshold=100),
    }

    app = create_app(config)

    # Tables are created by create_app -> ensure_database_initialized

    yield app

    # Cleanup
    with app.app_context():
        _db.session.remove()
        _db.drop_all()

    # Clean up session directory
    import shutil

    try:
        shutil.rmtree(session_dir)
    except Exception:
        pass


@pytest.fixture(scope="function")
def db_session(app):
    """
    Provide a database session for tests with automatic rollback.

    Each test runs within a transaction that is rolled back at the end,
    ensuring complete isolation between tests.

    Args:
        app: Flask application fixture

    Returns:
        Session: SQLAlchemy session that will be rolled back after test
    """
    with app.app_context():
        # Create a new connection that will be used for the test
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Bind the session to the connection
        # expire_on_commit=False prevents objects from being detached after commit
        session = scoped_session(sessionmaker(bind=connection, expire_on_commit=False))

        # Replace the default session with our transactional session
        _db.session = session

        # Disable Flask-SQLAlchemy's automatic session removal on teardown.
        # The default teardown handler calls db.session.remove(), which discards
        # the scoped session after each request. That detaches model instances
        # created in the test before the test can refresh them, triggering
        # "Instance ... is not persistent within this Session" errors. For the
        # isolated in-memory DB used in tests we keep the session alive for the
        # whole test and let the fixture clean it up explicitly.
        try:
            app.teardown_appcontext_funcs = [
                func for func in app.teardown_appcontext_funcs if getattr(func, "__name__", "") != "shutdown_session"
            ]
            # Also neutralize any remaining teardown calls to session.remove()
            session.remove = lambda: None
        except Exception:
            pass

        # IMPORTANT: For SQLite in-memory databases, schema is per-connection.
        # Ensure tables exist on this connection, otherwise tests will see
        # "no such table" errors.
        _db.metadata.create_all(bind=connection)

        yield session

        # Rollback the transaction after the test
        session.close()
        # Only rollback if transaction is still active
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(app):
    """
    Provide Flask test client for HTTP requests.

    The test client allows making HTTP requests to the application
    without running a real server.

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client for making HTTP requests
    """
    return app.test_client()


@pytest.fixture(scope="function")
def admin_user(app, db_session):
    """
    Create an admin user for tests that require authentication.

    This fixture creates a minimal admin user. Tests should explicitly
    request this fixture if they need an admin user.

    Args:
        app: Flask application fixture
        db_session: Database session fixture

    Returns:
        Usuario: Admin user instance
    """
    from coati_payroll.auth import proteger_passwd
    from coati_payroll.enums import TipoUsuario
    from coati_payroll.model import Usuario

    with app.app_context():
        admin = Usuario()
        admin.usuario = "admin-test"
        admin.acceso = proteger_passwd("admin-password")
        admin.nombre = "Admin"
        admin.apellido = "Test"
        admin.correo_electronico = "admin@test.com"
        admin.tipo = TipoUsuario.ADMIN
        admin.activo = True

        db_session.add(admin)
        db_session.commit()

        # Refresh to get the generated ID
        db_session.refresh(admin)

        return admin
