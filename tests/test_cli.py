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
"""Unit tests for CLI commands - New structure."""

from pathlib import Path
from unittest.mock import patch


class TestSystemCommands:
    """Tests for system CLI commands."""

    def test_system_status(self, runner, app):
        """Test system status command."""
        result = runner.invoke(args=["system", "status"])
        assert result.exit_code == 0
        assert "System Status" in result.output or "database" in result.output.lower()

    def test_system_check(self, runner, app):
        """Test system check command."""
        result = runner.invoke(args=["system", "check"])
        assert result.exit_code == 0
        assert "Database connection" in result.output or "OK" in result.output

    def test_system_info(self, runner, app):
        """Test system info command."""
        result = runner.invoke(args=["system", "info"])
        assert result.exit_code == 0
        assert "version" in result.output.lower() or "Coati Payroll" in result.output

    def test_system_env(self, runner):
        """Test system env command."""
        result = runner.invoke(args=["system", "env"])
        assert result.exit_code == 0
        assert "FLASK" in result.output or "Environment" in result.output


class TestDatabaseCommands:
    """Tests for database management CLI commands."""

    def test_database_init(self, runner):
        """Test database init command creates tables and admin user."""
        result = runner.invoke(args=["database", "init"])
        assert result.exit_code == 0
        assert "Database tables created" in result.output
        assert "Administrator user" in result.output or "admin" in result.output.lower()

    def test_database_seed(self, runner):
        """Test database seed command loads initial data."""
        result = runner.invoke(args=["database", "seed"])
        assert result.exit_code == 0
        assert "Initial data loaded" in result.output or "Seeding" in result.output

    def test_database_status(self, runner, app):
        """Test database status command."""
        runner.invoke(args=["database", "seed"])
        result = runner.invoke(args=["database", "status"])
        assert result.exit_code == 0
        assert "Tables" in result.output or "Records" in result.output

    def test_database_drop(self, runner):
        """Test database drop command removes all tables."""
        result = runner.invoke(args=["database", "drop", "--yes"])
        assert result.exit_code == 0
        assert "dropped" in result.output.lower()

    def test_database_backup(self, runner, app, tmp_path):
        """Test database backup command creates backup file."""
        runner.invoke(args=["database", "seed"])
        
        backup_file = tmp_path / "test_backup.db"
        result = runner.invoke(args=["database", "backup", "-o", str(backup_file)])
        
        assert result.exit_code == 0
        assert "Backup completed successfully" in result.output
        assert backup_file.exists()
        assert backup_file.stat().st_size > 0

    def test_database_backup_default_filename(self, runner, app):
        """Test database backup with auto-generated filename."""
        result = runner.invoke(args=["database", "backup"])
        
        assert result.exit_code == 0
        assert "Backup completed successfully" in result.output
        assert "coati_backup_" in result.output
        assert ".db" in result.output


class TestUserCommands:
    """Tests for user management CLI commands."""

    def test_users_list(self, runner, app):
        """Test users list command."""
        result = runner.invoke(args=["users", "list"])
        assert result.exit_code == 0
        assert "Users" in result.output or "admin" in result.output.lower()

    def test_users_create(self, runner, app):
        """Test users create command."""
        result = runner.invoke(
            args=["users", "create"],
            input="testuser\ntestpass123\ntestpass123\nTest User\ntest@example.com\n"
        )
        assert result.exit_code == 0
        assert "created successfully" in result.output or "testuser" in result.output

    def test_users_disable(self, runner, app):
        """Test users disable command."""
        # First create a user
        runner.invoke(
            args=["users", "create"],
            input="disableuser\npass123\npass123\nDisable User\n\n"
        )
        
        # Then disable it
        result = runner.invoke(args=["users", "disable", "disableuser"])
        assert result.exit_code == 0
        assert "disabled successfully" in result.output or "disableuser" in result.output

    def test_users_reset_password(self, runner, app):
        """Test users reset-password command."""
        # First create a user
        runner.invoke(
            args=["users", "create"],
            input="resetuser\noldpass\noldpass\nReset User\n\n"
        )
        
        # Reset password
        result = runner.invoke(
            args=["users", "reset-password", "resetuser"],
            input="newpass123\nnewpass123\n"
        )
        assert result.exit_code == 0
        assert "Password reset" in result.output or "resetuser" in result.output

    def test_users_set_admin(self, runner, app):
        """Test users set-admin command (legacy)."""
        with patch("coati_payroll.cli.getpass.getpass") as mock_getpass:
            mock_getpass.side_effect = ["adminpass", "adminpass"]
            
            with patch("coati_payroll.cli.click.prompt") as mock_prompt:
                mock_prompt.return_value = "newadmin"
                
                result = runner.invoke(args=["users", "set-admin"])
        
        assert result.exit_code == 0
        assert "administrator" in result.output.lower() or "newadmin" in result.output


class TestCacheCommands:
    """Tests for cache management CLI commands."""

    def test_cache_clear(self, runner, app):
        """Test cache clear command."""
        result = runner.invoke(args=["cache", "clear"])
        
        assert result.exit_code == 0
        assert "cache cleared" in result.output.lower() or "Clearing" in result.output

    def test_cache_status(self, runner, app):
        """Test cache status command."""
        result = runner.invoke(args=["cache", "status"])
        
        assert result.exit_code == 0
        assert "cache" in result.output.lower() or "Status" in result.output

    def test_cache_warm(self, runner, app):
        """Test cache warm command."""
        result = runner.invoke(args=["cache", "warm"])
        
        assert result.exit_code == 0
        assert "cache" in result.output.lower() or "warmed" in result.output.lower()


class TestMaintenanceCommands:
    """Tests for maintenance CLI commands."""

    def test_maintenance_cleanup_sessions(self, runner, app):
        """Test maintenance cleanup-sessions command."""
        result = runner.invoke(args=["maintenance", "cleanup-sessions"])
        
        assert result.exit_code == 0
        assert "session" in result.output.lower() or "cleanup" in result.output.lower()

    def test_maintenance_cleanup_temp(self, runner, app):
        """Test maintenance cleanup-temp command."""
        result = runner.invoke(args=["maintenance", "cleanup-temp"])
        
        assert result.exit_code == 0
        assert "temp" in result.output.lower() or "cleanup" in result.output.lower()

    def test_maintenance_run_jobs(self, runner, app):
        """Test maintenance run-jobs command."""
        result = runner.invoke(args=["maintenance", "run-jobs"])
        
        assert result.exit_code == 0
        assert "job" in result.output.lower() or "completed" in result.output.lower()


class TestDebugCommands:
    """Tests for debug CLI commands."""

    def test_debug_config(self, runner, app):
        """Test debug config command."""
        result = runner.invoke(args=["debug", "config"])
        
        assert result.exit_code == 0
        assert "config" in result.output.lower() or "SQLALCHEMY" in result.output

    def test_debug_routes(self, runner, app):
        """Test debug routes command."""
        result = runner.invoke(args=["debug", "routes"])
        
        assert result.exit_code == 0
        assert "route" in result.output.lower() or "/" in result.output
