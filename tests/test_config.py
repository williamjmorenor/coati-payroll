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
"""Unit tests for configuration module."""

from pathlib import Path

import pytest


class TestConfigurationDirectories:
    """Tests for configuration directory constants."""

    def test_directorio_actual_is_path(self):
        """Test DIRECTORIO_ACTUAL is a Path object."""
        from coati_payroll.config import DIRECTORIO_ACTUAL

        assert isinstance(DIRECTORIO_ACTUAL, Path)

    def test_directorio_actual_exists(self):
        """Test DIRECTORIO_ACTUAL points to existing directory."""
        from coati_payroll.config import DIRECTORIO_ACTUAL

        assert DIRECTORIO_ACTUAL.exists()

    def test_directorio_plantillas_is_string(self):
        """Test DIRECTORIO_PLANTILLAS_BASE is a string."""
        from coati_payroll.config import DIRECTORIO_PLANTILLAS_BASE

        assert isinstance(DIRECTORIO_PLANTILLAS_BASE, str)

    def test_directorio_archivos_is_string(self):
        """Test DIRECTORIO_ARCHIVOS_BASE is a string."""
        from coati_payroll.config import DIRECTORIO_ARCHIVOS_BASE

        assert isinstance(DIRECTORIO_ARCHIVOS_BASE, str)


class TestConfiguration:
    """Tests for configuration dictionary."""

    def test_configuration_has_secret_key(self):
        """Test configuration has SECRET_KEY."""
        from coati_payroll.config import CONFIGURACION

        assert "SECRET_KEY" in CONFIGURACION

    def test_configuration_has_database_uri(self):
        """Test configuration has SQLALCHEMY_DATABASE_URI."""
        from coati_payroll.config import CONFIGURACION

        assert "SQLALCHEMY_DATABASE_URI" in CONFIGURACION

    def test_database_uri_is_sqlite_for_testing(self):
        """Test database URI is sqlite in-memory during testing."""
        from coati_payroll.config import CONFIGURACION

        db_uri = CONFIGURACION.get("SQLALCHEMY_DATABASE_URI", "")
        # Should be sqlite in test environment
        assert "sqlite" in db_uri


class TestLoadConfigFromFile:
    """Tests for configuration file loading."""

    def test_load_config_returns_dict(self):
        """Test load_config_from_file returns a dictionary."""
        from coati_payroll.config import load_config_from_file

        result = load_config_from_file()
        assert isinstance(result, dict)

    def test_load_config_handles_missing_file(self):
        """Test load_config_from_file handles missing config file gracefully."""
        from coati_payroll.config import load_config_from_file

        # Should not raise an exception
        result = load_config_from_file()
        # Returns empty dict when no config file found
        assert isinstance(result, dict)


class TestTestingDetection:
    """Tests for testing environment detection."""

    def test_testing_flag_is_true_during_pytest(self):
        """Test TESTING flag is True when running pytest."""
        from coati_payroll.config import TESTING

        assert TESTING is True

    def test_sqlite_is_memory_during_testing(self):
        """Test SQLITE uses in-memory database during testing."""
        from coati_payroll.config import SQLITE

        assert SQLITE == "sqlite:///:memory:"
