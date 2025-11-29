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

import pytest

from coati_payroll.model import generador_de_codigos_unicos, utc_now


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
