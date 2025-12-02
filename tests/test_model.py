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
"""Unit tests for model utilities."""

from datetime import datetime, timezone

from coati_payroll.model import (
    generador_codigo_empleado,
    generador_de_codigos_unicos,
    utc_now,
)


class TestGeneradorDeCodigosUnicos:
    """Tests for ULID code generator."""

    def test_returns_string(self):
        """Test generator returns a string."""
        result = generador_de_codigos_unicos()
        assert isinstance(result, str)

    def test_length_is_26(self):
        """Test ULID has correct length of 26 characters."""
        result = generador_de_codigos_unicos()
        assert len(result) == 26

    def test_unique_codes(self):
        """Test multiple calls produce unique codes."""
        codes = [generador_de_codigos_unicos() for _ in range(100)]
        assert len(codes) == len(set(codes))

    def test_alphanumeric(self):
        """Test ULID contains only alphanumeric characters."""
        result = generador_de_codigos_unicos()
        assert result.isalnum()


class TestGeneradorCodigoEmpleado:
    """Tests for employee code generator."""

    def test_returns_string(self):
        """Test generator returns a string."""
        result = generador_codigo_empleado()
        assert isinstance(result, str)

    def test_has_correct_prefix(self):
        """Test employee code has EMP- prefix."""
        result = generador_codigo_empleado()
        assert result.startswith("EMP-")

    def test_has_correct_format(self):
        """Test employee code has format EMP-XXXXXX."""
        result = generador_codigo_empleado()
        parts = result.split("-")
        assert len(parts) == 2
        assert parts[0] == "EMP"
        assert len(parts[1]) == 6

    def test_suffix_is_uppercase(self):
        """Test suffix is uppercase alphanumeric."""
        result = generador_codigo_empleado()
        suffix = result.split("-")[1]
        assert suffix.isupper()
        assert suffix.isalnum()

    def test_unique_codes(self):
        """Test multiple calls produce unique codes."""
        codes = [generador_codigo_empleado() for _ in range(100)]
        assert len(codes) == len(set(codes))

    def test_total_length(self):
        """Test total length is 10 characters (EMP- + 6)."""
        result = generador_codigo_empleado()
        assert len(result) == 10


class TestUtcNow:
    """Tests for timezone-aware UTC datetime generator."""

    def test_returns_datetime(self):
        """Test utc_now returns a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_has_timezone_info(self):
        """Test returned datetime is timezone-aware."""
        result = utc_now()
        assert result.tzinfo is not None

    def test_timezone_is_utc(self):
        """Test timezone is UTC."""
        result = utc_now()
        assert result.tzinfo == timezone.utc

    def test_time_is_approximately_now(self):
        """Test returned time is approximately now."""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after
