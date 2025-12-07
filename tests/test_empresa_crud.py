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
"""Tests for Empresa (Company) CRUD operations."""

import pytest


class TestEmpresaCRUD:
    """Test CRUD operations for Empresa."""

    def test_empresa_index_loads(self, app, authenticated_client):
        """Test that empresa index page loads."""
        response = authenticated_client.get("/empresa/")
        assert response.status_code == 200

    def test_empresa_new_form_loads(self, app, authenticated_client):
        """Test that new empresa form loads."""
        response = authenticated_client.get("/empresa/new")
        assert response.status_code == 200

    def test_create_empresa(self, app, authenticated_client):
        """Test creating a new empresa."""
        with app.app_context():
            from coati_payroll.model import db, Empresa

            response = authenticated_client.post(
                "/empresa/new",
                data={
                    "codigo": "TEST_EMP",
                    "razon_social": "Test Company S.A.",
                    "ruc": "J9999999999999",
                    "direccion": "Test Address",
                    "telefono": "+505 1234 5678",
                    "correo": "test@company.com",
                    "activo": "y",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            # Verify empresa was created
            empresa = db.session.execute(db.select(Empresa).filter_by(codigo="TEST_EMP")).scalar_one_or_none()
            assert empresa is not None
            assert empresa.razon_social == "Test Company S.A."
            assert empresa.ruc == "J9999999999999"

    def test_empresa_list_with_data(self, app, authenticated_client):
        """Test that empresa list shows created empresas."""
        with app.app_context():
            from coati_payroll.model import db, Empresa

            # Create empresa
            empresa = Empresa()
            empresa.codigo = "LIST_TEST"
            empresa.razon_social = "List Test Company"
            empresa.ruc = "J8888888888888"
            empresa.activo = True
            empresa.creado_por = "test"
            db.session.add(empresa)
            db.session.commit()

            # View list
            response = authenticated_client.get("/empresa/")
            assert response.status_code == 200
            assert b"LIST_TEST" in response.data
