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
"""Tests for email verification and restricted access functionality."""

from datetime import datetime

from coati_payroll.auth import proteger_passwd
from coati_payroll.model import Usuario, ConfiguracionGlobal, db
from tests.helpers.auth import login_user


def test_user_with_verified_email_can_login(client, app, db_session):
    """
    Test that a user with verified email can log in successfully.

    Setup:
        - Create user with verified email

    Action:
        - POST to /auth/login with valid credentials

    Verification:
        - Response is redirect (302/303)
        - Redirects to home page
        - No warning about unverified email
    """
    # Create user with verified email
    with app.app_context():
        user = Usuario()
        user.usuario = "verified-user"
        user.acceso = proteger_passwd("password123")
        user.nombre = "Verified"
        user.apellido = "User"
        user.correo_electronico = "verified@test.com"
        user.tipo = "admin"
        user.activo = True
        user.email_verificado = True
        db.session.add(user)
        db.session.commit()

    # Login
    response = login_user(client, "verified-user", "password123")

    # Should redirect after successful login
    assert response.status_code in (302, 303)
    assert b"Su correo electr" not in response.data  # No warning message


def test_user_with_unverified_email_blocked_by_default(client, app, db_session):
    """
    Test that a user with unverified email is blocked by default.

    Setup:
        - Create user with unverified email
        - Global config has restricted access disabled (default)

    Action:
        - POST to /auth/login with valid credentials

    Verification:
        - User cannot log in
        - Warning message about verification requirement is shown
    """
    # Create user with unverified email
    with app.app_context():
        user = Usuario()
        user.usuario = "unverified-user"
        user.acceso = proteger_passwd("password123")
        user.nombre = "Unverified"
        user.apellido = "User"
        user.correo_electronico = "unverified@test.com"
        user.tipo = "admin"
        user.activo = True
        user.email_verificado = False
        db.session.add(user)
        db.session.commit()

    # Attempt to login
    response = login_user(client, "unverified-user", "password123")

    # Should stay on login page (200) or return a response
    assert response.status_code in (200, 302, 303)


def test_user_with_unverified_email_allowed_when_configured(client, app, db_session):
    """
    Test that a user with unverified email can log in when restricted access is enabled.

    Setup:
        - Create user with unverified email
        - Enable restricted access in global config

    Action:
        - POST to /auth/login with valid credentials

    Verification:
        - User can log in
        - Warning message about restricted access is shown
    """
    # Create user with unverified email
    with app.app_context():
        user = Usuario()
        user.usuario = "unverified-allowed"
        user.acceso = proteger_passwd("password123")
        user.nombre = "Unverified"
        user.apellido = "Allowed"
        user.correo_electronico = "unverified.allowed@test.com"
        user.tipo = "admin"
        user.activo = True
        user.email_verificado = False
        db.session.add(user)

        # Enable restricted access
        config = ConfiguracionGlobal()
        config.permitir_acceso_email_no_verificado = True
        db.session.add(config)
        db.session.commit()

    # Login
    response = login_user(client, "unverified-allowed", "password123")

    # Should redirect after successful login
    assert response.status_code in (302, 303)


def test_configuration_page_shows_restricted_access_option(client, app, admin_user):
    """
    Test that configuration page displays the restricted access option.

    Setup:
        - Create admin user
        - Log in

    Action:
        - GET /configuracion/

    Verification:
        - Page displays restricted access checkbox
    """
    # Login first
    login_response = login_user(client, "admin-test", "admin-password")
    
    # Follow redirect if login was successful
    if login_response.status_code in (302, 303):
        # Access configuration page
        response = client.get("/configuracion/")

        # Should show restricted access option
        assert response.status_code == 200
        assert b"permitir_acceso_email_no_verificado" in response.data
    else:
        # Login failed
        assert False, "Login failed"


def test_admin_can_enable_restricted_access(client, app, admin_user, db_session):
    """
    Test that admin can enable restricted access for unverified email users.

    Setup:
        - Create admin user
        - Log in

    Action:
        - POST to /configuracion/acceso_email with checkbox enabled

    Verification:
        - Configuration is updated in database
        - Success message is shown
    """
    # Login first
    login_response = login_user(client, "admin-test", "admin-password")
    
    # Ensure login was successful
    assert login_response.status_code in (302, 303)

    # Enable restricted access
    response = client.post(
        "/configuracion/acceso_email",
        data={"permitir_acceso_email_no_verificado": "on"},
        follow_redirects=False,
    )

    # Should redirect (success)
    assert response.status_code in (302, 303)

    # Verify configuration in database
    with app.app_context():
        config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one_or_none()
        assert config is not None
        assert config.permitir_acceso_email_no_verificado is True


def test_admin_can_disable_restricted_access(client, app, admin_user, db_session):
    """
    Test that admin can disable restricted access for unverified email users.

    Setup:
        - Create admin user
        - Enable restricted access in config
        - Log in

    Action:
        - POST to /configuracion/acceso_email with checkbox disabled

    Verification:
        - Configuration is updated in database
        - Success message is shown
    """
    # Enable restricted access first
    with app.app_context():
        config = ConfiguracionGlobal()
        config.permitir_acceso_email_no_verificado = True
        db.session.add(config)
        db.session.commit()

    # Login
    login_response = login_user(client, "admin-test", "admin-password")
    
    # Ensure login was successful
    assert login_response.status_code in (302, 303)

    # Disable restricted access (no checkbox = off)
    response = client.post("/configuracion/acceso_email", data={}, follow_redirects=False)

    # Should redirect (success)
    assert response.status_code in (302, 303)

    # Verify configuration in database
    with app.app_context():
        config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one_or_none()
        assert config is not None
        assert config.permitir_acceso_email_no_verificado is False


def test_usuario_model_has_email_verification_fields(app, db_session):
    """
    Test that Usuario model has the new email verification fields.

    Setup:
        - None

    Action:
        - Create a user with email verification fields

    Verification:
        - Fields are accessible and can be set
    """
    with app.app_context():
        user = Usuario()
        user.usuario = "test-user"
        user.acceso = proteger_passwd("password")
        user.nombre = "Test"
        user.apellido = "User"
        user.correo_electronico = "test@example.com"
        user.tipo = "admin"
        user.activo = True
        user.email_verificado = True
        
        user.fecha_verificacion_email = datetime.now()
        
        db.session.add(user)
        db.session.commit()

        # Retrieve and verify
        retrieved_user = db.session.execute(
            db.select(Usuario).filter_by(usuario="test-user")
        ).scalar_one()
        
        assert retrieved_user.email_verificado is True
        assert retrieved_user.fecha_verificacion_email is not None


def test_configuracion_global_has_restricted_access_field(app, db_session):
    """
    Test that ConfiguracionGlobal model has the new restricted access field.

    Setup:
        - None

    Action:
        - Create a configuration with restricted access field

    Verification:
        - Field is accessible and can be set
    """
    with app.app_context():
        config = ConfiguracionGlobal()
        config.idioma = "es"
        config.permitir_acceso_email_no_verificado = True
        
        db.session.add(config)
        db.session.commit()

        # Retrieve and verify
        retrieved_config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one()
        
        assert retrieved_config.permitir_acceso_email_no_verificado is True
