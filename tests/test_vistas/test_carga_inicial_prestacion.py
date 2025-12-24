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
"""Comprehensive tests for carga inicial prestacion (coati_payroll/vistas/carga_inicial_prestacion.py)."""

from sqlalchemy import func, select
from decimal import Decimal

from coati_payroll.model import CargaInicialPrestacion, Empleado, Empresa, Moneda, Prestacion, PrestacionAcumulada
from tests.helpers.auth import login_user


def test_carga_inicial_prestacion_index_requires_authentication(app, client, db_session):
    """Test that carga inicial index requires authentication."""
    with app.app_context():
        response = client.get("/carga-inicial-prestaciones/", follow_redirects=False)
        assert response.status_code == 302


def test_carga_inicial_prestacion_index_accessible_to_authenticated_users(app, client, admin_user, db_session):
    """Test that authenticated users can access carga inicial list."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        response = client.get("/carga-inicial-prestaciones/")
        assert response.status_code == 200


def test_carga_inicial_prestacion_nueva_requires_authentication(app, client, db_session):
    """Test that creating initial loads requires authentication."""
    with app.app_context():
        response = client.get("/carga-inicial-prestaciones/nueva", follow_redirects=False)
        assert response.status_code == 302


def test_carga_inicial_prestacion_nueva_accessible_to_authenticated_users(app, client, admin_user, db_session):
    """Test that authenticated users can access nueva carga form."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        response = client.get("/carga-inicial-prestaciones/nueva")
        assert response.status_code == 200


def test_carga_inicial_prestacion_reporte_requires_authentication(app, client, db_session):
    """Test that report access requires authentication."""
    with app.app_context():
        response = client.get("/carga-inicial-prestaciones/reporte", follow_redirects=False)
        assert response.status_code == 302


def test_carga_inicial_prestacion_reporte_accessible_to_authenticated_users(app, client, admin_user, db_session):
    """Test that authenticated users can access reports."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        response = client.get("/carga-inicial-prestaciones/reporte")
        assert response.status_code == 200


def test_carga_inicial_prestacion_workflow_complete_process(app, client, admin_user, db_session):
    """End-to-end test: Complete initial load workflow."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Step 1: View all loads
        response = client.get("/carga-inicial-prestaciones/")
        assert response.status_code == 200

        # Step 2: Access creation form
        response = client.get("/carga-inicial-prestaciones/nueva")
        assert response.status_code == 200

        # Step 3: View report
        response = client.get("/carga-inicial-prestaciones/reporte")
        assert response.status_code == 200


def _create_test_data(db_session):
    """Create test data for carga inicial prestacion tests."""
    # Create empresa
    empresa = Empresa(
        codigo="TESTCO",
        razon_social="Test Company",
        ruc="J-12345678-9",
        activo=True,
        creado_por="test",
    )
    db_session.add(empresa)
    db_session.commit()
    db_session.refresh(empresa)

    # Create moneda
    moneda = Moneda(
        codigo="USD",
        nombre="Dólar Estadounidense",
        simbolo="$",
        activo=True,
        creado_por="test",
    )
    db_session.add(moneda)
    db_session.commit()
    db_session.refresh(moneda)

    # Create prestacion
    prestacion = Prestacion(
        codigo="VAC",
        nombre="Vacaciones",
        tipo_acumulacion="mensual",
        activo=True,
        creado_por="test",
    )
    db_session.add(prestacion)
    db_session.commit()
    db_session.refresh(prestacion)

    # Create empleado
    empleado = Empleado(
        empresa_id=empresa.id,
        codigo_empleado="EMP001",
        primer_nombre="Juan",
        primer_apellido="Perez",
        identificacion_personal="001-010101-0001A",
        salario_base=Decimal("1000.00"),
        moneda_id=moneda.id,
        activo=True,
        creado_por="test",
    )
    db_session.add(empleado)
    db_session.commit()
    db_session.refresh(empleado)

    return empresa, moneda, prestacion, empleado


def test_carga_inicial_prestacion_post_creates_new_record(app, client, admin_user, db_session):
    """Test POST to /nueva creates a new carga inicial prestacion record."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # POST to create new carga inicial
        response = client.post(
            "/carga-inicial-prestaciones/nueva",
            data={
                "empleado_id": empleado.id,
                "prestacion_id": prestacion.id,
                "anio_corte": 2024,
                "mes_corte": 6,
                "moneda_id": moneda.id,
                "saldo_acumulado": "1500.50",
                "tipo_cambio": "1.0",
                "saldo_convertido": "1500.50",
                "observaciones": "Test carga inicial",
            },
            follow_redirects=False,
        )

        # Should redirect to index
        assert response.status_code == 302
        assert "/carga-inicial-prestaciones/" in response.location

        # Verify record was created in database
        carga = db_session.execute(
            select(CargaInicialPrestacion).filter_by(
                empleado_id=empleado.id,
                prestacion_id=prestacion.id,
                anio_corte=2024,
                mes_corte=6,
            )
        ).scalar_one_or_none()

        assert carga is not None
        assert carga.estado == "borrador"
        assert carga.saldo_acumulado == Decimal("1500.50")
        assert carga.saldo_convertido == Decimal("1500.50")
        assert carga.observaciones == "Test carga inicial"
        assert carga.creado_por == admin_user.usuario


def test_carga_inicial_prestacion_post_duplicate_detection(app, client, admin_user, db_session):
    """Test POST to /nueva detects duplicates and shows warning."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # Create existing carga inicial
        existing_carga = CargaInicialPrestacion(
            empleado_id=empleado.id,
            prestacion_id=prestacion.id,
            anio_corte=2024,
            mes_corte=6,
            moneda_id=moneda.id,
            saldo_acumulado=Decimal("1000.00"),
            tipo_cambio=Decimal("1.0"),
            saldo_convertido=Decimal("1000.00"),
            estado="borrador",
            creado_por="test",
        )
        db_session.add(existing_carga)
        db_session.commit()

        # Try to POST duplicate
        response = client.post(
            "/carga-inicial-prestaciones/nueva",
            data={
                "empleado_id": empleado.id,
                "prestacion_id": prestacion.id,
                "anio_corte": 2024,
                "mes_corte": 6,
                "moneda_id": moneda.id,
                "saldo_acumulado": "2000.00",
                "tipo_cambio": "1.0",
                "saldo_convertido": "2000.00",
                "observaciones": "Duplicate test",
            },
            follow_redirects=False,
        )

        # Should return 200 with form (not redirect)
        assert response.status_code == 200

        # Verify only one record exists
        count = (
            db_session.execute(
                select(func.count(CargaInicialPrestacion.id)).filter_by(
                    empleado_id=empleado.id,
                    prestacion_id=prestacion.id,
                    anio_corte=2024,
                    mes_corte=6,
                )
            ).scalar()
            or 0
        )
        assert count == 1


def test_carga_inicial_prestacion_editar_get_request(app, client, admin_user, db_session):
    """Test GET to /editar loads the edit form."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # Create carga inicial
        carga = CargaInicialPrestacion(
            empleado_id=empleado.id,
            prestacion_id=prestacion.id,
            anio_corte=2024,
            mes_corte=6,
            moneda_id=moneda.id,
            saldo_acumulado=Decimal("1000.00"),
            tipo_cambio=Decimal("1.0"),
            saldo_convertido=Decimal("1000.00"),
            estado="borrador",
            creado_por="test",
        )
        db_session.add(carga)
        db_session.commit()
        db_session.refresh(carga)

        # GET edit form
        response = client.get(f"/carga-inicial-prestaciones/{carga.id}/editar")
        assert response.status_code == 200


def test_carga_inicial_prestacion_editar_applied_status_redirects(app, client, admin_user, db_session):
    """Test that editing an applied carga inicial redirects with warning."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # Create applied carga inicial
        carga = CargaInicialPrestacion(
            empleado_id=empleado.id,
            prestacion_id=prestacion.id,
            anio_corte=2024,
            mes_corte=6,
            moneda_id=moneda.id,
            saldo_acumulado=Decimal("1000.00"),
            tipo_cambio=Decimal("1.0"),
            saldo_convertido=Decimal("1000.00"),
            estado="aplicado",
            creado_por="test",
        )
        db_session.add(carga)
        db_session.commit()
        db_session.refresh(carga)

        # Try to edit applied carga
        response = client.get(f"/carga-inicial-prestaciones/{carga.id}/editar", follow_redirects=False)

        # Should redirect to index
        assert response.status_code == 302
        assert "/carga-inicial-prestaciones/" in response.location


def test_carga_inicial_prestacion_editar_post_updates_record(app, client, admin_user, db_session):
    """Test POST to /editar updates existing carga inicial prestacion."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # Create carga inicial
        carga = CargaInicialPrestacion(
            empleado_id=empleado.id,
            prestacion_id=prestacion.id,
            anio_corte=2024,
            mes_corte=6,
            moneda_id=moneda.id,
            saldo_acumulado=Decimal("1000.00"),
            tipo_cambio=Decimal("1.0"),
            saldo_convertido=Decimal("1000.00"),
            observaciones="Original",
            estado="borrador",
            creado_por="test",
        )
        db_session.add(carga)
        db_session.commit()
        db_session.refresh(carga)

        # POST to update
        response = client.post(
            f"/carga-inicial-prestaciones/{carga.id}/editar",
            data={
                "empleado_id": empleado.id,
                "prestacion_id": prestacion.id,
                "anio_corte": 2024,
                "mes_corte": 7,  # Changed month
                "moneda_id": moneda.id,
                "saldo_acumulado": "2500.75",  # Changed amount
                "tipo_cambio": "1.0",
                "saldo_convertido": "2500.75",
                "observaciones": "Updated",  # Changed observations
            },
            follow_redirects=False,
        )

        # Should redirect to index
        assert response.status_code == 302
        assert "/carga-inicial-prestaciones/" in response.location

        # Verify record was updated
        db_session.refresh(carga)
        assert carga.mes_corte == 7
        assert carga.saldo_acumulado == Decimal("2500.75")
        assert carga.saldo_convertido == Decimal("2500.75")
        assert carga.observaciones == "Updated"
        assert carga.modificado_por == admin_user.usuario


def test_carga_inicial_prestacion_aplicar_creates_transaction(app, client, admin_user, db_session):
    """Test POST to /aplicar creates transaction in prestacion_acumulada."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # Create carga inicial
        carga = CargaInicialPrestacion(
            empleado_id=empleado.id,
            prestacion_id=prestacion.id,
            anio_corte=2024,
            mes_corte=6,
            moneda_id=moneda.id,
            saldo_acumulado=Decimal("1000.00"),
            tipo_cambio=Decimal("1.0"),
            saldo_convertido=Decimal("1000.00"),
            observaciones="Test application",
            estado="borrador",
            creado_por="test",
        )
        db_session.add(carga)
        db_session.commit()
        db_session.refresh(carga)

        # POST to apply
        response = client.post(
            f"/carga-inicial-prestaciones/{carga.id}/aplicar",
            follow_redirects=False,
        )

        # Should redirect to index
        assert response.status_code == 302
        assert "/carga-inicial-prestaciones/" in response.location

        # Verify carga status updated
        db_session.refresh(carga)
        assert carga.estado == "aplicado"
        assert carga.aplicado_por == admin_user.usuario
        assert carga.fecha_aplicacion is not None

        # Verify transaction created in prestacion_acumulada
        transaction = db_session.execute(
            select(PrestacionAcumulada).filter_by(carga_inicial_id=carga.id)
        ).scalar_one_or_none()

        assert transaction is not None
        assert transaction.empleado_id == empleado.id
        assert transaction.prestacion_id == prestacion.id
        assert transaction.tipo_transaccion == "saldo_inicial"
        assert transaction.monto_transaccion == Decimal("1000.00")
        assert transaction.saldo_nuevo == Decimal("1000.00")


def test_carga_inicial_prestacion_eliminar_deletes_draft(app, client, admin_user, db_session):
    """Test POST to /eliminar deletes draft carga inicial."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # Create carga inicial
        carga = CargaInicialPrestacion(
            empleado_id=empleado.id,
            prestacion_id=prestacion.id,
            anio_corte=2024,
            mes_corte=6,
            moneda_id=moneda.id,
            saldo_acumulado=Decimal("1000.00"),
            tipo_cambio=Decimal("1.0"),
            saldo_convertido=Decimal("1000.00"),
            estado="borrador",
            creado_por="test",
        )
        db_session.add(carga)
        db_session.commit()
        db_session.refresh(carga)
        carga_id = carga.id

        # POST to delete
        response = client.post(
            f"/carga-inicial-prestaciones/{carga_id}/eliminar",
            follow_redirects=False,
        )

        # Should redirect to index
        assert response.status_code == 302
        assert "/carga-inicial-prestaciones/" in response.location

        # Verify record was deleted
        deleted_carga = db_session.execute(select(CargaInicialPrestacion).filter_by(id=carga_id)).scalar_one_or_none()
        assert deleted_carga is None


def test_carga_inicial_prestacion_eliminar_applied_redirects(app, client, admin_user, db_session):
    """Test that deleting an applied carga inicial redirects with warning."""
    with app.app_context():
        login_user(client, admin_user.usuario, "admin-password")

        # Create test data
        empresa, moneda, prestacion, empleado = _create_test_data(db_session)

        # Create applied carga inicial
        carga = CargaInicialPrestacion(
            empleado_id=empleado.id,
            prestacion_id=prestacion.id,
            anio_corte=2024,
            mes_corte=6,
            moneda_id=moneda.id,
            saldo_acumulado=Decimal("1000.00"),
            tipo_cambio=Decimal("1.0"),
            saldo_convertido=Decimal("1000.00"),
            estado="aplicado",
            creado_por="test",
        )
        db_session.add(carga)
        db_session.commit()
        db_session.refresh(carga)
        carga_id = carga.id

        # Try to delete applied carga
        response = client.post(
            f"/carga-inicial-prestaciones/{carga_id}/eliminar",
            follow_redirects=False,
        )

        # Should redirect to index
        assert response.status_code == 302
        assert "/carga-inicial-prestaciones/" in response.location

        # Verify record still exists
        still_exists = db_session.execute(select(CargaInicialPrestacion).filter_by(id=carga_id)).scalar_one_or_none()
        assert still_exists is not None
        assert still_exists.estado == "aplicado"
