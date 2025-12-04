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
"""
Tests to verify all routes render without template errors (404/500).

This test module automatically visits all routes exposed by the Flask application
using Flask's test client to ensure there are no 404 or 500 errors, particularly
template rendering errors like TemplateNotFound.
"""

import re


class TestRouteRendering:
    """Tests to verify all routes render correctly without server errors."""

    def get_all_routes(self, app):
        """Get all routes from the Flask application.

        Returns a list of tuples: (endpoint, methods, rule_pattern)
        """
        routes = []
        for rule in app.url_map.iter_rules():
            # Skip static routes
            if rule.endpoint == "static":
                continue
            # Get methods excluding OPTIONS and HEAD
            methods = rule.methods - {"OPTIONS", "HEAD"}
            routes.append((rule.endpoint, methods, str(rule)))
        return routes

    def generate_test_url(self, rule_pattern: str) -> str:
        """Generate a test URL from a rule pattern by replacing dynamic segments.

        Flask uses patterns like <string:id>, <int:id>, <planilla_id>, etc.
        This method replaces them with test values.
        """
        # Pattern for Flask URL parameters
        # Matches: <type:name>, <name>, etc.
        param_pattern = re.compile(r"<(?:\w+:)?(\w+)>")

        def replace_param(match):  # pylint: disable=unused-argument
            # Use a placeholder test ID for all dynamic parameters
            # Using 'test-id-12345' as a non-existent ID to test 404 handling
            return "test-id-12345"

        return param_pattern.sub(replace_param, rule_pattern)

    def test_unauthenticated_routes_redirect_to_login(self, app, client):
        """Test that protected routes redirect unauthenticated users to login.

        All routes (except auth.login and auth.logout) should redirect
        to the login page when accessed without authentication.
        """
        with app.app_context():
            routes = self.get_all_routes(app)

            for endpoint, methods, rule_pattern in routes:
                # Skip auth routes as they are meant for unauthenticated users
                if endpoint.startswith("auth."):
                    continue

                if "GET" in methods:
                    url = self.generate_test_url(rule_pattern)
                    response = client.get(url)

                    # Should redirect to login (302) or be forbidden (401/403)
                    assert response.status_code in (
                        302,
                        401,
                        403,
                    ), f"Route {endpoint} ({url}) returned {response.status_code}, expected redirect to login"

    def test_auth_login_renders(self, app, client):
        """Test that the login page renders without errors."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        response_lower = response.data.decode("utf-8", errors="ignore").lower()
        assert "login" in response_lower or "sesión" in response_lower

    def test_authenticated_index_routes_render(self, app, authenticated_client):
        """Test that main index routes render correctly for authenticated users.

        This tests the primary listing/index routes that don't require
        specific database records.
        """
        with app.app_context():
            # Index routes that should work without specific data
            index_routes = [
                ("/", "app.index"),
                ("/user/", "user.index"),
                ("/currency/", "currency.index"),
                ("/exchange_rate/", "exchange_rate.index"),
                ("/employee/", "employee.index"),
                ("/custom_field/", "custom_field.index"),
                ("/calculation-rule/", "calculation_rule.index"),
                ("/percepciones/", "percepcion.index"),
                ("/deducciones/", "deduccion.index"),
                ("/prestaciones/", "prestacion.index"),
                ("/planilla/", "planilla.index"),
            ]

            for url, endpoint in index_routes:
                response = authenticated_client.get(url)
                # Should return 200 OK
                assert response.status_code == 200, (
                    f"Route {endpoint} ({url}) returned {response.status_code}, "
                    f"expected 200. Response data: {response.data[:500]}"
                )

    def test_authenticated_new_form_routes_render(self, app, authenticated_client):
        """Test that 'new' form routes render correctly for authenticated users.

        These routes display forms for creating new records.
        """
        with app.app_context():
            new_routes = [
                ("/user/new", "user.new"),
                ("/currency/new", "currency.new"),
                ("/exchange_rate/new", "exchange_rate.new"),
                ("/employee/new", "employee.new"),
                ("/custom_field/new", "custom_field.new"),
                ("/calculation-rule/new", "calculation_rule.new"),
                ("/percepciones/new", "percepcion.new"),
                ("/deducciones/new", "deduccion.new"),
                ("/prestaciones/new", "prestacion.new"),
                ("/planilla/new", "planilla.new"),
            ]

            for url, endpoint in new_routes:
                response = authenticated_client.get(url)
                # Should return 200 OK (form rendered)
                assert response.status_code == 200, (
                    f"Route {endpoint} ({url}) returned {response.status_code}, "
                    f"expected 200. Response data: {response.data[:500]}"
                )

    def test_edit_routes_with_nonexistent_id_handle_gracefully(
        self, app, authenticated_client
    ):
        """Test that edit routes handle non-existent IDs gracefully.

        When accessing an edit route with a non-existent ID, the application
        should redirect (to index) with a flash message, not return 500.
        """
        with app.app_context():
            # Edit routes with dynamic ID parameter
            edit_routes = [
                ("/user/edit/nonexistent-id-12345", "user.edit"),
                ("/currency/edit/nonexistent-id-12345", "currency.edit"),
                ("/exchange_rate/edit/nonexistent-id-12345", "exchange_rate.edit"),
                ("/employee/edit/nonexistent-id-12345", "employee.edit"),
                ("/custom_field/edit/nonexistent-id-12345", "custom_field.edit"),
                (
                    "/calculation-rule/edit/nonexistent-id-12345",
                    "calculation_rule.edit",
                ),
                ("/percepciones/edit/nonexistent-id-12345", "percepcion.edit"),
                ("/deducciones/edit/nonexistent-id-12345", "deduccion.edit"),
                ("/prestaciones/edit/nonexistent-id-12345", "prestacion.edit"),
            ]

            for url, endpoint in edit_routes:
                response = authenticated_client.get(url)
                # Should redirect (302) to index or show not found gracefully
                # Should NOT return 500 (server error)
                assert response.status_code != 500, (
                    f"Route {endpoint} ({url}) returned 500 server error. "
                    f"Response data: {response.data[:500]}"
                )
                # Accept 200 (if form shown with error), 302 (redirect), or 404
                assert response.status_code in (200, 302, 404), (
                    f"Route {endpoint} ({url}) returned {response.status_code}, "
                    f"expected 200, 302, or 404"
                )

    def test_all_get_routes_no_server_errors(self, app, authenticated_client):
        """Test that all GET routes don't return 500 server errors.

        This is a comprehensive test that visits all GET routes to ensure
        no template errors (TemplateNotFound) or other server errors occur.
        """
        with app.app_context():
            routes = self.get_all_routes(app)
            errors = []

            for endpoint, methods, rule_pattern in routes:
                if "GET" not in methods:
                    continue

                url = self.generate_test_url(rule_pattern)
                response = authenticated_client.get(url)

                # 500 server error indicates template or code errors
                if response.status_code == 500:
                    errors.append(
                        f"{endpoint} ({url}): returned 500 - {response.data[:200]}"
                    )

            # Report all errors at once for better debugging
            assert (
                not errors
            ), "The following routes returned 500 server errors:\n" + "\n".join(errors)


class TestTemplateRendering:
    """Tests to verify templates render without TemplateNotFound errors."""

    def test_templates_use_correct_macro_imports(self, app, authenticated_client):
        """Test that templates import macros correctly.

        The issue mentions TemplateNotFound: macros/form_helpers.html
        This test verifies that templates can load and render their macros.
        """
        with app.app_context():
            # Test routes that use form templates (which import macros)
            form_routes = [
                "/auth/login",
                "/user/new",
                "/currency/new",
                "/employee/new",
                "/calculation-rule/new",
            ]

            for url in form_routes:
                # For login, we don't need authentication
                if url == "/auth/login":
                    with app.test_client() as temp_client:
                        response = temp_client.get(url)
                else:
                    response = authenticated_client.get(url)

                # Check that the response doesn't contain template error indicators
                assert response.status_code != 500, (
                    f"Route {url} returned 500, possible template error. "
                    f"Response: {response.data[:500]}"
                )

                # Check for common error messages in response
                response_text = response.data.decode("utf-8", errors="ignore").lower()
                assert (
                    "templatenotfound" not in response_text
                ), f"Route {url} has TemplateNotFound error in response"
                assert (
                    "jinja2.exceptions" not in response_text
                ), f"Route {url} has Jinja2 exception in response"


class TestProfileRoute:
    """Tests for the user profile functionality."""

    def test_profile_route_renders_for_authenticated_users(
        self, app, authenticated_client
    ):
        """Test that the profile route renders correctly for authenticated users."""
        response = authenticated_client.get("/user/profile")
        assert response.status_code == 200

        response_text = response.data.decode("utf-8", errors="ignore")
        # Check for profile-related content
        assert "Mi Perfil" in response_text or "perfil" in response_text.lower()
        assert "Contraseña" in response_text or "contraseña" in response_text.lower()

    def test_profile_route_requires_authentication(self, app):
        """Test that unauthenticated users are redirected to login.

        Note: This test is covered by test_unauthenticated_routes_redirect_to_login
        which tests all protected routes including /user/profile.
        """
        # Create a fresh client with a new session
        with app.test_client() as fresh_client:
            # First, explicitly logout by visiting logout URL
            fresh_client.get("/auth/logout", follow_redirects=False)
            # Now test that profile requires auth
            response = fresh_client.get("/user/profile", follow_redirects=False)
            # Should redirect to login (302)
            assert response.status_code == 302
            assert "/auth/login" in response.location

    def test_profile_update_basic_info(self, app, authenticated_client):
        """Test updating basic profile information without password change."""
        response = authenticated_client.post(
            "/user/profile",
            data={
                "nombre": "Updated Name",
                "apellido": "Updated Lastname",
                "correo_electronico": "updated@example.com",
                "current_password": "",
                "new_password": "",
                "confirm_password": "",
                "submit": "Actualizar Perfil",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        response_text = response.data.decode("utf-8", errors="ignore").lower()
        # Should show success message or profile page
        assert "actualizado" in response_text or "updated name" in response_text

    def test_profile_password_change_requires_current_password(
        self, app, authenticated_client
    ):
        """Test that password change requires correct current password."""
        response = authenticated_client.post(
            "/user/profile",
            data={
                "nombre": "Test",
                "apellido": "User",
                "correo_electronico": "test@example.com",
                "current_password": "wrong-password",
                "new_password": "newpass123",
                "confirm_password": "newpass123",
                "submit": "Actualizar Perfil",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        response_text = response.data.decode("utf-8", errors="ignore").lower()
        # Should show error about incorrect current password
        assert "incorrecta" in response_text or "incorrect" in response_text

    def test_profile_password_change_requires_matching_passwords(
        self, app, authenticated_client
    ):
        """Test that new password and confirmation must match."""
        response = authenticated_client.post(
            "/user/profile",
            data={
                "nombre": "Test",
                "apellido": "User",
                "correo_electronico": "test@example.com",
                "current_password": "testpassword",
                "new_password": "newpass123",
                "confirm_password": "different123",
                "submit": "Actualizar Perfil",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        response_text = response.data.decode("utf-8", errors="ignore").lower()
        # Should show error about passwords not matching
        assert "coinciden" in response_text or "match" in response_text

    def test_profile_password_change_requires_current_password_when_new_provided(
        self, app, authenticated_client
    ):
        """Test that providing new password without current password shows error."""
        response = authenticated_client.post(
            "/user/profile",
            data={
                "nombre": "Test",
                "apellido": "User",
                "correo_electronico": "test@example.com",
                "current_password": "",
                "new_password": "newpass123",
                "confirm_password": "newpass123",
                "submit": "Actualizar Perfil",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        response_text = response.data.decode("utf-8", errors="ignore").lower()
        # Should show error about current password being required
        assert "actual" in response_text or "current" in response_text
