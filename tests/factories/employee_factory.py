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
"""Factory functions for creating employees."""

from datetime import date
from decimal import Decimal

from coati_payroll.model import Empleado


def create_employee(db_session, empresa_id, codigo=None, primer_nombre="Juan",
                    segundo_nombre=None, primer_apellido="Perez", segundo_apellido=None,
                    identificacion_personal=None, salario_base=Decimal("1000.00"), 
                    fecha_ingreso=None, activo=True):
    """
    Create an employee in the database.
    
    This is a simple factory function that creates an employee with the given
    parameters. No implicit data creation or side effects.
    
    Args:
        db_session: SQLAlchemy session
        empresa_id: ID of the company (required)
        codigo: Employee code (auto-generated if None)
        primer_nombre: First name (default: "Juan")
        segundo_nombre: Second name (optional)
        primer_apellido: First surname (default: "Perez")
        segundo_apellido: Second surname (optional)
        identificacion_personal: Personal ID (auto-generated if None)
        salario_base: Base salary (default: 1000.00)
        fecha_ingreso: Hire date (default: today)
        activo: Active status (default: True)
    
    Returns:
        Empleado: Created employee instance with ID assigned
    """
    from coati_payroll.model import generador_de_codigos_unicos
    
    empleado = Empleado()
    empleado.empresa_id = empresa_id
    if codigo:
        empleado.codigo_empleado = codigo
    empleado.primer_nombre = primer_nombre
    empleado.segundo_nombre = segundo_nombre
    empleado.primer_apellido = primer_apellido
    empleado.segundo_apellido = segundo_apellido
    # Generate unique identificacion_personal if not provided
    empleado.identificacion_personal = identificacion_personal or f"ID-{generador_de_codigos_unicos()[:12]}"
    empleado.salario_base = salario_base
    empleado.fecha_ingreso = fecha_ingreso or date.today()
    empleado.activo = activo
    
    db_session.add(empleado)
    db_session.commit()
    db_session.refresh(empleado)
    
    return empleado
