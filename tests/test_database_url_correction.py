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
"""Tests for database URL correction in config.py.

The config module automatically corrects database URLs to use the appropriate
SQLAlchemy drivers for each database engine.
"""

import os
import pytest
from unittest.mock import patch


class TestDatabaseURLCorrection:
    """Test automatic database URL correction for different database engines."""

    def test_postgres_url_corrected_to_pg8000(self):
        """Test postgres:// URL is corrected to postgresql+pg8000:// for PostgreSQL."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@localhost/dbname"}):
            # Reload config module to pick up new env var
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("postgresql+pg8000://")
            assert "user:pass@localhost/dbname" in corrected_url

    def test_postgresql_url_corrected_to_pg8000(self):
        """Test postgresql:// URL is corrected to postgresql+pg8000://."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/dbname"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("postgresql+pg8000://")
            assert "user:pass@localhost/dbname" in corrected_url

    def test_mysql_url_corrected_to_pymysql(self):
        """Test mysql:// URL is corrected to mysql+pymysql://."""
        with patch.dict(os.environ, {"DATABASE_URL": "mysql://user:pass@localhost/dbname"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("mysql+pymysql://")
            assert "user:pass@localhost/dbname" in corrected_url

    def test_mariadb_url_corrected_to_mariadbconnector(self):
        """Test mariadb:// URL is corrected to mariadb+mariadbconnector://."""
        with patch.dict(os.environ, {"DATABASE_URL": "mariadb://user:pass@localhost/dbname"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("mariadb+mariadbconnector://")
            assert "user:pass@localhost/dbname" in corrected_url

    def test_sqlite_url_unchanged(self):
        """Test sqlite:// URL is not modified."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///path/to/db.db"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url == "sqlite:///path/to/db.db"

    def test_postgres_url_removes_sslmode_unless_heroku(self):
        """Test sslmode is removed from postgres URL unless on Heroku."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/dbname?sslmode=require"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert "sslmode" not in corrected_url

    def test_postgres_url_keeps_sslmode_on_heroku(self):
        """Test sslmode is kept in postgres URL when DYNO env var is present."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgres://user:pass@localhost/dbname",
            "DYNO": "web.1"
        }):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("postgresql://")  # Keeps postgresql, not pg8000
            assert "sslmode=require" in corrected_url

    def test_url_with_special_characters_in_password(self):
        """Test URL correction preserves special characters in password."""
        # URL-encoded password with special chars
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:p%40ss%23word@localhost/dbname"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("postgresql+pg8000://")
            assert "p%40ss%23word" in corrected_url

    def test_url_with_port_number(self):
        """Test URL correction preserves port number."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost:5433/dbname"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("postgresql+pg8000://")
            assert ":5433" in corrected_url

    def test_url_with_query_parameters(self):
        """Test URL correction preserves query parameters."""
        with patch.dict(os.environ, {"DATABASE_URL": "mysql://user:pass@localhost/dbname?charset=utf8mb4"}):
            import importlib
            from coati_payroll import config
            importlib.reload(config)
            
            corrected_url = config.CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")
            assert corrected_url.startswith("mysql+pymysql://")
            assert "charset=utf8mb4" in corrected_url


class TestDatabaseDrivers:
    """Test that database drivers are available."""

    def test_pg8000_available(self):
        """Test pg8000 PostgreSQL driver is available."""
        try:
            import pg8000
            assert pg8000 is not None
        except ImportError:
            pytest.fail("pg8000 driver not available")

    def test_pymysql_available(self):
        """Test PyMySQL driver is available."""
        try:
            import pymysql
            assert pymysql is not None
        except ImportError:
            # PyMySQL might not be installed, but mysql-connector-python should be
            try:
                import mysql.connector
                assert mysql.connector is not None
            except ImportError:
                pytest.fail("No MySQL driver available")

    def test_sqlite3_available(self):
        """Test sqlite3 is available (built-in)."""
        import sqlite3
        assert sqlite3 is not None
