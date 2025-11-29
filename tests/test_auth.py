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
"""Unit tests for the authentication module."""

import pytest

from coati_payroll.auth import proteger_passwd, ph


class TestProtegerPasswd:
    """Tests for password hashing function."""

    def test_returns_bytes(self):
        """Test that proteger_passwd returns bytes."""
        result = proteger_passwd("test_password")
        assert isinstance(result, bytes)

    def test_different_passwords_different_hashes(self):
        """Test different passwords produce different hashes."""
        hash1 = proteger_passwd("password1")
        hash2 = proteger_passwd("password2")
        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Test same password produces different hashes (due to salt)."""
        hash1 = proteger_passwd("same_password")
        hash2 = proteger_passwd("same_password")
        # Argon2 includes random salt, so same password = different hashes
        assert hash1 != hash2

    def test_hash_can_be_verified(self):
        """Test that generated hash can be verified with argon2."""
        password = "my_secure_password"
        hashed = proteger_passwd(password)
        # Verify using the argon2 password hasher
        result = ph.verify(hashed.decode("utf-8"), password.encode())
        assert result is True

    def test_empty_password_works(self):
        """Test empty password still produces a hash."""
        result = proteger_passwd("")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_special_characters_password(self):
        """Test password with special characters."""
        password = "p@$$w0rd!#$%^&*()"
        result = proteger_passwd(password)
        assert isinstance(result, bytes)
        # Verify the hash is correct
        assert ph.verify(result.decode("utf-8"), password.encode())

    def test_unicode_password(self):
        """Test password with unicode characters."""
        password = "contraseña_日本語_пароль"
        result = proteger_passwd(password)
        assert isinstance(result, bytes)
        # Verify the hash is correct
        assert ph.verify(result.decode("utf-8"), password.encode())

    def test_long_password(self):
        """Test very long password."""
        password = "a" * 1000
        result = proteger_passwd(password)
        assert isinstance(result, bytes)
        # Verify the hash is correct
        assert ph.verify(result.decode("utf-8"), password.encode())
