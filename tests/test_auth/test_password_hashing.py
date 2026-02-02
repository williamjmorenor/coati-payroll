# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
# Copyright 2025 - 2026 BMO Soluciones, S.A.
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
"""Tests for password hashing functionality."""

from coati_payroll.auth import ph, proteger_passwd


def test_proteger_passwd_returns_bytes():
    """
    Test that proteger_passwd returns bytes.

    Setup:
        - None

    Action:
        - Hash a password

    Verification:
        - Result is bytes
    """
    result = proteger_passwd("test_password")
    assert isinstance(result, bytes)


def test_different_passwords_different_hashes():
    """
    Test that different passwords produce different hashes.

    Setup:
        - None

    Action:
        - Hash two different passwords

    Verification:
        - Hashes are different
    """
    hash1 = proteger_passwd("password1")
    hash2 = proteger_passwd("password2")
    assert hash1 != hash2


def test_same_password_different_hashes():
    """
    Test that same password produces different hashes due to salt.

    Setup:
        - None

    Action:
        - Hash the same password twice

    Verification:
        - Hashes are different (argon2 includes random salt)
    """
    hash1 = proteger_passwd("same_password")
    hash2 = proteger_passwd("same_password")
    assert hash1 != hash2


def test_hash_can_be_verified():
    """
    Test that generated hash can be verified with argon2.

    Setup:
        - None

    Action:
        - Hash a password and verify it

    Verification:
        - Verification succeeds
    """
    password = "my_secure_password"
    hashed = proteger_passwd(password)
    result = ph.verify(hashed.decode("utf-8"), password.encode())
    assert result is True


def test_empty_password_works():
    """
    Test that empty password still produces a hash.

    Setup:
        - None

    Action:
        - Hash empty password

    Verification:
        - Hash is created (non-empty bytes)
    """
    result = proteger_passwd("")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_special_characters_password():
    """
    Test password with special characters.

    Setup:
        - None

    Action:
        - Hash password with special characters

    Verification:
        - Hash is created and can be verified
    """
    password = "p@$$w0rd!#$%^&*()"
    result = proteger_passwd(password)
    assert isinstance(result, bytes)
    assert ph.verify(result.decode("utf-8"), password.encode())


def test_unicode_password():
    """
    Test password with unicode characters.

    Setup:
        - None

    Action:
        - Hash password with unicode

    Verification:
        - Hash is created and can be verified
    """
    password = "contraseña_日本語_пароль"
    result = proteger_passwd(password)
    assert isinstance(result, bytes)
    assert ph.verify(result.decode("utf-8"), password.encode())


def test_long_password():
    """
    Test very long password.

    Setup:
        - None

    Action:
        - Hash 1000 character password

    Verification:
        - Hash is created and can be verified
    """
    password = "a" * 1000
    result = proteger_passwd(password)
    assert isinstance(result, bytes)
    assert ph.verify(result.decode("utf-8"), password.encode())
