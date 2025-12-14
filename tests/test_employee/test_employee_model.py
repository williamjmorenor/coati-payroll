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
"""Tests for Empleado (Employee) model."""

from datetime import date
from decimal import Decimal

from coati_payroll.model import Empleado
from tests.factories.company_factory import create_company
from tests.factories.employee_factory import create_employee


def test_create_employee_with_factory(app, db_session):
    """
    Test creating an employee using factory.
    
    Setup:
        - Create company
    
    Action:
        - Create employee with factory
    
    Verification:
        - Employee exists with correct attributes
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_1", "Company", "J0001")
        
        empleado = create_employee(
            db_session,
            empresa_id=empresa.id,
            primer_nombre="Juan",
            primer_apellido="Pérez",
            salario_base=Decimal("10000.00")
        )
        
        assert empleado.id is not None
        assert empleado.primer_nombre == "Juan"
        assert empleado.primer_apellido == "Pérez"
        assert empleado.salario_base == Decimal("10000.00")
        assert empleado.empresa_id == empresa.id
        assert empleado.activo is True


def test_employee_belongs_to_empresa(app, db_session):
    """
    Test that employee can belong to a company.
    
    Setup:
        - Create company
    
    Action:
        - Create employee for that company
    
    Verification:
        - Employee's empresa relationship works
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_2", "Company", "J0002")
        
        empleado = create_employee(db_session, empresa_id=empresa.id)
        
        assert empleado.empresa_id == empresa.id
        assert empleado.empresa == empresa
        assert empleado in empresa.empleados


def test_employee_with_minimal_data(app, db_session):
    """
    Test creating employee with minimal data.
    
    Setup:
        - Create company
    
    Action:
        - Create employee with only required fields
    
    Verification:
        - Employee is created with default values
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_3", "Company", "J0003")
        
        empleado = create_employee(db_session, empresa_id=empresa.id)
        
        assert empleado.id is not None
        assert empleado.primer_nombre == "Juan"  # Default
        assert empleado.primer_apellido == "Perez"  # Default
        assert empleado.salario_base == Decimal("1000.00")  # Default


def test_employee_with_all_names(app, db_session):
    """
    Test creating employee with all name fields.
    
    Setup:
        - Create company
    
    Action:
        - Create employee with first and second names
    
    Verification:
        - All name fields are stored
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_4", "Company", "J0004")
        
        empleado = create_employee(
            db_session,
            empresa_id=empresa.id,
            primer_nombre="Juan",
            segundo_nombre="Carlos",
            primer_apellido="Pérez",
            segundo_apellido="González"
        )
        
        assert empleado.primer_nombre == "Juan"
        assert empleado.segundo_nombre == "Carlos"
        assert empleado.primer_apellido == "Pérez"
        assert empleado.segundo_apellido == "González"


def test_employee_auto_generates_codigo(app, db_session):
    """
    Test that employee code is auto-generated if not provided.
    
    Setup:
        - Create company
    
    Action:
        - Create employee without codigo
    
    Verification:
        - Codigo is auto-generated with EMP- prefix
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_5", "Company", "J0005")
        
        empleado = create_employee(db_session, empresa_id=empresa.id)
        
        assert empleado.codigo_empleado is not None
        assert empleado.codigo_empleado.startswith("EMP-")


def test_employee_custom_codigo(app, db_session):
    """
    Test creating employee with custom codigo.
    
    Setup:
        - Create company
    
    Action:
        - Create employee with custom codigo
    
    Verification:
        - Custom codigo is used
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_6", "Company", "J0006")
        
        empleado = create_employee(
            db_session,
            empresa_id=empresa.id,
            codigo="CUSTOM-001"
        )
        
        assert empleado.codigo_empleado == "CUSTOM-001"


def test_multiple_employees_same_company(app, db_session):
    """
    Test creating multiple employees for same company.
    
    Setup:
        - Create company
    
    Action:
        - Create multiple employees
    
    Verification:
        - All employees belong to same company
        - All have unique IDs
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_7", "Company", "J0007")
        
        emp1 = create_employee(db_session, empresa_id=empresa.id, primer_nombre="Juan")
        emp2 = create_employee(db_session, empresa_id=empresa.id, primer_nombre="María")
        emp3 = create_employee(db_session, empresa_id=empresa.id, primer_nombre="Pedro")
        
        assert emp1.id != emp2.id
        assert emp2.id != emp3.id
        
        assert len(empresa.empleados) == 3
        assert emp1 in empresa.empleados
        assert emp2 in empresa.empleados
        assert emp3 in empresa.empleados


def test_employee_fecha_ingreso_defaults_to_today(app, db_session):
    """
    Test that fecha_ingreso defaults to today if not provided.
    
    Setup:
        - Create company
    
    Action:
        - Create employee without fecha_ingreso
    
    Verification:
        - fecha_ingreso is set to today
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_8", "Company", "J0008")
        
        empleado = create_employee(db_session, empresa_id=empresa.id)
        
        assert empleado.fecha_ingreso == date.today()


def test_employee_can_be_inactive(app, db_session):
    """
    Test creating inactive employee.
    
    Setup:
        - Create company
    
    Action:
        - Create employee with activo=False
    
    Verification:
        - Employee is inactive
    """
    with app.app_context():
        empresa = create_company(db_session, "EMP_EMP_9", "Company", "J0009")
        
        empleado = create_employee(
            db_session,
            empresa_id=empresa.id,
            activo=False
        )
        
        assert empleado.activo is False
