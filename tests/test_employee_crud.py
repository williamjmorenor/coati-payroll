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
"""Tests for Employee CRUD operations."""

import pytest


class TestEmployeeCRUD:
    """Test CRUD operations for Employee."""

    def test_employee_pagination(self, app, authenticated_client):
        """Test employee list with pagination."""
        response = authenticated_client.get("/employee/?page=1")
        assert response.status_code == 200

    def test_employee_new_loads_with_custom_fields(self, app, authenticated_client):
        """Test that new employee form loads with custom fields."""
        with app.app_context():
            from coati_payroll.model import db, CampoPersonalizado

            # Create custom field
            campo = CampoPersonalizado()
            campo.nombre_campo = "test_field"
            campo.etiqueta = "Test Field"
            campo.tipo_dato = "texto"
            campo.orden = 1
            campo.activo = True
            campo.creado_por = "test"
            db.session.add(campo)
            db.session.commit()

            response = authenticated_client.get("/employee/new")
            assert response.status_code == 200
            assert b"test_field" in response.data or b"Test Field" in response.data

    def test_employee_edit_nonexistent_redirects(self, app, authenticated_client):
        """Test that editing nonexistent employee redirects."""
        response = authenticated_client.get(
            "/employee/edit/nonexistent-id-99999",
            follow_redirects=False
        )
        # Should redirect or return 404, not crash
        assert response.status_code in (302, 404)
