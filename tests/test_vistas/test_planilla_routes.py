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
"""Tests for planilla (payroll) routes."""

from tests.helpers.auth import login_user


def test_planilla_index_requires_authentication(app, client, db_session):
    """Test that planilla index requires authentication."""
    with app.app_context():
        response = client.get("/planilla/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_index_for_admin(app, client, admin_user, db_session):
    """Test that admin can access planilla index."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        response = client.get("/planilla/")
        assert response.status_code == 200


def test_planilla_new_requires_authentication(app, client, db_session):
    """Test that creating a new planilla requires authentication."""
    with app.app_context():
        response = client.get("/planilla/new", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_new_requires_write_access(app, client, db_session):
    """Test that creating a new planilla requires write access."""
    with app.app_context():
        from coati_payroll.enums import TipoUsuario
        from tests.factories.user_factory import create_user

        # Create AUDIT user (read-only)
        audit_user = create_user(db_session, "auditor", "password", tipo=TipoUsuario.AUDIT)
        login_user(client, audit_user.usuario, "password")

        response = client.get("/planilla/new", follow_redirects=False)
        # Should not allow access (403 or redirect)
        assert response.status_code in [302, 403]


def test_planilla_edit_requires_authentication(app, client, db_session):
    """Test that editing a planilla requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/edit", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_config_requires_authentication(app, client, db_session):
    """Test that accessing planilla config requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/config", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_nomina_list_requires_authentication(app, client, db_session):
    """Test that nomina list requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/nominas", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_nomina_view_requires_authentication(app, client, db_session):
    """Test that viewing nomina requires authentication."""
    with app.app_context():
        response = client.get("/planilla/999/nomina/888", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


def test_planilla_ejecutar_requires_authentication(app, client, db_session):
    """Test that executing planilla requires authentication."""
    with app.app_context():
        response = client.post("/planilla/999/ejecutar", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location
