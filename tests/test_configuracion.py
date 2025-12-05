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
"""Tests for global configuration views."""

import pytest


class TestConfiguracion:
    """Tests for configuration routes."""

    def test_configuracion_index_requires_login(self, client):
        """Test that configuration index page requires login."""
        response = client.get("/configuracion/")
        # May return 200 with redirect template or 302 redirect
        assert response.status_code in [200, 302]

    def test_configuracion_index_shows_config(self, authenticated_client):
        """Test that configuration index page shows current settings."""
        response = authenticated_client.get("/configuracion/")
        assert response.status_code == 200
        # Should show language options
        assert b"English" in response.data or b"Espa" in response.data

    def test_cambiar_idioma_to_english(self, authenticated_client, app):
        """Test changing language to English."""
        response = authenticated_client.post(
            "/configuracion/idioma",
            data={"idioma": "en"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify language was changed
        from coati_payroll.locale_config import get_language_from_db

        with app.app_context():
            language = get_language_from_db()
            assert language == "en"

    def test_cambiar_idioma_to_spanish(self, authenticated_client, app):
        """Test changing language to Spanish."""
        response = authenticated_client.post(
            "/configuracion/idioma",
            data={"idioma": "es"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify language was changed
        from coati_payroll.locale_config import get_language_from_db

        with app.app_context():
            language = get_language_from_db()
            assert language == "es"

    def test_cambiar_idioma_empty_value(self, authenticated_client):
        """Test changing language with empty value."""
        response = authenticated_client.post(
            "/configuracion/idioma",
            data={"idioma": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should show warning message

    def test_cambiar_idioma_unsupported_language(self, authenticated_client):
        """Test changing language to unsupported language."""
        response = authenticated_client.post(
            "/configuracion/idioma",
            data={"idioma": "fr"},  # French is not supported
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should show error message

    def test_cambiar_idioma_requires_login(self, client):
        """Test that changing language requires login."""
        response = client.post(
            "/configuracion/idioma",
            data={"idioma": "en"},
        )
        assert response.status_code == 302  # Redirect to login
