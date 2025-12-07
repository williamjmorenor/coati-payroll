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
"""Tests for Payroll Concepts (Perceptions, Deductions, Benefits) CRUD operations."""

import pytest


class TestPercepcionCRUD:
    """Test CRUD operations for Percepcion."""

    def test_percepcion_new_form_loads(self, app, authenticated_client):
        """Test that new percepcion form loads."""
        response = authenticated_client.get("/percepciones/new")
        assert response.status_code == 200

    def test_percepcion_pagination(self, app, authenticated_client):
        """Test percepcion list with pagination."""
        response = authenticated_client.get("/percepciones/?page=1")
        assert response.status_code == 200


class TestDeduccionCRUD:
    """Test CRUD operations for Deduccion."""

    def test_deduccion_new_form_loads(self, app, authenticated_client):
        """Test that new deduccion form loads."""
        response = authenticated_client.get("/deducciones/new")
        assert response.status_code == 200

    def test_deduccion_pagination(self, app, authenticated_client):
        """Test deduccion list with pagination."""
        response = authenticated_client.get("/deducciones/?page=1")
        assert response.status_code == 200


class TestPrestacionCRUD:
    """Test CRUD operations for Prestacion."""

    def test_prestacion_index_loads(self, app, authenticated_client):
        """Test that prestacion index page loads."""
        response = authenticated_client.get("/prestaciones/")
        assert response.status_code == 200

    def test_prestacion_new_form_loads(self, app, authenticated_client):
        """Test that new prestacion form loads."""
        response = authenticated_client.get("/prestaciones/new")
        assert response.status_code == 200

    def test_prestacion_pagination(self, app, authenticated_client):
        """Test prestacion list with pagination."""
        response = authenticated_client.get("/prestaciones/?page=1")
        assert response.status_code == 200
