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
"""Tests for users set-admin CLI command that require special handling."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from coati_payroll import create_app
from coati_payroll.cli import register_cli_commands, users
from coati_payroll.model import db, Usuario


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def cli_app():
    """Create a test Flask app with CLI commands registered."""
    config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:?check_same_thread=False",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"check_same_thread": False}},
        "SECRET_KEY": "test-secret-key",
        "PRESERVE_CONTEXT_ON_EXCEPTION": False,
    }
    app = create_app(config)
    register_cli_commands(app)
    return app


# ============================================================================
# USERS SET-ADMIN COMMAND TESTS
# ============================================================================


def test_users_set_admin_with_mock_getpass(cli_app, runner):
    """Test users set-admin command with mocked password input."""
    with cli_app.app_context():
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            # Mock password prompts
            mock_getpass.side_effect = ["testpass123", "testpass123"]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "testadmin"
                
                result = runner.invoke(users, ["set-admin"])
                assert result.exit_code == 0
                assert "administrator" in result.output.lower()


def test_users_set_admin_empty_username_with_mock(cli_app, runner):
    """Test set-admin with empty username using mock."""
    with cli_app.app_context():
        with patch("coati_payroll.cli.click.prompt") as mock_prompt:
            mock_prompt.return_value = ""
            
            result = runner.invoke(users, ["set-admin"])
            assert result.exit_code == 1
            assert "cannot be empty" in result.output.lower()


def test_users_set_admin_password_mismatch_with_mock(cli_app, runner):
    """Test set-admin with password mismatch using mock."""
    with cli_app.app_context():
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            # Mock password prompts with different values
            mock_getpass.side_effect = ["password1", "password2"]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "testadmin"
                
                result = runner.invoke(users, ["set-admin"])
                assert result.exit_code == 1
                assert "do not match" in result.output.lower()


def test_users_set_admin_empty_password_with_mock(cli_app, runner):
    """Test set-admin with empty password using mock."""
    with cli_app.app_context():
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            # Mock password prompts with empty values
            mock_getpass.side_effect = ["", ""]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "testadmin"
                
                result = runner.invoke(users, ["set-admin"])
                assert result.exit_code == 1
                assert "cannot be empty" in result.output.lower()


def test_users_set_admin_updates_existing_with_mock(cli_app, runner):
    """Test set-admin updates existing user using mock."""
    with cli_app.app_context():
        # Create a regular user first
        from coati_payroll.auth import proteger_passwd
        
        user = Usuario()
        user.usuario = "existinguser"
        user.acceso = proteger_passwd("oldpass")
        user.nombre = "Existing"
        user.apellido = "User"
        user.tipo = "operador"
        user.activo = True
        
        db.session.add(user)
        db.session.commit()
        
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            mock_getpass.side_effect = ["newpass123", "newpass123"]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "existinguser"
                
                result = runner.invoke(users, ["set-admin"])
                assert result.exit_code == 0
                assert "updated" in result.output.lower()
                
                # Verify user was updated
                updated_user = db.session.execute(
                    db.select(Usuario).filter_by(usuario="existinguser")
                ).scalar_one()
                assert updated_user.tipo == "admin"
                assert updated_user.activo is True


def test_users_set_admin_deactivates_other_admins_with_mock(cli_app, runner):
    """Test set-admin deactivates other admin users using mock."""
    with cli_app.app_context():
        # Create existing admin users
        from coati_payroll.auth import proteger_passwd
        
        admin1 = Usuario()
        admin1.usuario = "admin1"
        admin1.acceso = proteger_passwd("pass1")
        admin1.nombre = "Admin"
        admin1.apellido = "One"
        admin1.tipo = "admin"
        admin1.activo = True
        
        admin2 = Usuario()
        admin2.usuario = "admin2"
        admin2.acceso = proteger_passwd("pass2")
        admin2.nombre = "Admin"
        admin2.apellido = "Two"
        admin2.tipo = "admin"
        admin2.activo = True
        
        db.session.add_all([admin1, admin2])
        db.session.commit()
        
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            mock_getpass.side_effect = ["newadminpass", "newadminpass"]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "newadmin"
                
                result = runner.invoke(users, ["set-admin"])
                assert result.exit_code == 0
                
                # Verify old admins are deactivated
                admin1_after = db.session.execute(
                    db.select(Usuario).filter_by(usuario="admin1")
                ).scalar_one()
                admin2_after = db.session.execute(
                    db.select(Usuario).filter_by(usuario="admin2")
                ).scalar_one()
                
                assert admin1_after.activo is False
                assert admin2_after.activo is False
                
                # Verify new admin exists
                new_admin = db.session.execute(
                    db.select(Usuario).filter_by(usuario="newadmin")
                ).scalar_one()
                assert new_admin.tipo == "admin"
                assert new_admin.activo is True


def test_users_set_admin_with_database_error(cli_app, runner):
    """Test set-admin with database error using mock."""
    with cli_app.app_context():
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            mock_getpass.side_effect = ["testpass", "testpass"]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "testadmin"
                
                with patch.object(db.session, "commit", side_effect=Exception("DB Error")):
                    result = runner.invoke(users, ["set-admin"])
                    assert result.exit_code == 1
                    assert "error" in result.output.lower() or "failed" in result.output.lower()


def test_users_set_admin_with_whitespace_username(cli_app, runner):
    """Test set-admin with whitespace username using mock."""
    with cli_app.app_context():
        with patch("coati_payroll.cli.click.prompt") as mock_prompt:
            mock_prompt.return_value = "  "
            
            result = runner.invoke(users, ["set-admin"])
            assert result.exit_code == 1
            assert "cannot be empty" in result.output.lower()


def test_users_set_admin_strips_username(cli_app, runner):
    """Test set-admin strips whitespace from username using mock."""
    with cli_app.app_context():
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            mock_getpass.side_effect = ["testpass", "testpass"]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "  adminuser  "
                
                result = runner.invoke(users, ["set-admin"])
                assert result.exit_code == 0
                
                # Verify username was stripped
                admin = db.session.execute(
                    db.select(Usuario).filter_by(usuario="adminuser")
                ).scalar_one()
                assert admin.usuario == "adminuser"
