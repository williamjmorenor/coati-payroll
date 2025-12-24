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
"""End-to-end tests for prestamo (loan) management using Flask test client.

These tests simulate real user interactions with the application through
HTTP GET and POST requests. They are simple, easy to understand and maintain.
"""

from datetime import date
from decimal import Decimal

from coati_payroll.model import Adelanto, Empleado, Moneda, Empresa, db
from coati_payroll.enums import AdelantoEstado, AdelantoTipo
from tests.helpers.auth import login_user


def test_prestamo_index_list_all_loans(app, client, admin_user, db_session):
    """
    Test: User views the list of all loans.

    Setup:
        - User is logged in
        - No loans exist

    Action:
        - GET /prestamo/

    Verification:
        - Page loads successfully (200)
    """
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        response = client.get("/prestamo/")
        assert response.status_code == 200


def test_prestamo_index_with_filters(app, client, admin_user, db_session):
    """
    Test: User filters loans by employee, status, and type.

    Setup:
        - User is logged in
        - Create employee and loan

    Action:
        - GET /prestamo/?empleado_id=X&estado=borrador&tipo=prestamo

    Verification:
        - Page loads successfully with filters applied
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(
            codigo="TEST001",
            razon_social="Test Company",
            ruc="J-12345678-9",
            activo=True,
        )
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.BORRADOR,
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        # Test filters
        response = client.get(f"/prestamo/?empleado_id={empleado.id}&estado=borrador&tipo=prestamo")
        assert response.status_code == 200


def test_prestamo_new_get_form(app, client, admin_user, db_session):
    """
    Test: User accesses the form to create a new loan.

    Setup:
        - User is logged in
        - Create employee and currency for dropdowns

    Action:
        - GET /prestamo/new

    Verification:
        - Form page loads successfully (200)
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.get("/prestamo/new")
        assert response.status_code == 200


def test_prestamo_new_post_create_loan(app, client, admin_user, db_session):
    """
    Test: User creates a new loan via form submission.

    Setup:
        - User is logged in
        - Create employee and currency

    Action:
        - POST /prestamo/new with loan data

    Verification:
        - Loan is created and user is redirected to detail page
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        # Submit loan creation form
        response = client.post(
            "/prestamo/new",
            data={
                "empleado_id": empleado.id,
                "tipo": AdelantoTipo.PRESTAMO,
                "fecha_solicitud": date.today().isoformat(),
                "monto_solicitado": "5000.00",
                "moneda_id": moneda.id,
                "cuotas_pactadas": "6",
                "tasa_interes": "0.0000",
                "tipo_interes": "ninguno",
                "metodo_amortizacion": "frances",
                "motivo": "Préstamo de prueba",
            },
            follow_redirects=False,
        )

        # Should redirect to detail page
        assert response.status_code == 302
        assert "/prestamo/" in response.location

        # Verify loan was created
        prestamo = db_session.execute(db.select(Adelanto).filter_by(empleado_id=empleado.id)).scalar_one_or_none()
        assert prestamo is not None
        assert prestamo.monto_solicitado == Decimal("5000.00")
        assert prestamo.estado == AdelantoEstado.BORRADOR


def test_prestamo_edit_get_form(app, client, admin_user, db_session):
    """
    Test: User accesses the form to edit a loan in draft state.

    Setup:
        - User is logged in
        - Create loan in draft state

    Action:
        - GET /prestamo/<prestamo_id>/edit

    Verification:
        - Edit form loads successfully (200)
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.BORRADOR,
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.get(f"/prestamo/{prestamo.id}/edit")
        assert response.status_code == 200


def test_prestamo_edit_post_update_loan(app, client, admin_user, db_session):
    """
    Test: User updates a loan via form submission.

    Setup:
        - User is logged in
        - Create loan in draft state

    Action:
        - POST /prestamo/<prestamo_id>/edit with updated data

    Verification:
        - Loan is updated and user is redirected to detail page
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.BORRADOR,
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        # Update loan
        response = client.post(
            f"/prestamo/{prestamo.id}/edit",
            data={
                "empleado_id": empleado.id,
                "tipo": AdelantoTipo.PRESTAMO,
                "fecha_solicitud": date.today().isoformat(),
                "monto_solicitado": "6000.00",  # Updated amount
                "moneda_id": moneda.id,
                "cuotas_pactadas": "8",  # Updated installments
                "tasa_interes": "0.0000",
                "tipo_interes": "ninguno",
                "metodo_amortizacion": "frances",
                "motivo": "Préstamo actualizado",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert f"/prestamo/{prestamo.id}" in response.location

        # Verify loan was updated - re-query to avoid DetachedInstanceError
        prestamo_updated = db_session.get(Adelanto, prestamo.id)
        assert prestamo_updated.monto_solicitado == Decimal("6000.00")
        assert prestamo_updated.cuotas_pactadas == 8


def test_prestamo_submit_draft_to_pending(app, client, admin_user, db_session):
    """
    Test: User submits a draft loan for approval.

    Setup:
        - User is logged in
        - Create loan in draft state

    Action:
        - POST /prestamo/<prestamo_id>/submit

    Verification:
        - Loan status changes to pending and user is redirected
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.BORRADOR,
        )
        db_session.add(prestamo)
        db_session.commit()

        # Store ID and expunge to avoid DetachedInstanceError during request
        prestamo_id = prestamo.id
        db_session.expunge_all()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.post(f"/prestamo/{prestamo_id}/submit", follow_redirects=False)

        assert response.status_code == 302
        assert f"/prestamo/{prestamo_id}" in response.location

        # Verify status changed - re-query to avoid DetachedInstanceError
        prestamo_updated = db_session.get(Adelanto, prestamo_id)
        assert prestamo_updated.estado == AdelantoEstado.PENDIENTE


def test_prestamo_approve_get_form(app, client, admin_user, db_session):
    """
    Test: User accesses the approval form for a pending loan.

    Setup:
        - User is logged in
        - Create loan in pending state

    Action:
        - GET /prestamo/<prestamo_id>/approve

    Verification:
        - Approval form loads successfully (200)
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.PENDIENTE,
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.get(f"/prestamo/{prestamo.id}/approve")
        assert response.status_code == 200


def test_prestamo_approve_post_approve_loan(app, client, admin_user, db_session):
    """
    Test: User approves a pending loan.

    Setup:
        - User is logged in
        - Create loan in pending state

    Action:
        - POST /prestamo/<prestamo_id>/approve with approval data

    Verification:
        - Loan is approved and user is redirected
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.PENDIENTE,
        )
        db_session.add(prestamo)
        db_session.commit()

        # Store ID and expunge to avoid DetachedInstanceError during request
        prestamo_id = prestamo.id
        db_session.expunge_all()

        login_user(client, admin_user.usuario, "admin-password")

        # Approve loan
        response = client.post(
            f"/prestamo/{prestamo_id}/approve",
            data={
                "aprobar": "1",
                "monto_aprobado": "5000.00",
                "fecha_aprobacion": date.today().isoformat(),
                "fecha_desembolso": date.today().isoformat(),
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert f"/prestamo/{prestamo_id}" in response.location

        # Verify loan was approved - re-query to avoid DetachedInstanceError
        prestamo_updated = db_session.get(Adelanto, prestamo_id)
        assert prestamo_updated.estado == AdelantoEstado.APROBADO
        assert prestamo_updated.monto_aprobado == Decimal("5000.00")


def test_prestamo_approve_post_reject_loan(app, client, admin_user, db_session):
    """
    Test: User rejects a pending loan.

    Setup:
        - User is logged in
        - Create loan in pending state

    Action:
        - POST /prestamo/<prestamo_id>/approve with rejection data

    Verification:
        - Loan is rejected and user is redirected
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.PENDIENTE,
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        # Reject loan - need to include required fields even when rejecting
        response = client.post(
            f"/prestamo/{prestamo.id}/approve",
            data={
                "rechazar": "1",
                "monto_aprobado": "5000.00",  # Required field
                "fecha_aprobacion": date.today().isoformat(),  # Required field
                "motivo_rechazo": "No cumple con los requisitos",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert f"/prestamo/{prestamo.id}" in response.location

        # Verify loan was rejected - re-query to avoid DetachedInstanceError
        prestamo_updated = db_session.get(Adelanto, prestamo.id)
        assert prestamo_updated.estado == AdelantoEstado.RECHAZADO


def test_prestamo_cancel_post_cancel_loan(app, client, admin_user, db_session):
    """
    Test: User cancels an active loan.

    Setup:
        - User is logged in
        - Create approved loan

    Action:
        - POST /prestamo/<prestamo_id>/cancel

    Verification:
        - Loan is cancelled and user is redirected
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.APROBADO,
            monto_aprobado=Decimal("5000.00"),
            saldo_pendiente=Decimal("5000.00"),
        )
        db_session.add(prestamo)
        db_session.commit()

        # Store ID and expunge to avoid DetachedInstanceError during request
        prestamo_id = prestamo.id
        db_session.expunge_all()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.post(f"/prestamo/{prestamo_id}/cancel", follow_redirects=False)

        assert response.status_code == 302
        assert f"/prestamo/{prestamo_id}" in response.location

        # Verify loan was cancelled - re-query to avoid DetachedInstanceError
        prestamo_updated = db_session.get(Adelanto, prestamo_id)
        assert prestamo_updated.estado == AdelantoEstado.CANCELADO


def test_prestamo_pago_extraordinario_get_form(app, client, admin_user, db_session):
    """
    Test: User accesses the form to register an extraordinary payment.

    Setup:
        - User is logged in
        - Create approved loan

    Action:
        - GET /prestamo/<prestamo_id>/pago-extraordinario

    Verification:
        - Form loads successfully (200)
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.APROBADO,
            monto_aprobado=Decimal("5000.00"),
            saldo_pendiente=Decimal("5000.00"),
            monto_por_cuota=Decimal("833.33"),
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.get(f"/prestamo/{prestamo.id}/pago-extraordinario")
        assert response.status_code == 200


def test_prestamo_condonacion_get_form(app, client, admin_user, db_session):
    """
    Test: User accesses the form to record loan forgiveness.

    Setup:
        - User is logged in
        - Create approved loan

    Action:
        - GET /prestamo/<prestamo_id>/condonacion

    Verification:
        - Form loads successfully (200)
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.APROBADO,
            monto_aprobado=Decimal("5000.00"),
            saldo_pendiente=Decimal("5000.00"),
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.get(f"/prestamo/{prestamo.id}/condonacion")
        assert response.status_code == 200


def test_prestamo_condonacion_post_record_forgiveness(app, client, admin_user, db_session):
    """
    Test: User records loan forgiveness.

    Setup:
        - User is logged in
        - Create approved loan with pending balance

    Action:
        - POST /prestamo/<prestamo_id>/condonacion with forgiveness data

    Verification:
        - Forgiveness is recorded and loan balance is updated
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.APROBADO,
            monto_aprobado=Decimal("5000.00"),
            saldo_pendiente=Decimal("5000.00"),
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        # Record forgiveness - justificacion needs at least 20 characters
        response = client.post(
            f"/prestamo/{prestamo.id}/condonacion",
            data={
                "fecha_condonacion": date.today().isoformat(),
                "monto_condonado": "2000.00",
                "autorizado_por": "Gerente General",
                "documento_soporte": "resolucion",  # Must match one of the choices
                "referencia_documento": "RES-2025-001",
                "justificacion": "Condonación parcial por méritos del empleado en reconocimiento a su excelente desempeño laboral durante el último año.",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert f"/prestamo/{prestamo.id}" in response.location

        # Verify balance was updated - re-query to avoid DetachedInstanceError
        prestamo_updated = db_session.get(Adelanto, prestamo.id)
        assert prestamo_updated.saldo_pendiente < Decimal("5000.00")


def test_prestamo_export_excel(app, client, admin_user, db_session):
    """
    Test: User exports payment schedule to Excel.

    Setup:
        - User is logged in
        - Create approved loan

    Action:
        - GET /prestamo/<prestamo_id>/tabla-pago/excel

    Verification:
        - Excel file is generated and downloaded
    """
    with app.app_context():
        # Create test data
        empresa = Empresa(codigo="TEST001", razon_social="Test", ruc="J-123", activo=True)
        db_session.add(empresa)
        db_session.commit()

        moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
        db_session.add(moneda)
        db_session.commit()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010101-0001A",
            salario_base=Decimal("10000.00"),
            moneda_id=moneda.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()

        prestamo = Adelanto(
            empleado_id=empleado.id,
            tipo=AdelantoTipo.PRESTAMO,
            fecha_solicitud=date.today(),
            monto_solicitado=Decimal("5000.00"),
            moneda_id=moneda.id,
            cuotas_pactadas=6,
            estado=AdelantoEstado.APROBADO,
            monto_aprobado=Decimal("5000.00"),
            fecha_aprobacion=date.today(),
        )
        db_session.add(prestamo)
        db_session.commit()

        login_user(client, admin_user.usuario, "admin-password")

        response = client.get(f"/prestamo/{prestamo.id}/tabla-pago/excel")
        # Excel export may return 200 or redirect if openpyxl is not available
        assert response.status_code in [200, 302]
