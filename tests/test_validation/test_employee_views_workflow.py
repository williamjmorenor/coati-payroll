# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest


from coati_payroll.enums import TipoUsuario
from coati_payroll.model import Empleado, Empresa, Moneda
from tests.factories.user_factory import create_user
from tests.helpers.auth import login_user


def _create_empresa_moneda(db_session):
    empresa = Empresa(codigo="EMPVAL", razon_social="Employee Co", ruc="J-EMP", activo=True)
    moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
    db_session.add(empresa)
    db_session.add(moneda)
    db_session.commit()
    return empresa, moneda


@pytest.mark.validation
def test_employee_index_get(app, client, admin_user, db_session):
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        resp = client.get("/employee/")
        assert resp.status_code == 200


@pytest.mark.validation
def test_employee_new_post_creates_employee(app, client, db_session):
    with app.app_context():
        # Use HHRR user (write access)
        hr_user = create_user(db_session, "hr-emp", "password", tipo=TipoUsuario.HHRR)
        empresa, moneda = _create_empresa_moneda(db_session)

        login_user(client, hr_user.usuario, "password")

        resp = client.post(
            "/employee/new",
            data={
                "codigo_empleado": "EMP-VAL-001",
                "primer_nombre": "Ana",
                "segundo_nombre": "",
                "primer_apellido": "García",
                "segundo_apellido": "",
                "identificacion_personal": "001-020202-0002B",
                "fecha_alta": date.today().isoformat(),
                "salario_base": "1234.56",
                # Optional select fields: send empty or valid IDs to avoid "Not a valid choice"
                "moneda_id": str(moneda.id),
                "empresa_id": str(empresa.id),
                "submit": "Guardar",
            },
            follow_redirects=False,
        )

        assert resp.status_code == 302

        created = db_session.query(Empleado).filter(Empleado.codigo_empleado == "EMP-VAL-001").one_or_none()
        assert created is not None


@pytest.mark.validation
def test_employee_edit_and_delete_workflow(app, client, db_session):
    with app.app_context():
        hr_user = create_user(db_session, "hr-emp2", "password", tipo=TipoUsuario.HHRR)
        empresa, moneda = _create_empresa_moneda(db_session)

        emp = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP-VAL-002",
            primer_nombre="Luis",
            primer_apellido="Pérez",
            identificacion_personal="001-030303-0003C",
            fecha_alta=date.today(),
            salario_base=Decimal("1000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(emp)
        db_session.commit()

        login_user(client, hr_user.usuario, "password")

        # Edit
        resp = client.post(
            f"/employee/edit/{emp.id}",
            data={
                "codigo_empleado": "EMP-VAL-002",
                "primer_nombre": "Luis Updated",
                "segundo_nombre": "",
                "primer_apellido": "Pérez",
                "segundo_apellido": "",
                "identificacion_personal": "001-030303-0003C",
                "fecha_alta": date.today().isoformat(),
                "salario_base": "2000.00",
                "moneda_id": str(moneda.id),
                "empresa_id": str(empresa.id),
                "submit": "Guardar",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

        # Basic smoke check that list page still renders after update
        resp = client.get("/employee/")
        assert resp.status_code == 200

        # Delete
        resp = client.post(f"/employee/delete/{emp.id}", follow_redirects=False)
        assert resp.status_code == 302

        # Smoke check that list page still renders after delete
        resp = client.get("/employee/")
        assert resp.status_code == 200
