# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
# Copyright 2025 - 2026 BMO Soluciones, S.A.
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
"""Unit tests for NominaService class."""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from coati_payroll.enums import NominaEstado
from coati_payroll.model import (
    Empresa,
    Empleado,
    Moneda,
    Nomina,
    NominaDetalle,
    NominaEmpleado,
    NominaNovedad,
    AdelantoAbono,
    Planilla,
    PlanillaEmpleado,
    TipoPlanilla,
)
from coati_payroll.vistas.planilla.services.nomina_service import NominaService


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def moneda(app, db_session):
    """Create a Moneda for testing."""
    with app.app_context():
        moneda = Moneda(codigo="USD", nombre="Dolar", simbolo="$", activo=True)
        db_session.add(moneda)
        db_session.commit()
        db_session.refresh(moneda)
        return moneda


@pytest.fixture
def empresa(app, db_session):
    """Create an Empresa for testing."""
    with app.app_context():
        empresa = Empresa(
            codigo="TEST",
            razon_social="Test Company S.A.",
            ruc="123456789",
            activo=True,
        )
        db_session.add(empresa)
        db_session.commit()
        db_session.refresh(empresa)
        return empresa


@pytest.fixture
def tipo_planilla(app, db_session):
    """Create a TipoPlanilla for testing."""
    with app.app_context():
        tipo = TipoPlanilla(
            codigo="MENSUAL",
            descripcion="Planilla Mensual",
            periodicidad="mensual",
            dias=30,
            periodos_por_anio=12,
            mes_inicio_fiscal=1,
            dia_inicio_fiscal=1,
            activo=True,
        )
        db_session.add(tipo)
        db_session.commit()
        db_session.refresh(tipo)
        return tipo


@pytest.fixture
def planilla(app, db_session, tipo_planilla, moneda, empresa, admin_user):
    """Create a Planilla for testing."""
    with app.app_context():
        planilla = Planilla(
            nombre="Test Planilla",
            descripcion="Planilla de prueba",
            tipo_planilla_id=tipo_planilla.id,
            moneda_id=moneda.id,
            empresa_id=empresa.id,
            periodo_fiscal_inicio=date(2024, 1, 1),
            periodo_fiscal_fin=date(2024, 12, 31),
            activo=True,
            creado_por=admin_user.usuario,
        )
        db_session.add(planilla)
        db_session.commit()
        db_session.refresh(planilla)
        return planilla


@pytest.fixture
def empleado(app, db_session, moneda, empresa):
    """Create an Empleado for testing."""
    with app.app_context():
        empleado = Empleado(
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            primer_apellido="Pérez",
            identificacion_personal="001-010180-0001A",
            fecha_alta=date(2024, 1, 1),
            salario_base=Decimal("15000.00"),
            moneda_id=moneda.id,
            empresa_id=empresa.id,
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()
        db_session.refresh(empleado)
        return empleado


@pytest.fixture
def planilla_empleado(app, db_session, planilla, empleado):
    """Create a PlanillaEmpleado for testing."""
    with app.app_context():
        pe = PlanillaEmpleado(
            planilla_id=planilla.id,
            empleado_id=empleado.id,
            activo=True,
        )
        db_session.add(pe)
        db_session.commit()
        db_session.refresh(pe)
        return pe


# ============================================================================
# TESTS FOR ejecutar_nomina
# ============================================================================


class TestEjecutarNomina:
    """Tests for NominaService.ejecutar_nomina method."""

    @patch("coati_payroll.vistas.planilla.services.nomina_service.NominaEngine")
    def test_ejecutar_nomina_synchronous_small_payroll(
        self, mock_engine_class, app, db_session, planilla, planilla_empleado, admin_user
    ):
        """Test synchronous execution for small payroll (below threshold)."""
        with app.app_context():
            # Setup
            periodo_inicio = date(2024, 1, 1)
            periodo_fin = date(2024, 1, 31)
            fecha_calculo = date(2024, 1, 31)
            usuario = admin_user.usuario

            # Mock the engine
            mock_engine = MagicMock()
            mock_nomina = MagicMock(spec=Nomina)
            mock_nomina.id = 1
            mock_engine.ejecutar.return_value = mock_nomina
            mock_engine.errors = []
            mock_engine.warnings = ["test warning"]
            mock_engine_class.return_value = mock_engine

            # Execute
            nomina, errors, warnings = NominaService.ejecutar_nomina(
                planilla=planilla,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                fecha_calculo=fecha_calculo,
                usuario=usuario,
            )

            # Assert
            assert nomina == mock_nomina
            assert errors == []
            assert warnings == ["test warning"]

            # Verify engine was instantiated with correct parameters
            mock_engine_class.assert_called_once_with(
                planilla=planilla,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                fecha_calculo=fecha_calculo,
                usuario=usuario,
            )
            mock_engine.ejecutar.assert_called_once()

    @patch("coati_payroll.vistas.planilla.services.nomina_service.get_queue_driver")
    @patch("coati_payroll.vistas.planilla.services.nomina_service.NominaEngine")
    def test_ejecutar_nomina_background_large_payroll(
        self, mock_engine_class, mock_get_queue, app, db_session, planilla, moneda, empresa, admin_user
    ):
        """Test background execution for large payroll (above threshold)."""
        with app.app_context():
            # Create many employees to exceed threshold
            # Default threshold is 100, so create 101 employees
            for i in range(101):
                empleado = Empleado(
                    codigo_empleado=f"EMP{i:03d}",
                    primer_nombre=f"Empleado{i}",
                    primer_apellido="Test",
                    identificacion_personal=f"001-{i:06d}-0001A",
                    fecha_alta=date(2024, 1, 1),
                    salario_base=Decimal("10000.00"),
                    moneda_id=moneda.id,
                    empresa_id=empresa.id,
                    activo=True,
                )
                db_session.add(empleado)
                db_session.flush()

                pe = PlanillaEmpleado(
                    planilla_id=planilla.id,
                    empleado_id=empleado.id,
                    activo=True,
                )
                db_session.add(pe)

            db_session.commit()
            db_session.refresh(planilla)

            # Mock queue driver
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue

            # Setup
            periodo_inicio = date(2024, 1, 1)
            periodo_fin = date(2024, 1, 31)
            fecha_calculo = date(2024, 1, 31)
            usuario = admin_user.usuario

            # Execute
            nomina, errors, warnings = NominaService.ejecutar_nomina(
                planilla=planilla,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                fecha_calculo=fecha_calculo,
                usuario=usuario,
            )

            # Assert
            assert nomina is not None
            assert nomina.estado == NominaEstado.CALCULANDO
            assert nomina.procesamiento_en_background is True
            assert nomina.total_empleados == 101
            assert errors == []
            assert warnings == []

            # Verify queue was called
            mock_queue.enqueue.assert_called_once()
            call_args = mock_queue.enqueue.call_args
            assert call_args[0][0] == "process_large_payroll"
            assert call_args[1]["nomina_id"] == nomina.id
            assert call_args[1]["planilla_id"] == planilla.id

            # Verify engine was NOT called for background processing
            mock_engine_class.assert_not_called()

    @patch("coati_payroll.vistas.planilla.services.nomina_service.get_queue_driver")
    def test_ejecutar_nomina_background_queue_error(
        self, mock_get_queue, app, db_session, planilla, moneda, empresa, admin_user
    ):
        """Test background execution handles queue errors gracefully."""
        with app.app_context():
            # Create many employees to exceed threshold
            for i in range(101):
                empleado = Empleado(
                    codigo_empleado=f"EMP{i:03d}",
                    primer_nombre=f"Empleado{i}",
                    primer_apellido="Test",
                    identificacion_personal=f"001-{i:06d}-0001A",
                    fecha_alta=date(2024, 1, 1),
                    salario_base=Decimal("10000.00"),
                    moneda_id=moneda.id,
                    empresa_id=empresa.id,
                    activo=True,
                )
                db_session.add(empleado)
                db_session.flush()

                pe = PlanillaEmpleado(
                    planilla_id=planilla.id,
                    empleado_id=empleado.id,
                    activo=True,
                )
                db_session.add(pe)

            db_session.commit()
            db_session.refresh(planilla)

            # Mock queue driver to raise an error
            mock_queue = MagicMock()
            mock_queue.enqueue.side_effect = Exception("Queue connection failed")
            mock_get_queue.return_value = mock_queue

            # Setup
            periodo_inicio = date(2024, 1, 1)
            periodo_fin = date(2024, 1, 31)
            fecha_calculo = date(2024, 1, 31)
            usuario = admin_user.usuario

            # Execute
            nomina, errors, warnings = NominaService.ejecutar_nomina(
                planilla=planilla,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                fecha_calculo=fecha_calculo,
                usuario=usuario,
            )

            # Assert
            assert nomina is None
            assert len(errors) == 1
            assert "Error al iniciar el procesamiento en segundo plano" in errors[0]
            assert "Queue connection failed" in errors[0]
            assert warnings == []

            # Verify nomina was created but marked as ERROR
            nomina_in_db = db_session.query(Nomina).filter_by(planilla_id=planilla.id).first()
            assert nomina_in_db is not None
            assert nomina_in_db.estado == NominaEstado.ERROR
            assert "background_task_initialization_error" in nomina_in_db.errores_calculo


# ============================================================================
# TESTS FOR recalcular_nomina
# ============================================================================


class TestRecalcularNomina:
    """Tests for NominaService.recalcular_nomina method."""

    @patch("coati_payroll.audit_helpers.crear_log_auditoria_nomina")
    @patch("coati_payroll.vistas.planilla.services.nomina_service.NominaEngine")
    def test_recalcular_nomina_deletes_old_data(
        self, mock_engine_class, mock_audit, app, db_session, planilla, empleado, admin_user
    ):
        """Test that recalcular_nomina properly deletes old nomina data."""
        with app.app_context():
            # Create original nomina with related records
            original_nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 31),
                generado_por=admin_user.usuario,
                estado=NominaEstado.GENERADO,
                total_bruto=Decimal("15000.00"),
                total_deducciones=Decimal("2000.00"),
                total_neto=Decimal("13000.00"),
                total_empleados=1,
                empleados_procesados=1,
                empleados_con_error=0,
            )
            db_session.add(original_nomina)
            db_session.commit()
            db_session.refresh(original_nomina)
            original_nomina_id = original_nomina.id

            # Create NominaEmpleado
            nomina_empleado = NominaEmpleado(
                nomina_id=original_nomina.id,
                empleado_id=empleado.id,
                salario_bruto=Decimal("15000.00"),
                total_ingresos=Decimal("15000.00"),
                total_deducciones=Decimal("2000.00"),
                salario_neto=Decimal("13000.00"),
                sueldo_base_historico=Decimal("15000.00"),
            )
            db_session.add(nomina_empleado)
            db_session.commit()
            db_session.refresh(nomina_empleado)

            # Create NominaDetalle
            nomina_detalle = NominaDetalle(
                nomina_empleado_id=nomina_empleado.id,
                tipo="ingreso",
                codigo="SALARIO",
                descripcion="Salario Base",
                monto=Decimal("15000.00"),
            )
            db_session.add(nomina_detalle)
            db_session.commit()

            # Create NominaNovedad
            nomina_novedad = NominaNovedad(
                nomina_id=original_nomina.id,
                empleado_id=empleado.id,
                codigo_concepto="EXTRA",
                valor_cantidad=Decimal("100.00"),
            )
            db_session.add(nomina_novedad)
            db_session.commit()

            # Mock the engine for recalculation
            mock_engine = MagicMock()
            new_mock_nomina = MagicMock(spec=Nomina)
            new_mock_nomina.id = 999
            new_mock_nomina.estado = NominaEstado.GENERADO
            mock_engine.ejecutar.return_value = new_mock_nomina
            mock_engine.errors = []
            mock_engine.warnings = []
            mock_engine_class.return_value = mock_engine

            # Execute recalculation
            new_nomina, errors, warnings = NominaService.recalcular_nomina(
                nomina=original_nomina, planilla=planilla, usuario=admin_user.usuario
            )

            # Assert the new nomina is returned
            assert new_nomina == new_mock_nomina
            assert errors == []
            assert warnings == []

            # Verify old records were deleted
            assert db_session.query(Nomina).filter_by(id=original_nomina_id).first() is None
            assert db_session.query(NominaEmpleado).filter_by(nomina_id=original_nomina_id).first() is None
            assert db_session.query(NominaDetalle).filter_by(nomina_empleado_id=nomina_empleado.id).first() is None
            assert db_session.query(NominaNovedad).filter_by(nomina_id=original_nomina_id).first() is None

            # Verify engine was called
            mock_engine_class.assert_called_once()
            mock_engine.ejecutar.assert_called_once()

            # Verify audit log was created
            mock_audit.assert_called_once()

    @patch("coati_payroll.audit_helpers.crear_log_auditoria_nomina")
    @patch("coati_payroll.vistas.planilla.services.nomina_service.NominaEngine")
    def test_recalcular_nomina_sets_recalculo_flags(
        self, mock_engine_class, mock_audit, app, db_session, planilla, empleado, admin_user
    ):
        """Test that recalcular_nomina sets es_recalculo and nomina_original_id."""
        with app.app_context():
            # Create original nomina
            original_nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 31),
                generado_por=admin_user.usuario,
                estado=NominaEstado.GENERADO,
                total_bruto=Decimal("15000.00"),
                total_deducciones=Decimal("2000.00"),
                total_neto=Decimal("13000.00"),
                total_empleados=1,
                empleados_procesados=1,
                empleados_con_error=0,
            )
            db_session.add(original_nomina)
            db_session.commit()
            db_session.refresh(original_nomina)
            original_nomina_id = original_nomina.id

            # Mock the engine
            mock_engine = MagicMock()
            new_mock_nomina = MagicMock(spec=Nomina)
            mock_engine.ejecutar.return_value = new_mock_nomina
            mock_engine.errors = ["test error"]
            mock_engine.warnings = ["test warning"]
            mock_engine_class.return_value = mock_engine

            # Execute recalculation
            new_nomina, errors, warnings = NominaService.recalcular_nomina(
                nomina=original_nomina, planilla=planilla, usuario=admin_user.usuario
            )

            # Assert flags are set
            assert new_nomina.es_recalculo is True
            assert new_nomina.nomina_original_id == original_nomina_id
            assert errors == ["test error"]
            assert warnings == ["test warning"]

    @patch("coati_payroll.audit_helpers.crear_log_auditoria_nomina")
    @patch("coati_payroll.vistas.planilla.services.nomina_service.NominaEngine")
    def test_recalcular_nomina_with_adelanto_abono(
        self, mock_engine_class, mock_audit, app, db_session, planilla, empleado, admin_user
    ):
        """Test that recalcular_nomina deletes AdelantoAbono records."""
        with app.app_context():
            # Create original nomina
            original_nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 31),
                generado_por=admin_user.usuario,
                estado=NominaEstado.GENERADO,
                total_bruto=Decimal("15000.00"),
                total_deducciones=Decimal("2000.00"),
                total_neto=Decimal("13000.00"),
                total_empleados=1,
                empleados_procesados=1,
                empleados_con_error=0,
            )
            db_session.add(original_nomina)
            db_session.commit()
            db_session.refresh(original_nomina)
            original_nomina_id = original_nomina.id

            # Create AdelantoAbono linked to this nomina
            # Note: We need to create the related Adelanto first
            from coati_payroll.model import Adelanto

            adelanto = Adelanto(
                empleado_id=empleado.id,
                tipo="adelanto",
                monto_aprobado=Decimal("1000.00"),
                fecha_desembolso=date(2024, 1, 15),
                saldo_pendiente=Decimal("1000.00"),
            )
            db_session.add(adelanto)
            db_session.commit()
            db_session.refresh(adelanto)

            adelanto_abono = AdelantoAbono(
                adelanto_id=adelanto.id,
                nomina_id=original_nomina.id,
                monto_abonado=Decimal("500.00"),
                fecha_abono=date(2024, 1, 31),
            )
            db_session.add(adelanto_abono)
            db_session.commit()

            # Mock the engine
            mock_engine = MagicMock()
            new_mock_nomina = MagicMock(spec=Nomina)
            mock_engine.ejecutar.return_value = new_mock_nomina
            mock_engine.errors = []
            mock_engine.warnings = []
            mock_engine_class.return_value = mock_engine

            # Execute recalculation
            new_nomina, errors, warnings = NominaService.recalcular_nomina(
                nomina=original_nomina, planilla=planilla, usuario=admin_user.usuario
            )

            # Verify AdelantoAbono was deleted
            assert db_session.query(AdelantoAbono).filter_by(nomina_id=original_nomina_id).first() is None

    @patch("coati_payroll.audit_helpers.crear_log_auditoria_nomina")
    @patch("coati_payroll.vistas.planilla.services.nomina_service.NominaEngine")
    def test_recalcular_nomina_uses_original_fecha_calculo(
        self, mock_engine_class, mock_audit, app, db_session, planilla, empleado, admin_user
    ):
        """Test that recalcular_nomina uses the original fecha_calculo."""
        with app.app_context():
            # Create original nomina with fecha_calculo_original
            fecha_calculo_original = date(2024, 1, 31)
            original_nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 31),
                generado_por=admin_user.usuario,
                estado=NominaEstado.GENERADO,
                total_bruto=Decimal("15000.00"),
                total_deducciones=Decimal("2000.00"),
                total_neto=Decimal("13000.00"),
                total_empleados=1,
                empleados_procesados=1,
                empleados_con_error=0,
                fecha_calculo_original=fecha_calculo_original,
            )
            db_session.add(original_nomina)
            db_session.commit()
            db_session.refresh(original_nomina)

            # Mock the engine
            mock_engine = MagicMock()
            new_mock_nomina = MagicMock(spec=Nomina)
            mock_engine.ejecutar.return_value = new_mock_nomina
            mock_engine.errors = []
            mock_engine.warnings = []
            mock_engine_class.return_value = mock_engine

            # Execute recalculation
            NominaService.recalcular_nomina(nomina=original_nomina, planilla=planilla, usuario=admin_user.usuario)

            # Verify engine was called with original fecha_calculo
            call_args = mock_engine_class.call_args
            assert call_args[1]["fecha_calculo"] == fecha_calculo_original

    @patch("coati_payroll.audit_helpers.crear_log_auditoria_nomina")
    @patch("coati_payroll.vistas.planilla.services.nomina_service.NominaEngine")
    def test_recalcular_nomina_creates_audit_log(
        self, mock_engine_class, mock_audit, app, db_session, planilla, empleado, admin_user
    ):
        """Test that recalcular_nomina creates an audit log entry."""
        with app.app_context():
            # Create original nomina
            original_nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 31),
                generado_por=admin_user.usuario,
                estado=NominaEstado.GENERADO,
                total_bruto=Decimal("15000.00"),
                total_deducciones=Decimal("2000.00"),
                total_neto=Decimal("13000.00"),
                total_empleados=1,
                empleados_procesados=1,
                empleados_con_error=0,
            )
            db_session.add(original_nomina)
            db_session.commit()
            db_session.refresh(original_nomina)
            original_nomina_id = original_nomina.id

            # Mock the engine
            mock_engine = MagicMock()
            new_mock_nomina = MagicMock(spec=Nomina)
            new_mock_nomina.estado = NominaEstado.GENERADO
            mock_engine.ejecutar.return_value = new_mock_nomina
            mock_engine.errors = []
            mock_engine.warnings = []
            mock_engine_class.return_value = mock_engine

            # Execute recalculation
            NominaService.recalcular_nomina(nomina=original_nomina, planilla=planilla, usuario=admin_user.usuario)

            # Verify audit log was created with correct parameters
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args[1]
            assert call_args["nomina"] == new_mock_nomina
            assert call_args["accion"] == "recalculated"
            assert call_args["usuario"] == admin_user.usuario
            assert f"nómina original {original_nomina_id}" in call_args["descripcion"]
            assert call_args["cambios"]["nomina_original_id"] == original_nomina_id
            assert call_args["estado_anterior"] == "deleted"
            assert call_args["estado_nuevo"] == NominaEstado.GENERADO
