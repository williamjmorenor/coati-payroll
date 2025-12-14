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
"""Tests for User CRUD operations."""

import pytest


class TestUserCRUD:
    """Test CRUD operations for User."""

    def test_user_new_form_loads(self, app, authenticated_client):
        """Test that new user form loads."""
        response = authenticated_client.get("/user/new")
        assert response.status_code == 200

    def test_user_pagination(self, app, authenticated_client):
        """Test user list with pagination."""
        response = authenticated_client.get("/user/?page=1")
        assert response.status_code == 200

    def test_create_user(self, app, authenticated_client):
        """Test creating a new user."""
        with app.app_context():
            from coati_payroll.model import db, Usuario

            response = authenticated_client.post(
                "/user/new",
                data={
                    "usuario": "newuser",
                    "nombre": "New",
                    "apellido": "User",
                    "correo_electronico": "newuser@test.com",
                    "password": "testpass123",
                    "confirm_password": "testpass123",
                    "tipo": "hhrr",
                    "activo": "y",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            # Verify user was created
            user = db.session.execute(db.select(Usuario).filter_by(usuario="newuser")).scalar_one_or_none()
            assert user is not None
            assert user.nombre == "New"
            assert user.tipo == "hhrr"

    def test_profile_page_loads(self, app, authenticated_client):
        """Test that profile page loads."""
        response = authenticated_client.get("/user/profile")
        assert response.status_code == 200

    def test_profile_update_without_password(self, app, authenticated_client):
        """Test updating profile without changing password."""
        response = authenticated_client.post(
            "/user/profile",
            data={
                "nombre": "Updated",
                "apellido": "Name",
                "correo_electronico": "updated@test.com",
                "current_password": "",
                "new_password": "",
                "confirm_password": "",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
