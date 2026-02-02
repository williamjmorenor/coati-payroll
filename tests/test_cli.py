# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Unit tests for CLI module functions."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from coati_payroll.auth import proteger_passwd
from coati_payroll.model import Usuario, db


# ============================================================================
# SYSTEM COMMANDS TESTS
# ============================================================================


def test_system_status(app, db_session):
    """Test _system_status returns correct data."""
    from coati_payroll.cli import _system_status

    with app.app_context():
        # Delete all admin users that may have been created during setup
        db_session.query(Usuario).filter_by(tipo="admin").delete()
        db_session.commit()

        # Create a single admin user manually
        admin = Usuario()
        admin.usuario = "admin-for-status"
        admin.acceso = proteger_passwd("password")
        admin.nombre = "Admin"
        admin.apellido = "Test"
        admin.tipo = "admin"
        admin.activo = True
        db_session.add(admin)
        db_session.commit()

        result = _system_status()

        assert result["database"] == "connected"
        assert result["admin_user"] == "active"
        assert "mode" in result


def test_system_status_no_admin(app, db_session):
    """Test _system_status when no admin user exists."""
    from coati_payroll.cli import _system_status

    with app.app_context():
        result = _system_status()

        assert result["database"] == "connected"
        assert result["admin_user"] == "none"


def test_system_check(app, db_session, admin_user):
    """Test _system_check returns checks."""
    from coati_payroll.cli import _system_check

    with app.app_context():
        checks = _system_check()

        assert len(checks) == 3
        assert any(c["name"] == "Database connection" for c in checks)
        assert any(c["name"] == "Active admin user" for c in checks)
        assert any(c["name"] == "Required tables" for c in checks)


def test_system_info(app, db_session):
    """Test _system_info returns system information."""
    from coati_payroll.cli import _system_info

    with app.app_context():
        info = _system_info()

        assert "version" in info
        assert "python" in info
        assert "database_uri" in info


def test_system_env():
    """Test _system_env returns environment variables."""
    from coati_payroll.cli import _system_env

    env_vars = _system_env()

    assert "FLASK_APP" in env_vars
    assert "FLASK_ENV" in env_vars
    assert "DATABASE_URL" in env_vars
    assert "ADMIN_USER" in env_vars
    assert "COATI_LANG" in env_vars


# ============================================================================
# DATABASE COMMANDS TESTS
# ============================================================================


def test_database_status(app, db_session):
    """Test _database_status returns database info."""
    from coati_payroll.cli import _database_status

    with app.app_context():
        result = _database_status()

        assert "tables" in result
        assert "table_names" in result
        assert "record_counts" in result
        assert isinstance(result["tables"], int)


def test_database_init(app, db_session):
    """Test _database_init initializes database."""
    from coati_payroll.cli import _database_init

    with app.app_context():
        admin_user = _database_init(app)

        assert admin_user is not None
        assert isinstance(admin_user, str)


def test_database_seed(app, db_session):
    """Test _database_seed loads initial data."""
    from coati_payroll.cli import _database_seed

    with app.app_context():
        # Should not raise an exception
        _database_seed()


def test_database_drop(app, db_session):
    """Test _database_drop removes all tables."""
    from coati_payroll.cli import _database_drop

    with app.app_context():
        # Should not raise an exception
        _database_drop()


def test_backup_sqlite(app, db_session):
    """Test _backup_sqlite creates backup file for in-memory database."""
    from coati_payroll.cli import _backup_sqlite

    with app.app_context():
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            output_file = tmp.name

        try:
            # Use the actual in-memory database URL
            db_url = str(db.engine.url)

            # The function should handle in-memory databases
            result = _backup_sqlite(db_url, output_file)

            assert result.exists()
            assert str(result) == output_file
            # Verify file has some content (not empty)
            assert result.stat().st_size > 0
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


def test_database_restore_sqlite(app, db_session):
    """Test _database_restore_sqlite restores from backup."""
    from coati_payroll.cli import _database_restore_sqlite

    with app.app_context():
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            backup_file = tmp.name
            tmp.write(b"test data")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            target_db = tmp.name

        try:
            db_url = f"sqlite:///{target_db}"
            _database_restore_sqlite(backup_file, db_url)

            assert Path(target_db).exists()
        finally:
            if Path(backup_file).exists():
                Path(backup_file).unlink()
            if Path(target_db).exists():
                Path(target_db).unlink()


def test_database_restore_sqlite_file_not_found(app, db_session):
    """Test _database_restore_sqlite raises error for missing file."""
    from coati_payroll.cli import _database_restore_sqlite

    with app.app_context():
        with pytest.raises(FileNotFoundError):
            _database_restore_sqlite("nonexistent.db", "sqlite:///test.db")


def test_database_restore_sqlite_memory_db_error(app, db_session):
    """Test _database_restore_sqlite raises error for in-memory database."""
    from coati_payroll.cli import _database_restore_sqlite

    with app.app_context():
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            backup_file = tmp.name

        try:
            with pytest.raises(ValueError, match="Cannot restore to in-memory database"):
                _database_restore_sqlite(backup_file, "sqlite:///:memory:")
        finally:
            if Path(backup_file).exists():
                Path(backup_file).unlink()


# ============================================================================
# USER COMMANDS TESTS
# ============================================================================


def test_users_list(app, db_session, admin_user):
    """Test _users_list returns all users."""
    from coati_payroll.cli import _users_list

    with app.app_context():
        users = _users_list()

        assert len(users) >= 1
        assert any(u["username"] == "admin-test" for u in users)


def test_users_create(app, db_session):
    """Test _users_create creates a new user."""
    from coati_payroll.cli import _users_create

    with app.app_context():
        _users_create("testuser", "password123", "Test User", "test@example.com", "operador")

        user = db.session.execute(db.select(Usuario).filter_by(usuario="testuser")).scalar_one_or_none()
        assert user is not None
        assert user.nombre == "Test"
        assert user.apellido == "User"
        assert user.correo_electronico == "test@example.com"
        assert user.tipo == "operador"
        assert user.activo is True


def test_users_create_existing_user(app, db_session, admin_user):
    """Test _users_create raises error for existing user."""
    from coati_payroll.cli import _users_create

    with app.app_context():
        with pytest.raises(ValueError, match="already exists"):
            _users_create("admin-test", "password", "Admin Test", None, "admin")


def test_users_disable(app, db_session, admin_user):
    """Test _users_disable disables a user."""
    from coati_payroll.cli import _users_disable

    with app.app_context():
        _users_disable("admin-test")

        user = db.session.execute(db.select(Usuario).filter_by(usuario="admin-test")).scalar_one_or_none()
        assert user is not None
        assert user.activo is False


def test_users_disable_nonexistent(app, db_session):
    """Test _users_disable raises error for nonexistent user."""
    from coati_payroll.cli import _users_disable

    with app.app_context():
        with pytest.raises(ValueError, match="not found"):
            _users_disable("nonexistent")


def test_users_reset_password(app, db_session, admin_user):
    """Test _users_reset_password resets password."""
    from coati_payroll.cli import _users_reset_password

    with app.app_context():
        old_password = admin_user.acceso
        _users_reset_password("admin-test", "newpassword123")

        user = db.session.execute(db.select(Usuario).filter_by(usuario="admin-test")).scalar_one_or_none()
        assert user is not None
        assert user.acceso != old_password


def test_users_reset_password_nonexistent(app, db_session):
    """Test _users_reset_password raises error for nonexistent user."""
    from coati_payroll.cli import _users_reset_password

    with app.app_context():
        with pytest.raises(ValueError, match="not found"):
            _users_reset_password("nonexistent", "newpassword")


def test_users_set_admin_new_user(app, db_session):
    """Test _users_set_admin creates new admin user."""
    from coati_payroll.cli import _users_set_admin

    with app.app_context():
        is_new, deactivated = _users_set_admin("newadmin", "adminpass")

        assert is_new is True
        assert deactivated == 0

        user = db.session.execute(db.select(Usuario).filter_by(usuario="newadmin")).scalar_one_or_none()
        assert user is not None
        assert user.tipo == "admin"
        assert user.activo is True


def test_users_set_admin_existing_user(app, db_session, admin_user):
    """Test _users_set_admin updates existing user to admin."""
    from coati_payroll.cli import _users_set_admin

    with app.app_context():
        # Create a non-admin user
        user = Usuario()
        user.usuario = "regularuser"
        user.acceso = proteger_passwd("password")
        user.nombre = "Regular"
        user.apellido = "User"
        user.tipo = "operador"
        user.activo = True
        db_session.add(user)
        db_session.commit()

        is_new, deactivated = _users_set_admin("regularuser", "newpass")

        assert is_new is False
        assert deactivated == 1  # admin-test was deactivated

        user = db.session.execute(db.select(Usuario).filter_by(usuario="regularuser")).scalar_one_or_none()
        assert user is not None
        assert user.tipo == "admin"
        assert user.activo is True


# ============================================================================
# CACHE COMMANDS TESTS
# ============================================================================


def test_cache_clear(app, db_session):
    """Test _cache_clear clears caches."""
    from coati_payroll.cli import _cache_clear

    with app.app_context():
        # Should not raise an exception
        _cache_clear()


def test_cache_warm(app, db_session):
    """Test _cache_warm warms up caches."""
    from coati_payroll.cli import _cache_warm

    with app.app_context():
        lang = _cache_warm()
        assert lang is not None
        assert isinstance(lang, str)


def test_cache_status(app, db_session):
    """Test _cache_status returns cache status."""
    from coati_payroll.cli import _cache_status

    with app.app_context():
        status = _cache_status()
        assert "language_cache" in status


# ============================================================================
# DEBUG COMMANDS TESTS
# ============================================================================


def test_debug_config(app, db_session):
    """Test _debug_config returns configuration."""
    from coati_payroll.cli import _debug_config

    with app.app_context():
        config = _debug_config(app)

        assert "SQLALCHEMY_DATABASE_URI" in config
        assert "TESTING" in config
        assert "DEBUG" in config


def test_debug_routes(app, db_session):
    """Test _debug_routes returns routes."""
    from coati_payroll.cli import _debug_routes

    with app.app_context():
        routes = _debug_routes(app)

        assert len(routes) > 0
        assert all("endpoint" in r for r in routes)
        assert all("methods" in r for r in routes)
        assert all("path" in r for r in routes)


# ============================================================================
# BACKUP POSTGRESQL AND MYSQL TESTS (mocked)
# ============================================================================


def test_backup_postgresql(app, db_session, monkeypatch):
    """Test _backup_postgresql creates backup."""
    from coati_payroll.cli import _backup_postgresql
    import subprocess

    # Mock subprocess.run to avoid actually running pg_dump
    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with app.app_context():
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp:
            output_file = tmp.name

        try:
            db_url = "postgresql://user:pass@localhost/dbname"
            result = _backup_postgresql(db_url, output_file)

            assert result == Path(output_file)
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


def test_backup_postgresql_failure(app, db_session, monkeypatch):
    """Test _backup_postgresql handles pg_dump failure."""
    from coati_payroll.cli import _backup_postgresql
    import subprocess

    # Mock subprocess.run to simulate failure
    def mock_run(*args, **kwargs):
        class Result:
            returncode = 1
            stderr = "pg_dump error"

        return Result()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with app.app_context():
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp:
            output_file = tmp.name

        try:
            db_url = "postgresql://user:pass@localhost/dbname"
            with pytest.raises(RuntimeError, match="pg_dump failed"):
                _backup_postgresql(db_url, output_file)
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


def test_backup_mysql(app, db_session, monkeypatch):
    """Test _backup_mysql creates backup."""
    from coati_payroll.cli import _backup_mysql
    import subprocess

    # Mock subprocess.run to avoid actually running mysqldump
    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with app.app_context():
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp:
            output_file = tmp.name

        try:
            db_url = "mysql://user:pass@localhost/dbname"
            result = _backup_mysql(db_url, output_file)

            assert result == Path(output_file)
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


def test_backup_mysql_failure(app, db_session, monkeypatch):
    """Test _backup_mysql handles mysqldump failure."""
    from coati_payroll.cli import _backup_mysql
    import subprocess

    # Mock subprocess.run to simulate failure
    def mock_run(*args, **kwargs):
        class Result:
            returncode = 1
            stderr = "mysqldump error"

        return Result()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with app.app_context():
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp:
            output_file = tmp.name

        try:
            db_url = "mysql://user:pass@localhost/dbname"
            with pytest.raises(RuntimeError, match="mysqldump failed"):
                _backup_mysql(db_url, output_file)
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


# ============================================================================
# OUTPUT RESULT AND CONTEXT TESTS
# ============================================================================


def test_output_result_text(capsys):
    """Test output_result in text mode."""
    from coati_payroll.cli import output_result, CLIContext

    ctx = CLIContext()
    ctx.json_output = False

    output_result(ctx, "Test message", None, True)
    captured = capsys.readouterr()
    assert "✓ Test message" in captured.out


def test_output_result_json(capsys):
    """Test output_result in JSON mode."""
    from coati_payroll.cli import output_result, CLIContext
    import json

    ctx = CLIContext()
    ctx.json_output = True

    output_result(ctx, "Test message", {"key": "value"}, True)
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["success"] is True
    assert result["message"] == "Test message"
    assert result["data"]["key"] == "value"


def test_output_result_failure(capsys):
    """Test output_result with failure."""
    from coati_payroll.cli import output_result, CLIContext

    ctx = CLIContext()
    ctx.json_output = False

    output_result(ctx, "Error occurred", None, False)
    captured = capsys.readouterr()
    assert "✗ Error occurred" in captured.out


def test_cli_context():
    """Test CLIContext initialization."""
    from coati_payroll.cli import CLIContext

    ctx = CLIContext()
    assert ctx.environment is None
    assert ctx.json_output is False
    assert ctx.auto_yes is False


# ============================================================================
# ADDITIONAL INTEGRATION TESTS
# ============================================================================


def test_system_check_db_connection_failure(app, db_session, monkeypatch):
    """Test _system_check handles database connection failure."""
    from coati_payroll.cli import _system_check

    def mock_execute(*args, **kwargs):
        raise Exception("Connection failed")

    with app.app_context():
        # Temporarily break the database connection
        original_execute = db.session.execute
        monkeypatch.setattr(db.session, "execute", mock_execute)

        checks = _system_check()

        # Should have a failed database connection check
        db_check = next((c for c in checks if c["name"] == "Database connection"), None)
        assert db_check is not None
        assert db_check["status"] == "FAILED"

        # Restore original execute
        monkeypatch.setattr(db.session, "execute", original_execute)


def test_users_create_single_name(app, db_session):
    """Test _users_create with single name (no last name)."""
    from coati_payroll.cli import _users_create

    with app.app_context():
        _users_create("singlename", "password123", "SingleName", None, "operador")

        user = db.session.execute(db.select(Usuario).filter_by(usuario="singlename")).scalar_one_or_none()
        assert user is not None
        assert user.nombre == "SingleName"
        assert user.apellido == ""


def test_backup_sqlite_with_auto_timestamp(app, db_session):
    """Test _backup_sqlite generates timestamp in filename."""
    from coati_payroll.cli import _backup_sqlite

    with app.app_context():
        db_url = str(db.engine.url)

        # Call without specifying output file
        result = _backup_sqlite(db_url)

        try:
            assert result.exists()
            assert "coati_backup_" in str(result)
            assert result.suffix == ".db"
        finally:
            if result.exists():
                result.unlink()


def test_backup_postgresql_with_auto_timestamp(app, db_session, monkeypatch):
    """Test _backup_postgresql generates timestamp in filename."""
    from coati_payroll.cli import _backup_postgresql
    import subprocess

    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with app.app_context():
        db_url = "postgresql://user:pass@localhost/dbname"

        # Call without specifying output file
        result = _backup_postgresql(db_url)

        try:
            # Check that a filename with timestamp was generated
            assert "coati_backup_" in str(result)
            assert result.suffix == ".sql"
        finally:
            if result.exists():
                result.unlink()


def test_backup_mysql_with_auto_timestamp(app, db_session, monkeypatch):
    """Test _backup_mysql generates timestamp in filename."""
    from coati_payroll.cli import _backup_mysql
    import subprocess

    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", mock_run)

    with app.app_context():
        db_url = "mysql://user:pass@localhost/dbname"

        # Call without specifying output file
        result = _backup_mysql(db_url)

        try:
            # Check that a filename with timestamp was generated
            assert "coati_backup_" in str(result)
            assert result.suffix == ".sql"
        finally:
            if result.exists():
                result.unlink()


# ============================================================================
# CLI COMMAND TESTS (using CliRunner)
# ============================================================================


def test_system_env_command():
    """Test system env command."""
    from click.testing import CliRunner
    from coati_payroll.cli import system

    runner = CliRunner()
    result = runner.invoke(system, ["env"])
    assert result.exit_code == 0
    assert "FLASK_APP" in result.output


def test_register_cli_commands(app):
    """Test register_cli_commands adds commands to app."""
    from coati_payroll.cli import register_cli_commands

    # Count commands before
    initial_commands = len(app.cli.commands)

    register_cli_commands(app)

    # Check that commands were added
    assert len(app.cli.commands) >= initial_commands
    assert "system" in app.cli.commands
    assert "database" in app.cli.commands
    assert "users" in app.cli.commands
    assert "cache" in app.cli.commands
    assert "maintenance" in app.cli.commands
    assert "debug" in app.cli.commands
    assert "plugins" in app.cli.commands
