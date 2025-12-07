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
"""Tests for Planilla CRUD operations."""

import pytest
from datetime import date


class TestPlanillaCRUD:
    """Test CRUD operations for Planilla."""

    def test_planilla_index_loads(self, app, authenticated_client):
        """Test that planilla index page loads."""
        response = authenticated_client.get("/planilla/")
        assert response.status_code == 200

    def test_planilla_new_form_loads(self, app, authenticated_client):
        """Test that new planilla form loads."""
        response = authenticated_client.get("/planilla/new")
        assert response.status_code == 200

    def test_create_planilla(self, app, authenticated_client):
        """Test creating a new planilla."""
        with app.app_context():
            from coati_payroll.model import db, Planilla, Moneda, TipoPlanilla, Empresa

            # Get or create required entities
            moneda = db.session.execute(db.select(Moneda).filter_by(activo=True)).scalars().first()
            if not moneda:
                moneda = Moneda()
                moneda.codigo = "TEST_CUR"
                moneda.nombre = "Test Currency"
                moneda.simbolo = "T$"
                moneda.activo = True
                moneda.creado_por = "test"
                db.session.add(moneda)
                db.session.commit()

            tipo = TipoPlanilla()
            tipo.codigo = "TEST_TIPO"
            tipo.descripcion = "Test Type"
            tipo.periodicidad = "mensual"
            tipo.creado_por = "test"
            db.session.add(tipo)
            db.session.commit()

            empresa = Empresa()
            empresa.codigo = "TEST_EMP_PL"
            empresa.razon_social = "Test Empresa"
            empresa.ruc = "J1111111111111"
            empresa.activo = True
            empresa.creado_por = "test"
            db.session.add(empresa)
            db.session.commit()

            response = authenticated_client.post(
                "/planilla/new",
                data={
                    "nombre": "Test Planilla",
                    "descripcion": "Test planilla description",
                    "tipo_planilla_id": str(tipo.id),
                    "moneda_id": str(moneda.id),
                    "empresa_id": str(empresa.id),
                    "periodo_fiscal_inicio": "2024-01-01",
                    "periodo_fiscal_fin": "2024-12-31",
                    "prioridad_prestamos": "250",
                    "prioridad_adelantos": "251",
                    "activo": "y",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            # Verify planilla was created
            planilla = db.session.execute(
                db.select(Planilla).filter_by(nombre="Test Planilla")
            ).scalar_one_or_none()
            assert planilla is not None

    def test_planilla_config_empleados_loads(self, app, authenticated_client):
        """Test that planilla empleados config page loads."""
        with app.app_context():
            from coati_payroll.model import db, Planilla, Moneda, TipoPlanilla

            moneda = db.session.execute(db.select(Moneda).filter_by(activo=True)).scalars().first()
            tipo = db.session.execute(db.select(TipoPlanilla)).scalars().first()

            if not tipo:
                tipo = TipoPlanilla()
                tipo.codigo = "CFG_TIPO"
                tipo.descripcion = "Config Type"
                tipo.periodicidad = "mensual"
                tipo.creado_por = "test"
                db.session.add(tipo)
                db.session.commit()

            planilla = Planilla()
            planilla.nombre = "Config Test"
            planilla.descripcion = "For config testing"
            planilla.tipo_planilla_id = tipo.id
            planilla.moneda_id = moneda.id if moneda else None
            planilla.periodo_fiscal_inicio = date(2024, 1, 1)
            planilla.periodo_fiscal_fin = date(2024, 12, 31)
            planilla.activo = True
            planilla.creado_por = "test"
            db.session.add(planilla)
            db.session.commit()

            # Load config pages
            response = authenticated_client.get(f"/planilla/{planilla.id}/config/empleados")
            assert response.status_code == 200

    def test_planilla_list_with_pagination(self, app, authenticated_client):
        """Test planilla list with pagination."""
        response = authenticated_client.get("/planilla/?page=1")
        assert response.status_code == 200
