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


class TestValidarAcceso:
    """Tests for access validation function."""

    def test_validar_acceso_valid_credentials(self, app):
        """Test validar_acceso with valid credentials."""
        from coati_payroll.auth import validar_acceso, proteger_passwd
        from coati_payroll.model import Usuario, db

        with app.app_context():
            # Create a test user
            user = Usuario()
            user.usuario = "testuser_auth"
            user.acceso = proteger_passwd("testpass")
            user.nombre = "Test"
            user.apellido = "User"
            user.tipo = "user"
            user.activo = True
            db.session.add(user)
            db.session.commit()

            # Test valid credentials
            result = validar_acceso("testuser_auth", "testpass")
            assert result is True

    def test_validar_acceso_invalid_password(self, app):
        """Test validar_acceso with invalid password."""
        from coati_payroll.auth import validar_acceso, proteger_passwd
        from coati_payroll.model import Usuario, db

        with app.app_context():
            # Create a test user
            user = Usuario()
            user.usuario = "testuser_auth2"
            user.acceso = proteger_passwd("testpass")
            user.nombre = "Test"
            user.apellido = "User"
            user.tipo = "user"
            user.activo = True
            db.session.add(user)
            db.session.commit()

            # Test invalid password
            result = validar_acceso("testuser_auth2", "wrongpass")
            assert result is False

    def test_validar_acceso_nonexistent_user(self, app):
        """Test validar_acceso with non-existent user."""
        from coati_payroll.auth import validar_acceso

        with app.app_context():
            # Test non-existent user
            result = validar_acceso("nonexistent_user", "anypass")
            assert result is False

    def test_validar_acceso_by_email(self, app):
        """Test validar_acceso with email instead of username."""
        from coati_payroll.auth import validar_acceso, proteger_passwd
        from coati_payroll.model import Usuario, db

        with app.app_context():
            # Create a test user with email
            user = Usuario()
            user.usuario = "testuser_auth3"
            user.correo_electronico = "test@example.com"
            user.acceso = proteger_passwd("testpass")
            user.nombre = "Test"
            user.apellido = "User"
            user.tipo = "user"
            user.activo = True
            db.session.add(user)
            db.session.commit()

            # Test with email
            result = validar_acceso("test@example.com", "testpass")
            assert result is True


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_get(self, client):
        """Test GET request to login page."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"login" in response.data.lower() or b"email" in response.data.lower()

    def test_login_post_valid(self, app, client):
        """Test POST to login with valid credentials."""
        from coati_payroll.auth import proteger_passwd
        from coati_payroll.model import Usuario, db

        with app.app_context():
            # Create a test user
            user = Usuario()
            user.usuario = "testuser_login"
            user.acceso = proteger_passwd("testpass")
            user.nombre = "Test"
            user.apellido = "User"
            user.tipo = "user"
            user.activo = True
            db.session.add(user)
            db.session.commit()

        # Try to login
        response = client.post(
            "/auth/login",
            data={"email": "testuser_login", "password": "testpass"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_login_post_invalid(self, client):
        """Test POST to login with invalid credentials."""
        response = client.post(
            "/auth/login",
            data={"email": "nonexistent", "password": "wrongpass"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_logout_redirects(self, authenticated_client):
        """Test logout redirects to login."""
        response = authenticated_client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
