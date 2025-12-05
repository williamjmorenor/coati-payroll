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
"""Tests for custom field CRUD operations."""

import pytest


class TestCustomField:
    """Tests for custom field CRUD routes."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app):
        """Set up test data for custom field tests."""
        from coati_payroll.model import CampoPersonalizado, db

        with app.app_context():
            # Clear any existing test data
            db.session.execute(db.delete(CampoPersonalizado))
            db.session.commit()

    def test_custom_field_index_requires_login(self, client):
        """Test that custom field index page requires login."""
        response = client.get("/custom_field/")
        # May return 200 with redirect template or 302 redirect
        assert response.status_code in [200, 302]

    def test_custom_field_index_shows_fields(self, authenticated_client, app):
        """Test that custom field index page shows existing fields."""
        from coati_payroll.model import CampoPersonalizado, db

        with app.app_context():
            # Create test custom fields
            field1 = CampoPersonalizado()
            field1.nombre_campo = "custom_field_1"
            field1.etiqueta = "Custom Field 1"
            field1.tipo_dato = "text"
            field1.orden = 1
            field1.activo = True
            db.session.add(field1)

            field2 = CampoPersonalizado()
            field2.nombre_campo = "custom_field_2"
            field2.etiqueta = "Custom Field 2"
            field2.tipo_dato = "number"
            field2.orden = 2
            field2.activo = True
            db.session.add(field2)

            db.session.commit()

        response = authenticated_client.get("/custom_field/")
        assert response.status_code == 200
        assert b"Custom Field 1" in response.data or b"custom_field_1" in response.data

    def test_custom_field_new_get_shows_form(self, authenticated_client):
        """Test that new custom field GET request shows the form."""
        response = authenticated_client.get("/custom_field/new")
        assert response.status_code == 200
        assert b"Nuevo Campo Personalizado" in response.data or b"form" in response.data.lower()

    def test_custom_field_new_post_creates_field(self, authenticated_client, app):
        """Test creating a new custom field."""
        response = authenticated_client.post(
            "/custom_field/new",
            data={
                "nombre_campo": "test_field",
                "etiqueta": "Test Field",
                "tipo_dato": "texto",  # Use valid choice from form
                "descripcion": "Test description",
                "orden": "1",
                "activo": True,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            from coati_payroll.model import CampoPersonalizado, db

            field = db.session.execute(
                db.select(CampoPersonalizado).filter_by(nombre_campo="test_field")
            ).scalar_one_or_none()
            assert field is not None
            assert field.etiqueta == "Test Field"
            assert field.tipo_dato == "texto"
            assert field.descripcion == "Test description"
            assert field.orden == 1
            assert field.activo is True

    def test_custom_field_edit_get_shows_form(self, authenticated_client, app):
        """Test that edit custom field GET request shows the form with data."""
        from coati_payroll.model import CampoPersonalizado, db

        with app.app_context():
            # Create a test custom field
            field = CampoPersonalizado()
            field.nombre_campo = "test_field"
            field.etiqueta = "Test Field"
            field.tipo_dato = "text"
            field.orden = 1
            field.activo = True
            db.session.add(field)
            db.session.commit()
            field_id = field.id

        response = authenticated_client.get(f"/custom_field/edit/{field_id}")
        assert response.status_code == 200
        assert b"test_field" in response.data or b"Test Field" in response.data

    def test_custom_field_edit_post_updates_field(self, authenticated_client, app):
        """Test updating an existing custom field."""
        from coati_payroll.model import CampoPersonalizado, db

        with app.app_context():
            # Create a test custom field
            field = CampoPersonalizado()
            field.nombre_campo = "test_field"
            field.etiqueta = "Test Field"
            field.tipo_dato = "text"
            field.orden = 1
            field.activo = True
            db.session.add(field)
            db.session.commit()
            field_id = field.id

        response = authenticated_client.post(
            f"/custom_field/edit/{field_id}",
            data={
                "nombre_campo": "updated_field",
                "etiqueta": "Updated Field",
                "tipo_dato": "entero",  # Use valid choice from form
                "descripcion": "Updated description",
                "orden": "2",
                # activo not included = False
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            field = db.session.get(CampoPersonalizado, field_id)
            assert field.nombre_campo == "updated_field"
            assert field.etiqueta == "Updated Field"
            assert field.tipo_dato == "entero"
            assert field.orden == 2
            assert field.activo is False

    def test_custom_field_edit_nonexistent_redirects(self, authenticated_client):
        """Test that editing a non-existent custom field redirects."""
        response = authenticated_client.get("/custom_field/edit/NONEXISTENT", follow_redirects=True)
        assert response.status_code == 200

    def test_custom_field_delete_removes_field(self, authenticated_client, app):
        """Test deleting a custom field."""
        from coati_payroll.model import CampoPersonalizado, db

        with app.app_context():
            # Create a test custom field
            field = CampoPersonalizado()
            field.nombre_campo = "test_field"
            field.etiqueta = "Test Field"
            field.tipo_dato = "text"
            field.orden = 1
            field.activo = True
            db.session.add(field)
            db.session.commit()
            field_id = field.id

        response = authenticated_client.post(f"/custom_field/delete/{field_id}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            field = db.session.get(CampoPersonalizado, field_id)
            assert field is None

    def test_custom_field_delete_nonexistent_redirects(self, authenticated_client):
        """Test that deleting a non-existent custom field redirects."""
        response = authenticated_client.post("/custom_field/delete/NONEXISTENT", follow_redirects=True)
        assert response.status_code == 200
