# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Tests for salary change draft/approval/application workflow."""

from datetime import date
from decimal import Decimal

from coati_payroll.model import Empleado, Empresa, HistorialSalario, db
from tests.helpers.auth import login_user


def _create_company(db_session, codigo: str) -> Empresa:
    empresa = Empresa(
        codigo=codigo,
        razon_social=f"Empresa {codigo}",
        ruc=f"RUC-{codigo}",
    )
    db_session.add(empresa)
    db_session.commit()
    db_session.refresh(empresa)
    return empresa


def _create_employee(db_session, empresa_id: str, codigo: str, salario: Decimal) -> Empleado:
    empleado = Empleado(
        codigo_empleado=codigo,
        primer_nombre="Ana",
        primer_apellido="Pérez",
        identificacion_personal=f"ID-{codigo}",
        fecha_alta=date(2024, 1, 1),
        salario_base=salario,
        empresa_id=empresa_id,
    )
    db_session.add(empleado)
    db_session.commit()
    db_session.refresh(empleado)
    return empleado


def test_salary_change_full_workflow(app, client, admin_user, db_session):
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        empresa = _create_company(db_session, "EMP-A")
        empleado = _create_employee(db_session, empresa.id, "EMP001", Decimal("1000.00"))

        response = client.post(
            f"/employee/salary-changes/new/{empleado.id}",
            data={
                "fecha_efectiva": "2024-02-01",
                "salario_nuevo": "1200.00",
                "motivo": "Ajuste anual",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        cambio = db_session.execute(db.select(HistorialSalario).filter_by(empleado_id=empleado.id)).scalar_one()
        assert cambio.estado == "draft"

        response = client.post(f"/employee/salary-changes/{cambio.id}/approve", follow_redirects=False)
        assert response.status_code == 302
        db_session.refresh(cambio)
        assert cambio.estado == "approved"

        response = client.post(f"/employee/salary-changes/{cambio.id}/apply", follow_redirects=False)
        assert response.status_code == 302
        db_session.refresh(cambio)
        db_session.refresh(empleado)
        assert cambio.estado == "applied"
        assert empleado.salario_base == Decimal("1200.00")


def test_large_company_requires_different_approver(app, client, admin_user, db_session):
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        empresa = _create_company(db_session, "EMP-B")
        empleado = _create_employee(db_session, empresa.id, "EMP100", Decimal("1000.00"))

        for index in range(1, 50):
            _create_employee(db_session, empresa.id, f"E{index}", Decimal("900.00"))

        cambio = HistorialSalario(
            empleado_id=empleado.id,
            fecha_efectiva=date(2024, 2, 1),
            salario_anterior=Decimal("1000.00"),
            salario_nuevo=Decimal("1300.00"),
            motivo="Promoción",
            estado="draft",
            creado_por=admin_user.usuario,
        )
        db_session.add(cambio)
        db_session.commit()

        response = client.post(f"/employee/salary-changes/{cambio.id}/approve", follow_redirects=False)
        assert response.status_code == 302
        db_session.refresh(cambio)
        assert cambio.estado == "draft"


def test_employee_edit_does_not_create_salary_change_draft(app, client, admin_user, db_session):
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        empresa = _create_company(db_session, "EMP-C")
        empleado = _create_employee(db_session, empresa.id, "EMP200", Decimal("1000.00"))

        response = client.post(
            f"/employee/edit/{empleado.id}",
            data={
                "codigo_empleado": empleado.codigo_empleado,
                "primer_nombre": "Ana",
                "segundo_nombre": "",
                "primer_apellido": "Pérez",
                "segundo_apellido": "",
                "identificacion_personal": empleado.identificacion_personal,
                "fecha_alta": "2024-01-01",
                "salario_base": "1500.00",
                "activo": "y",
                "nacionalidad": "Nicaragüense",
                "correo": "",
                "telefono": "",
                "direccion": "",
                "cargo": "Analista",
                "area": "Operaciones",
                "centro_costos": "",
                "banco": "",
                "numero_cuenta_bancaria": "",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["Location"].endswith(f"/employee/salary-changes/new/{empleado.id}")

        db_session.refresh(empleado)
        assert empleado.salario_base == Decimal("1000.00")

        cambios = db_session.execute(db.select(HistorialSalario).filter_by(empleado_id=empleado.id)).scalars().all()
        assert cambios == []


def test_employee_edit_shows_single_salary_change_flow_hint(app, client, admin_user, db_session):
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")
        empresa = _create_company(db_session, "EMP-D")
        empleado = _create_employee(db_session, empresa.id, "EMP300", Decimal("1000.00"))

        response = client.get(f"/employee/edit/{empleado.id}")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Para modificar el salario use el flujo de cambios salariales." in html
        assert f"/employee/salary-changes/new/{empleado.id}" in html
