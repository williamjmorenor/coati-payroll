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
"""Tests for report engine functionality."""

from decimal import Decimal

from coati_payroll.enums import ReportType, ReportStatus, ReportExecutionStatus
from coati_payroll.model import Report, ReportRole
from coati_payroll.report_engine import (
    CustomReportBuilder,
    ReportExecutionManager,
    can_view_report,
    can_execute_report,
    can_export_report,
    ALLOWED_ENTITIES,
    ALLOWED_FIELDS,
    ALLOWED_OPERATORS,
)
from tests.factories.company_factory import create_company
from tests.factories.employee_factory import create_employee


def test_allowed_entities_defined():
    """
    Test that allowed entities are properly defined.
    
    Setup:
        - None
    
    Action:
        - Check ALLOWED_ENTITIES
    
    Verification:
        - Dictionary is not empty
        - Contains expected entities
    """
    assert len(ALLOWED_ENTITIES) > 0
    assert "Employee" in ALLOWED_ENTITIES
    assert "Nomina" in ALLOWED_ENTITIES


def test_allowed_fields_defined():
    """
    Test that allowed fields are properly defined.
    
    Setup:
        - None
    
    Action:
        - Check ALLOWED_FIELDS
    
    Verification:
        - Dictionary is not empty
        - Employee has fields defined
    """
    assert len(ALLOWED_FIELDS) > 0
    assert "Employee" in ALLOWED_FIELDS
    assert len(ALLOWED_FIELDS["Employee"]) > 0
    assert "codigo_empleado" in ALLOWED_FIELDS["Employee"]


def test_allowed_operators_defined():
    """
    Test that allowed operators are properly defined.
    
    Setup:
        - None
    
    Action:
        - Check ALLOWED_OPERATORS
    
    Verification:
        - Dictionary is not empty
        - Contains basic operators
    """
    assert len(ALLOWED_OPERATORS) > 0
    assert "=" in ALLOWED_OPERATORS
    assert "!=" in ALLOWED_OPERATORS
    assert ">" in ALLOWED_OPERATORS
    assert "like" in ALLOWED_OPERATORS


def test_custom_report_builder_valid_definition(app, db_session):
    """
    Test CustomReportBuilder with valid definition.
    
    Setup:
        - Create a custom report with valid definition
    
    Action:
        - Create builder and validate
    
    Verification:
        - Validation returns no errors
    """
    with app.app_context():
        definition = {
            "columns": [
                {"type": "field", "entity": "Employee", "field": "codigo_empleado"},
                {"type": "field", "entity": "Employee", "field": "primer_nombre"},
            ],
            "filters": [
                {"field": "activo", "operator": "=", "value": True}
            ],
            "sorting": [
                {"field": "primer_apellido", "direction": "asc"}
            ]
        }
        
        report = Report(
            name="Valid Report",
            type=ReportType.CUSTOM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
            definition=definition,
        )
        
        builder = CustomReportBuilder(report)
        errors = builder.validate_definition()
        
        assert len(errors) == 0


def test_custom_report_builder_invalid_entity(app, db_session):
    """
    Test CustomReportBuilder with invalid entity.
    
    Setup:
        - Create report with invalid base entity
    
    Action:
        - Create builder and validate
    
    Verification:
        - Validation returns error
    """
    with app.app_context():
        report = Report(
            name="Invalid Entity Report",
            type=ReportType.CUSTOM,
            status=ReportStatus.ENABLED,
            base_entity="InvalidEntity",
            definition={"columns": []},
        )
        
        try:
            builder = CustomReportBuilder(report)
            assert False, "Should raise ValueError for invalid entity"
        except ValueError as e:
            assert "Invalid base entity" in str(e)


def test_custom_report_builder_invalid_field(app, db_session):
    """
    Test CustomReportBuilder with invalid field.
    
    Setup:
        - Create report with invalid field
    
    Action:
        - Validate definition
    
    Verification:
        - Validation returns error about invalid field
    """
    with app.app_context():
        definition = {
            "columns": [
                {"type": "field", "entity": "Employee", "field": "invalid_field"},
            ],
        }
        
        report = Report(
            name="Invalid Field Report",
            type=ReportType.CUSTOM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
            definition=definition,
        )
        
        builder = CustomReportBuilder(report)
        errors = builder.validate_definition()
        
        assert len(errors) > 0
        assert any("invalid_field" in error for error in errors)


def test_custom_report_builder_invalid_operator(app, db_session):
    """
    Test CustomReportBuilder with invalid operator.
    
    Setup:
        - Create report with invalid operator
    
    Action:
        - Validate definition
    
    Verification:
        - Validation returns error about invalid operator
    """
    with app.app_context():
        definition = {
            "columns": [
                {"type": "field", "entity": "Employee", "field": "codigo_empleado"},
            ],
            "filters": [
                {"field": "activo", "operator": "invalid_op", "value": True}
            ],
        }
        
        report = Report(
            name="Invalid Operator Report",
            type=ReportType.CUSTOM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
            definition=definition,
        )
        
        builder = CustomReportBuilder(report)
        errors = builder.validate_definition()
        
        assert len(errors) > 0
        assert any("invalid_op" in error for error in errors)


def test_custom_report_execute_with_data(app, db_session):
    """
    Test executing a custom report with actual data.
    
    Setup:
        - Create company and employees
        - Create custom report
    
    Action:
        - Execute report
    
    Verification:
        - Results contain employee data
    """
    with app.app_context():
        # Create test data
        empresa = create_company(db_session, "TEST_COMP", "Test Company", "J1234")
        emp1 = create_employee(
            db_session,
            empresa_id=empresa.id,
            primer_nombre="Juan",
            primer_apellido="Perez",
            salario_base=Decimal("10000.00"),
        )
        emp2 = create_employee(
            db_session,
            empresa_id=empresa.id,
            primer_nombre="Maria",
            primer_apellido="Garcia",
            salario_base=Decimal("12000.00"),
        )
        db_session.commit()
        
        # Create report
        definition = {
            "columns": [
                {"type": "field", "entity": "Employee", "field": "primer_nombre", "label": "Nombre"},
                {"type": "field", "entity": "Employee", "field": "primer_apellido", "label": "Apellido"},
            ],
            "filters": [],
            "sorting": [
                {"field": "primer_apellido", "direction": "asc"}
            ]
        }
        
        report = Report(
            name="Employee List",
            type=ReportType.CUSTOM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
            definition=definition,
        )
        
        builder = CustomReportBuilder(report)
        results, total_count = builder.execute()
        
        assert total_count == 2
        assert len(results) == 2
        assert results[0]["Apellido"] == "Garcia"  # Sorted by apellido
        assert results[1]["Apellido"] == "Perez"


def test_can_view_report_admin():
    """
    Test admin can view any report.
    
    Setup:
        - Create report without permissions
    
    Action:
        - Check if admin can view
    
    Verification:
        - Returns True
    """
    report = Report(
        name="Test Report",
        type=ReportType.SYSTEM,
        status=ReportStatus.ENABLED,
        base_entity="Employee",
    )
    
    assert can_view_report(report, "admin") is True


def test_can_view_report_with_permission(app, db_session):
    """
    Test user with permission can view report.
    
    Setup:
        - Create report with hhrr view permission
    
    Action:
        - Check if hhrr can view
    
    Verification:
        - Returns True
    """
    with app.app_context():
        report = Report(
            name="Test Report",
            type=ReportType.SYSTEM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
        )
        db_session.add(report)
        db_session.commit()
        
        role = ReportRole(
            report_id=report.id,
            role="hhrr",
            can_view=True,
            can_execute=False,
            can_export=False,
        )
        db_session.add(role)
        db_session.commit()
        
        db_session.refresh(report)
        
        assert can_view_report(report, "hhrr") is True


def test_can_view_report_without_permission(app, db_session):
    """
    Test user without permission cannot view report.
    
    Setup:
        - Create report without audit permission
    
    Action:
        - Check if audit can view
    
    Verification:
        - Returns False
    """
    with app.app_context():
        report = Report(
            name="Test Report",
            type=ReportType.SYSTEM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
        )
        db_session.add(report)
        db_session.commit()
        
        assert can_view_report(report, "audit") is False


def test_can_execute_report_admin():
    """
    Test admin can execute any report.
    
    Setup:
        - Create report
    
    Action:
        - Check if admin can execute
    
    Verification:
        - Returns True
    """
    report = Report(
        name="Test Report",
        type=ReportType.SYSTEM,
        status=ReportStatus.ENABLED,
        base_entity="Employee",
    )
    
    assert can_execute_report(report, "admin") is True


def test_can_export_report_admin():
    """
    Test admin can export any report.
    
    Setup:
        - Create report
    
    Action:
        - Check if admin can export
    
    Verification:
        - Returns True
    """
    report = Report(
        name="Test Report",
        type=ReportType.SYSTEM,
        status=ReportStatus.ENABLED,
        base_entity="Employee",
    )
    
    assert can_export_report(report, "admin") is True


def test_report_execution_manager(app, db_session):
    """
    Test ReportExecutionManager creates execution records.
    
    Setup:
        - Create report with data
    
    Action:
        - Execute report via manager
    
    Verification:
        - Execution record is created
        - Results are returned
    """
    with app.app_context():
        # Create test data
        empresa = create_company(db_session, "TEST_COMP2", "Test Company 2", "J5678")
        emp1 = create_employee(db_session, empresa_id=empresa.id)
        db_session.commit()
        
        # Create report
        definition = {
            "columns": [
                {"type": "field", "entity": "Employee", "field": "codigo_empleado", "label": "Código"},
            ],
            "filters": [],
            "sorting": []
        }
        
        report = Report(
            name="Test Execution",
            type=ReportType.CUSTOM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
            definition=definition,
        )
        db_session.add(report)
        db_session.commit()
        
        # Execute via manager
        manager = ReportExecutionManager(report, "test_user")
        results, total_count, execution = manager.execute()
        
        assert execution.id is not None
        assert execution.status == ReportExecutionStatus.COMPLETED
        assert execution.executed_by == "test_user"
        assert execution.row_count == 1
        assert execution.execution_time_ms > 0
        assert len(results) == 1


def test_custom_report_pagination(app, db_session):
    """
    Test custom report pagination.
    
    Setup:
        - Create multiple employees
        - Create report
    
    Action:
        - Execute with pagination
    
    Verification:
        - Correct page of results returned
    """
    with app.app_context():
        empresa = create_company(db_session, "TEST_COMP3", "Test Company 3", "J9999")
        
        # Create 5 employees
        for i in range(5):
            create_employee(
                db_session,
                empresa_id=empresa.id,
                primer_nombre=f"Emp{i}",
            )
        db_session.commit()
        
        # Create report
        definition = {
            "columns": [
                {"type": "field", "entity": "Employee", "field": "primer_nombre", "label": "Nombre"},
            ],
            "filters": [],
            "sorting": []
        }
        
        report = Report(
            name="Paginated Report",
            type=ReportType.CUSTOM,
            status=ReportStatus.ENABLED,
            base_entity="Employee",
            definition=definition,
        )
        
        builder = CustomReportBuilder(report)
        
        # Get page 1 with 2 per page
        results_page1, total = builder.execute(page=1, per_page=2)
        assert len(results_page1) == 2
        assert total == 5
        
        # Get page 2
        results_page2, total = builder.execute(page=2, per_page=2)
        assert len(results_page2) == 2
        
        # Get page 3
        results_page3, total = builder.execute(page=3, per_page=2)
        assert len(results_page3) == 1  # Last page has only 1
