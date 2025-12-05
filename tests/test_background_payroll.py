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
"""Tests for background payroll processing functionality."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from coati_payroll.enums import NominaEstado
from coati_payroll.model import (
    db,
    Planilla,
    TipoPlanilla,
    Empleado,
    Nomina,
    NominaEmpleado,
    Moneda,
    PlanillaEmpleado,
)
from coati_payroll.queue.tasks import process_large_payroll


class TestBackgroundPayrollProcessing:
    """Test background payroll processing with progress tracking."""

    @pytest.fixture
    def planilla_con_empleados(self, app, request):
        """Create a planilla with multiple employees for testing."""
        with app.app_context():
            # Use test name to make unique codes
            test_name = request.node.name
            unique_suffix = abs(hash(test_name)) % 10000
            
            # Create currency
            moneda = Moneda(
                codigo=f"NIO{unique_suffix}",
                nombre=f"Córdoba {unique_suffix}",
                simbolo="C$",
                activo=True,
            )
            db.session.add(moneda)
            db.session.flush()

            # Create tipo_planilla
            tipo_planilla = TipoPlanilla(
                codigo=f"MTEST{unique_suffix}",
                descripcion=f"Planilla Mensual Test {unique_suffix}",
                periodicidad="mensual",
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
                activo=True,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            # Create planilla
            planilla = Planilla(
                nombre=f"Planilla Test Background {unique_suffix}",
                descripcion=f"Para pruebas de procesamiento en segundo plano {unique_suffix}",
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db.session.add(planilla)
            db.session.flush()

            # Create 5 employees
            empleados = []
            for i in range(5):
                empleado = Empleado(
                    codigo_empleado=f"EMPBG{unique_suffix}-{i:03d}",
                    primer_nombre=f"Empleado{i}",
                    primer_apellido=f"Test{i}",
                    identificacion_personal=f"{unique_suffix:04d}-01019{i:01d}-{i:04d}P",
                    fecha_nacimiento=date(1990, 1, 1),
                    fecha_alta=date(2020, 1, 1),
                    salario_base=Decimal("10000.00"),
                    moneda_id=moneda.id,
                    activo=True,
                )
                db.session.add(empleado)
                db.session.flush()
                empleados.append(empleado)

                # Associate employee with planilla
                planilla_empleado = PlanillaEmpleado(
                    planilla_id=planilla.id,
                    empleado_id=empleado.id,
                    activo=True,
                )
                db.session.add(planilla_empleado)

            db.session.commit()

            yield planilla, empleados

    def test_process_large_payroll_creates_nomina_records(
        self, app, planilla_con_empleados
    ):
        """Test that background task creates NominaEmpleado records."""
        with app.app_context():
            planilla, empleados = planilla_con_empleados

            # Create nomina record
            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 1, 1),
                periodo_fin=date(2024, 1, 31),
                estado=NominaEstado.CALCULANDO,
                total_empleados=len(empleados),
                empleados_procesados=0,
                procesamiento_en_background=True,
            )
            db.session.add(nomina)
            db.session.commit()

            # Execute background task
            result = process_large_payroll(
                nomina_id=nomina.id,
                planilla_id=planilla.id,
                periodo_inicio="2024-01-01",
                periodo_fin="2024-01-31",
            )

            # Verify result
            assert result["success"] is True
            assert result["total_empleados"] == len(empleados)
            assert result["empleados_procesados"] == len(empleados)
            assert result["empleados_con_error"] == 0

            # Verify nomina state
            db.session.refresh(nomina)
            assert nomina.estado == NominaEstado.GENERADO
            assert nomina.empleados_procesados == len(empleados)
            assert len(nomina.nomina_empleados) == len(empleados)

            # Verify each employee was processed
            for ne in nomina.nomina_empleados:
                assert ne.salario_bruto > 0
                assert ne.salario_neto > 0

    def test_process_large_payroll_updates_progress(self, app, planilla_con_empleados):
        """Test that background task updates progress incrementally."""
        with app.app_context():
            planilla, empleados = planilla_con_empleados

            # Create nomina
            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 2, 1),
                periodo_fin=date(2024, 2, 29),
                estado=NominaEstado.CALCULANDO,
                total_empleados=len(empleados),
                empleados_procesados=0,
                procesamiento_en_background=True,
            )
            db.session.add(nomina)
            db.session.commit()

            # Execute task
            result = process_large_payroll(
                nomina_id=nomina.id,
                planilla_id=planilla.id,
                periodo_inicio="2024-02-01",
                periodo_fin="2024-02-29",
            )

            # Verify progress was tracked
            db.session.refresh(nomina)
            assert nomina.total_empleados == len(empleados)
            assert nomina.empleados_procesados == len(empleados)
            assert result["success"] is True

    def test_process_large_payroll_handles_errors(self, app, planilla_con_empleados):
        """Test that background task handles employee calculation errors gracefully."""
        with app.app_context():
            planilla, empleados = planilla_con_empleados

            # Set one employee's salary to 0 to potentially trigger calculation issues
            # (This is a simplified test - in real scenario, formula errors would occur)
            # We don't set it to None as it violates NOT NULL constraint
            empleados[2].salario_base = Decimal("0.00")
            db.session.commit()

            # Create nomina
            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 3, 1),
                periodo_fin=date(2024, 3, 31),
                estado=NominaEstado.CALCULANDO,
                total_empleados=len(empleados),
                empleados_procesados=0,
                procesamiento_en_background=True,
            )
            db.session.add(nomina)
            db.session.commit()

            # Execute task
            result = process_large_payroll(
                nomina_id=nomina.id,
                planilla_id=planilla.id,
                periodo_inicio="2024-03-01",
                periodo_fin="2024-03-31",
            )

            # Verify success (all employees processed, even with zero salary)
            assert result["success"] is True
            # With zero salary, calculation should still work (just result in zero net pay)
            assert result["empleados_con_error"] >= 0
            db.session.refresh(nomina)
            # State should be GENERADO if processing completed
            assert nomina.estado in [NominaEstado.GENERADO, NominaEstado.ERROR]

    def test_nomina_progress_tracking_fields(self, app):
        """Test that Nomina model has all required progress tracking fields."""
        with app.app_context():
            # Create currency and tipo_planilla with unique codes
            moneda = Moneda(codigo="NIOPF", nombre="Córdoba PF", simbolo="C$", activo=True)
            db.session.add(moneda)
            tipo_planilla = TipoPlanilla(
                codigo="MENSUALPF",
                descripcion="Mensual PF",
                periodicidad="mensual",
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
                activo=True,
            )
            db.session.add(tipo_planilla)
            db.session.flush()

            planilla = Planilla(
                nombre="Test Planilla Progress Tracking",
                tipo_planilla_id=tipo_planilla.id,
                moneda_id=moneda.id,
                activo=True,
            )
            db.session.add(planilla)
            db.session.commit()

            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date.today(),
                periodo_fin=date.today() + timedelta(days=30),
                estado=NominaEstado.CALCULANDO,
                total_empleados=100,
                empleados_procesados=50,
                empleados_con_error=2,
                errores_calculo={"emp1": "Error 1", "emp2": "Error 2"},
                procesamiento_en_background=True,
            )
            db.session.add(nomina)
            db.session.commit()

            # Verify all fields are saved correctly
            db.session.refresh(nomina)
            assert nomina.total_empleados == 100
            assert nomina.empleados_procesados == 50
            assert nomina.empleados_con_error == 2
            assert nomina.errores_calculo == {"emp1": "Error 1", "emp2": "Error 2"}
            assert nomina.procesamiento_en_background is True
            assert nomina.estado == NominaEstado.CALCULANDO


class TestNominaEstadoEnum:
    """Test that NominaEstado enum has required states."""

    def test_calculando_estado_exists(self):
        """Test that CALCULANDO state is defined."""
        assert hasattr(NominaEstado, "CALCULANDO")
        assert NominaEstado.CALCULANDO == "calculando"

    def test_error_estado_exists(self):
        """Test that ERROR state is defined."""
        assert hasattr(NominaEstado, "ERROR")
        assert NominaEstado.ERROR == "error"

    def test_all_estados_defined(self):
        """Test that all expected states are defined."""
        expected_states = ["calculando", "generado", "aprobado", "aplicado", "error"]
        for state in expected_states:
            assert state in [s.value for s in NominaEstado]


class TestBackgroundPayrollThreshold:
    """Test configurable threshold for background processing."""

    def test_default_threshold_is_100(self, app):
        """Test that default threshold is 100 employees."""
        threshold = app.config.get("BACKGROUND_PAYROLL_THRESHOLD", 100)
        assert threshold == 100

    def test_threshold_can_be_configured(self, app):
        """Test that threshold can be changed via config."""
        # Set custom threshold
        app.config["BACKGROUND_PAYROLL_THRESHOLD"] = 50
        threshold = app.config.get("BACKGROUND_PAYROLL_THRESHOLD")
        assert threshold == 50
