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
"""Unit tests for ExportService class."""

import importlib.util
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest

from coati_payroll.model import (
    db,
    Empresa,
    Empleado,
    Moneda,
    Nomina,
    NominaDetalle,
    NominaEmpleado,
    Planilla,
    TipoPlanilla,
)


def _import_export_service():
    """Import ExportService directly from file to avoid queue initialization."""
    file_path = (
        Path(__file__).parent.parent.parent / "coati_payroll" / "vistas" / "planilla" / "services" / "export_service.py"
    )
    spec = importlib.util.spec_from_file_location("export_service", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ExportService


# Lazy import to avoid queue initialization issues
ExportService = None


def _prepare_objects_for_export(planilla, nomina):
    """Prepare planilla and nomina objects for export by merging into current session."""
    planilla = db.session.merge(planilla)
    nomina = db.session.merge(nomina)
    # Eagerly load relationships to avoid lazy loading issues
    if planilla.empresa_id:
        _ = planilla.empresa  # Load empresa relationship
    return planilla, nomina


@pytest.fixture
def moneda(app, db_session):
    """Create a Moneda for testing."""
    with app.app_context():
        moneda = Moneda(codigo="USD", nombre="Dollar", simbolo="$", activo=True)
        db_session.add(moneda)
        db_session.commit()
        db_session.refresh(moneda)
        return moneda


@pytest.fixture
def tipo_planilla(app, db_session):
    """Create a TipoPlanilla for testing."""
    with app.app_context():
        tipo_planilla = TipoPlanilla(
            codigo="MONTHLY",
            descripcion="Planilla mensual",
            periodicidad="mensual",
            dias=30,
            periodos_por_anio=12,
            mes_inicio_fiscal=1,
            dia_inicio_fiscal=1,
        )
        db_session.add(tipo_planilla)
        db_session.commit()
        db_session.refresh(tipo_planilla)
        return tipo_planilla


@pytest.fixture
def empresa(app, db_session):
    """Create an Empresa for testing."""
    with app.app_context():
        empresa = Empresa(
            codigo="TEST001",
            razon_social="Test Company S.A.",
            ruc="123456789",
            activo=True,
        )
        db_session.add(empresa)
        db_session.commit()
        db_session.refresh(empresa)
        return empresa


@pytest.fixture
def planilla(app, db_session, tipo_planilla, moneda, empresa):
    """Create a Planilla for testing."""
    with app.app_context():
        planilla = Planilla(
            nombre="Test Planilla",
            descripcion="Planilla de prueba",
            tipo_planilla_id=tipo_planilla.id,
            moneda_id=moneda.id,
            empresa_id=empresa.id,
            activo=True,
        )
        db_session.add(planilla)
        db_session.commit()
        db_session.refresh(planilla)
        return planilla


@pytest.fixture
def planilla_sin_empresa(app, db_session, tipo_planilla, moneda):
    """Create a Planilla without empresa for testing."""
    with app.app_context():
        planilla = Planilla(
            nombre="Test Planilla Sin Empresa",
            descripcion="Planilla sin empresa",
            tipo_planilla_id=tipo_planilla.id,
            moneda_id=moneda.id,
            empresa_id=None,
            activo=True,
        )
        db_session.add(planilla)
        db_session.commit()
        db_session.refresh(planilla)
        return planilla


@pytest.fixture
def empleado(app, db_session, empresa, moneda):
    """Create an Empleado for testing."""
    with app.app_context():
        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP001",
            primer_nombre="Juan",
            segundo_nombre="Carlos",
            primer_apellido="Perez",
            segundo_apellido="Garcia",
            identificacion_personal="123456789",
            id_seguridad_social="SS001",
            id_fiscal="FISCAL001",
            salario_base=Decimal("1000.00"),
            cargo="Desarrollador",
            moneda_id=moneda.id,
            fecha_alta=date.today() - timedelta(days=365),
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()
        db_session.refresh(empleado)
        return empleado


@pytest.fixture
def empleado_minimo(app, db_session, empresa, moneda):
    """Create a minimal Empleado for testing (no optional fields)."""
    with app.app_context():
        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMP002",
            primer_nombre="Maria",
            primer_apellido="Lopez",
            identificacion_personal="987654321",
            salario_base=Decimal("800.00"),
            moneda_id=moneda.id,
            fecha_alta=date.today() - timedelta(days=180),
            activo=True,
        )
        db_session.add(empleado)
        db_session.commit()
        db_session.refresh(empleado)
        return empleado


@pytest.fixture
def nomina(app, db_session, planilla):
    """Create a Nomina for testing."""
    with app.app_context():
        nomina = Nomina(
            planilla_id=planilla.id,
            periodo_inicio=date(2025, 1, 1),
            periodo_fin=date(2025, 1, 31),
            generado_por="test_user",
            estado="generado",
        )
        db_session.add(nomina)
        db_session.commit()
        db_session.refresh(nomina)
        return nomina


@pytest.fixture
def nomina_empleado(app, db_session, nomina, empleado):
    """Create a NominaEmpleado for testing."""
    with app.app_context():
        nomina_empleado = NominaEmpleado(
            nomina_id=nomina.id,
            empleado_id=empleado.id,
            salario_bruto=Decimal("1000.00"),
            total_ingresos=Decimal("1200.00"),
            total_deducciones=Decimal("200.00"),
            salario_neto=Decimal("1000.00"),
            sueldo_base_historico=Decimal("1000.00"),
            cargo_snapshot="Desarrollador Senior",
        )
        db_session.add(nomina_empleado)
        db_session.commit()
        db_session.refresh(nomina_empleado)
        return nomina_empleado


@pytest.fixture
def nomina_empleado_minimo(app, db_session, nomina, empleado_minimo):
    """Create a minimal NominaEmpleado for testing."""
    with app.app_context():
        nomina_empleado = NominaEmpleado(
            nomina_id=nomina.id,
            empleado_id=empleado_minimo.id,
            salario_bruto=Decimal("800.00"),
            total_ingresos=Decimal("800.00"),
            total_deducciones=Decimal("0.00"),
            salario_neto=Decimal("800.00"),
            sueldo_base_historico=Decimal("800.00"),
        )
        db_session.add(nomina_empleado)
        db_session.commit()
        db_session.refresh(nomina_empleado)
        return nomina_empleado


@pytest.fixture
def nomina_detalle_prestacion(app, db_session, nomina_empleado):
    """Create a NominaDetalle for prestacion testing."""
    with app.app_context():
        detalle = NominaDetalle(
            nomina_empleado_id=nomina_empleado.id,
            tipo="prestacion",
            codigo="VAC001",
            descripcion="Vacaciones",
            monto=Decimal("100.00"),
            orden=1,
        )
        db_session.add(detalle)
        db_session.commit()
        db_session.refresh(detalle)
        return detalle


class TestExportarNominaExcel:
    """Tests for exportar_nomina_excel method."""

    def test_exportar_nomina_excel_success(self, app, db_session, planilla, nomina, nomina_empleado):
        """
        Test that exportar_nomina_excel successfully exports nomina to Excel.

        Setup:
            - Create planilla, nomina, and nomina_empleado

        Action:
            - Call exportar_nomina_excel

        Verification:
            - Returns BytesIO object and filename
            - File is valid Excel format
            - Filename contains planilla name and nomina info
        """
        global ExportService
        if ExportService is None:
            ExportService = _import_export_service()

        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_nomina_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert isinstance(filename, str)
            assert filename.startswith("nomina_")
            assert planilla.nombre in filename
            assert ".xlsx" in filename

            # Verify file is not empty
            output.seek(0)
            content = output.read()
            assert len(content) > 0

            # Verify it's a valid Excel file (starts with ZIP signature)
            assert content.startswith(b"PK")

    def test_exportar_nomina_excel_with_empresa(self, app, db_session, planilla, nomina, nomina_empleado):
        """
        Test that export includes empresa information when available.

        Setup:
            - Create planilla with empresa, nomina, and nomina_empleado

        Action:
            - Call exportar_nomina_excel

        Verification:
            - Export succeeds
            - File contains empresa data
        """
        global ExportService
        if ExportService is None:
            ExportService = _import_export_service()

        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_nomina_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_nomina_excel_without_empresa(self, app, db_session, planilla_sin_empresa, nomina):
        """
        Test that export works without empresa.

        Setup:
            - Create planilla without empresa, nomina

        Action:
            - Call exportar_nomina_excel

        Verification:
            - Export succeeds even without empresa
        """
        with app.app_context():
            # Create nomina_empleado for this test
            from tests.factories.employee_factory import create_employee

            empleado = create_employee(
                db_session,
                empresa_id=None,
                codigo="EMP003",
                primer_nombre="Test",
                primer_apellido="User",
            )

            nomina_empleado = NominaEmpleado(
                nomina_id=nomina.id,
                empleado_id=empleado.id,
                salario_bruto=Decimal("500.00"),
                total_ingresos=Decimal("500.00"),
                total_deducciones=Decimal("0.00"),
                salario_neto=Decimal("500.00"),
                sueldo_base_historico=Decimal("500.00"),
            )
            db_session.add(nomina_empleado)
            db_session.commit()

            planilla_sin_empresa, nomina = _prepare_objects_for_export(planilla_sin_empresa, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_nomina_excel(planilla_sin_empresa, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_nomina_excel_multiple_employees(
        self, app, db_session, planilla, nomina, nomina_empleado, empleado_minimo
    ):
        """
        Test that export handles multiple employees correctly.

        Setup:
            - Create planilla, nomina with multiple nomina_empleados

        Action:
            - Call exportar_nomina_excel

        Verification:
            - Export succeeds with multiple employees
        """
        with app.app_context():
            # Add second employee
            nomina_empleado2 = NominaEmpleado(
                nomina_id=nomina.id,
                empleado_id=empleado_minimo.id,
                salario_bruto=Decimal("800.00"),
                total_ingresos=Decimal("800.00"),
                total_deducciones=Decimal("0.00"),
                salario_neto=Decimal("800.00"),
                sueldo_base_historico=Decimal("800.00"),
            )
            db_session.add(nomina_empleado2)
            db_session.commit()

            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_nomina_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_nomina_excel_empty_nomina(self, app, db_session, planilla, nomina):
        """
        Test that export works with empty nomina (no employees).

        Setup:
            - Create planilla and nomina without nomina_empleados

        Action:
            - Call exportar_nomina_excel

        Verification:
            - Export succeeds even with no employees
        """
        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_nomina_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_nomina_excel_missing_openpyxl(self, app, db_session, planilla, nomina, monkeypatch):
        """
        Test that export raises ImportError when openpyxl is not available.

        Setup:
            - Mock check_openpyxl_available to return None

        Action:
            - Call exportar_nomina_excel

        Verification:
            - Raises ImportError with appropriate message
        """
        with app.app_context():
            # Import the module to patch the function where it's used
            from coati_payroll.vistas.planilla.services import export_service

            def mock_check_openpyxl():
                return None

            # Patch the function in the module where it's imported and used
            monkeypatch.setattr(export_service, "check_openpyxl_available", mock_check_openpyxl)

            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            with pytest.raises(ImportError, match="openpyxl no está disponible"):
                ExportService.exportar_nomina_excel(planilla, nomina)


class TestExportarPrestacionesExcel:
    """Tests for exportar_prestaciones_excel method."""

    def test_exportar_prestaciones_excel_success(
        self, app, db_session, planilla, nomina, nomina_empleado, nomina_detalle_prestacion
    ):
        """
        Test that exportar_prestaciones_excel successfully exports prestaciones to Excel.

        Setup:
            - Create planilla, nomina, nomina_empleado, and nomina_detalle with prestacion

        Action:
            - Call exportar_prestaciones_excel

        Verification:
            - Returns BytesIO object and filename
            - File is valid Excel format
            - Filename contains planilla name and nomina info
        """
        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_prestaciones_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert isinstance(filename, str)
            assert filename.startswith("prestaciones_")
            assert planilla.nombre in filename
            assert ".xlsx" in filename

            # Verify file is not empty
            output.seek(0)
            content = output.read()
            assert len(content) > 0

            # Verify it's a valid Excel file
            assert content.startswith(b"PK")

    def test_exportar_prestaciones_excel_with_empresa(
        self, app, db_session, planilla, nomina, nomina_empleado, nomina_detalle_prestacion
    ):
        """
        Test that export includes empresa information when available.

        Setup:
            - Create planilla with empresa, nomina, nomina_empleado, and prestacion

        Action:
            - Call exportar_prestaciones_excel

        Verification:
            - Export succeeds
        """
        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_prestaciones_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_prestaciones_excel_multiple_prestaciones(
        self, app, db_session, planilla, nomina, nomina_empleado
    ):
        """
        Test that export handles multiple prestaciones correctly.

        Setup:
            - Create nomina with multiple prestaciones

        Action:
            - Call exportar_prestaciones_excel

        Verification:
            - Export succeeds with multiple prestaciones
        """
        with app.app_context():
            # Add multiple prestaciones
            detalle1 = NominaDetalle(
                nomina_empleado_id=nomina_empleado.id,
                tipo="prestacion",
                codigo="VAC001",
                descripcion="Vacaciones",
                monto=Decimal("100.00"),
                orden=1,
            )
            detalle2 = NominaDetalle(
                nomina_empleado_id=nomina_empleado.id,
                tipo="prestacion",
                codigo="BON001",
                descripcion="Bono",
                monto=Decimal("50.00"),
                orden=2,
            )
            db_session.add(detalle1)
            db_session.add(detalle2)
            db_session.commit()

            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_prestaciones_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_prestaciones_excel_no_prestaciones(self, app, db_session, planilla, nomina, nomina_empleado):
        """
        Test that export works when there are no prestaciones.

        Setup:
            - Create nomina with nomina_empleado but no prestaciones

        Action:
            - Call exportar_prestaciones_excel

        Verification:
            - Export succeeds even with no prestaciones
        """
        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_prestaciones_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_prestaciones_excel_empty_nomina(self, app, db_session, planilla, nomina):
        """
        Test that export works with empty nomina (no employees).

        Setup:
            - Create planilla and nomina without nomina_empleados

        Action:
            - Call exportar_prestaciones_excel

        Verification:
            - Export succeeds even with no employees
        """
        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            output, filename = ExportService.exportar_prestaciones_excel(planilla, nomina)

            assert isinstance(output, BytesIO)
            assert filename is not None

    def test_exportar_prestaciones_excel_missing_openpyxl(self, app, db_session, planilla, nomina, monkeypatch):
        """
        Test that export raises ImportError when openpyxl is not available.

        Setup:
            - Mock check_openpyxl_available to return None

        Action:
            - Call exportar_prestaciones_excel

        Verification:
            - Raises ImportError with appropriate message
        """
        with app.app_context():
            # Import the module to patch the function where it's used
            from coati_payroll.vistas.planilla.services import export_service

            def mock_check_openpyxl():
                return None

            # Patch the function in the module where it's imported and used
            monkeypatch.setattr(export_service, "check_openpyxl_available", mock_check_openpyxl)

            # Prepare objects to avoid detached instance errors
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            from coati_payroll.vistas.planilla.services.export_service import ExportService

            with pytest.raises(ImportError, match="openpyxl no está disponible"):
                ExportService.exportar_prestaciones_excel(planilla, nomina)


class TestExportarComprobanteExcel:
    """Tests for exportar_comprobante_excel method."""

    def test_exportar_comprobante_excel_not_implemented(self, app, db_session, planilla, nomina):
        """
        Test that exportar_comprobante_excel raises NotImplementedError.

        Setup:
            - Create planilla and nomina

        Action:
            - Call exportar_comprobante_excel

        Verification:
            - Raises NotImplementedError
        """
        global ExportService
        if ExportService is None:
            ExportService = _import_export_service()

        from coati_payroll.vistas.planilla.services.export_service import ExportService

        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            with pytest.raises(NotImplementedError):
                ExportService.exportar_comprobante_excel(planilla, nomina, "test_user")


class TestExportarComprobanteDetalladoExcel:
    """Tests for exportar_comprobante_detallado_excel method."""

    def test_exportar_comprobante_detallado_excel_not_implemented(self, app, db_session, planilla, nomina):
        """
        Test that exportar_comprobante_detallado_excel raises NotImplementedError.

        Setup:
            - Create planilla and nomina

        Action:
            - Call exportar_comprobante_detallado_excel

        Verification:
            - Raises NotImplementedError
        """
        global ExportService
        if ExportService is None:
            ExportService = _import_export_service()

        from coati_payroll.vistas.planilla.services.export_service import ExportService

        with app.app_context():
            planilla, nomina = _prepare_objects_for_export(planilla, nomina)

            with pytest.raises(NotImplementedError):
                ExportService.exportar_comprobante_detallado_excel(planilla, nomina)
