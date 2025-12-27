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

from __future__ import annotations

from datetime import date

import pytest

from coati_payroll.formula_engine import EXAMPLE_IR_NICARAGUA_SCHEMA
from coati_payroll.model import ReglaCalculo
from tests.helpers.auth import login_user


@pytest.mark.validation
def test_calculation_rule_create_and_save_schema(app, client, admin_user, db_session):
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        resp = client.post(
            "/calculation-rule/new",
            data={
                "codigo": "IR_VAL",
                "nombre": "IR Validation",
                "descripcion": "Test rule",
                "jurisdiccion": "Nicaragua",
                "moneda_referencia": "NIO",
                "version": "1.0.0",
                "tipo_regla": "impuesto",
                "vigente_desde": date.today().isoformat(),
                "activo": "y",
                "submit": "Guardar",
            },
            follow_redirects=False,
        )

        assert resp.status_code == 302

        rule = db_session.query(ReglaCalculo).filter(ReglaCalculo.codigo == "IR_VAL").one_or_none()
        assert rule is not None

        # Save schema via API
        resp = client.post(f"/calculation-rule/api/save-schema/{rule.id}", json={"schema": EXAMPLE_IR_NICARAGUA_SCHEMA})
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload is not None
        assert payload.get("success") is True

        # Test schema execution endpoint
        resp = client.post(
            f"/calculation-rule/api/test-schema/{rule.id}",
            json={"schema": EXAMPLE_IR_NICARAGUA_SCHEMA, "inputs": {}},
        )
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload is not None
        assert payload.get("success") is True


@pytest.mark.validation
def test_calculation_rule_delete(app, client, admin_user, db_session):
    with app.app_context():
        rule = ReglaCalculo(
            codigo="DEL_VAL",
            nombre="Delete Validation",
            version="1.0.0",
            tipo_regla="impuesto",
            vigente_desde=date.today(),
            activo=True,
            esquema_json={},
            creado_por="test",
        )
        db_session.add(rule)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        resp = client.post(f"/calculation-rule/delete/{rule.id}", follow_redirects=False)
        assert resp.status_code == 302

        deleted = db_session.get(ReglaCalculo, rule.id)
        assert deleted is None
