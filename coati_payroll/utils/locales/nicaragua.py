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
"""
Nicaragua payroll testing utilities.

This module provides reusable functions for testing Nicaragua payroll calculations,
including INSS (7%) and IR (progressive income tax) with accumulated method.

The main function `ejecutar_test_nomina_nicaragua()` allows running payroll tests
based on JSON test data, making it easy to validate different scenarios.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from coati_payroll.model import (
    AcumuladoAnual,
    Deduccion,
    Empleado,
    Empresa,
    Moneda,
    Nomina,
    NominaEmpleado,
    Percepcion,
    Planilla,
    PlanillaDeduccion,
    PlanillaEmpleado,
    PlanillaPercepcion,
    TipoPlanilla,
    Usuario,
)
from coati_payroll.nomina_engine import NominaEngine


def ejecutar_test_nomina_nicaragua(
    test_data: Dict[str, Any],
    db_session: Any,
    app: Any,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Execute Nicaragua payroll test based on JSON test data.
    
    This reusable function creates all necessary entities (employee, company, deductions, etc.)
    and executes payroll for multiple months based on the provided test data. It validates
    that the calculated INSS and IR values match the expected values.
    
    Args:
        test_data: Dictionary containing test configuration and monthly data.
                   Expected structure:
                   {
                       "employee": {
                           "codigo": "EMP-001",
                           "nombre": "Juan",
                           "apellido": "Pérez",
                           "salario_base": 25000.00
                       },
                       "fiscal_year_start": "2025-01-01",
                       "months": [
                           {
                               "month": 1,
                               "salario_ordinario": 25000.00,
                               "salario_ocasional": 0.00,
                               "expected_inss": 1750.00,
                               "expected_ir": 2566.67
                           },
                           ...
                       ]
                   }
        db_session: SQLAlchemy database session
        app: Flask application context
        verbose: If True, print progress information
        
    Returns:
        Dictionary with test results including:
        - success: Boolean indicating if all validations passed
        - results: List of results for each month
        - accumulated: Final accumulated values
        - errors: List of validation errors (if any)
    """
    with app.app_context():
        results = {
            "success": True,
            "results": [],
            "accumulated": None,
            "errors": [],
        }
        
        try:
            # Extract configuration from test data
            employee_config = test_data.get("employee", {})
            fiscal_year_start = date.fromisoformat(test_data.get("fiscal_year_start", "2025-01-01"))
            months_data = test_data.get("months", [])
            
            if verbose:
                print(f"\n{'='*80}")
                print(f"NICARAGUA PAYROLL TEST: {employee_config.get('nombre', 'Test')} {employee_config.get('apellido', 'Employee')}")
                print(f"{'='*80}")
            
            # ===== SETUP PHASE =====
            
            # Create currency (Córdoba)
            nio = Moneda(
                codigo="NIO",
                nombre="Córdoba Nicaragüense",
                simbolo="C$",
                activo=True,
            )
            db_session.add(nio)
            db_session.flush()
            
            # Create company
            empresa = Empresa(
                codigo="NIC-TEST",
                razon_social="Empresa Test Nicaragua S.A.",
                nombre_comercial="Test Nicaragua",
                ruc="J-99999999-9",
                pais="Nicaragua",
                activo=True,
            )
            db_session.add(empresa)
            db_session.flush()
            
            # Create payroll type (Monthly - Nicaragua fiscal year)
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL_NIC",
                descripcion="Nómina Mensual Nicaragua",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=fiscal_year_start.month,
                dia_inicio_fiscal=fiscal_year_start.day,
                acumula_anual=True,
                moneda_id=nio.id,
                activo=True,
            )
            db_session.add(tipo_planilla)
            db_session.flush()
            
            # Create INSS deduction (7%)
            inss_deduccion = Deduccion(
                codigo="INSS_NIC",
                nombre="INSS Laboral 7%",
                descripcion="Aporte al seguro social del empleado",
                tipo_formula="porcentaje",
                formula="7",
                es_obligatoria=True,
                antes_impuesto=True,
                prioridad=1,
                activo=True,
            )
            db_session.add(inss_deduccion)
            db_session.flush()
            
            # Create IR deduction (placeholder - would use ReglaCalculo in production)
            ir_deduccion = Deduccion(
                codigo="IR_NIC",
                nombre="Impuesto sobre la Renta Nicaragua",
                descripcion="IR con método acumulado Art. 19 num. 6",
                tipo_formula="formula_personalizada",
                formula="0",
                es_obligatoria=True,
                es_impuesto=True,
                prioridad=2,
                activo=True,
            )
            db_session.add(ir_deduccion)
            db_session.flush()
            
            # Create test user
            usuario = Usuario(
                usuario="test_nic",
                nombre="Test",
                apellido="Nicaragua",
                correo="test@nicaragua.test",
                password_hash="test",
                activo=True,
            )
            db_session.add(usuario)
            db_session.flush()
            
            # Create employee
            empleado = Empleado(
                codigo=employee_config.get("codigo", "EMP-TEST"),
                primer_nombre=employee_config.get("nombre", "Test"),
                primer_apellido=employee_config.get("apellido", "Employee"),
                fecha_alta=fiscal_year_start,
                salario_mensual=Decimal(str(employee_config.get("salario_base", 25000.00))),
                tipo_salario="mensual",
                moneda_salario_id=nio.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()
            
            # Create perceptions for occasional income if needed
            percepcion_ocasional = None
            if any(m.get("salario_ocasional", 0) > 0 for m in months_data):
                percepcion_ocasional = Percepcion(
                    codigo="BONO_NIC",
                    nombre="Bono/Ingreso Ocasional",
                    descripcion="Ingresos ocasionales gravables",
                    gravable=True,
                    activo=True,
                )
                db_session.add(percepcion_ocasional)
                db_session.flush()
            
            db_session.commit()
            
            # ===== EXECUTION PHASE: Process each month =====
            
            for month_data in months_data:
                month_num = month_data.get("month", 1)
                salario_ordinario = Decimal(str(month_data.get("salario_ordinario", 0)))
                salario_ocasional = Decimal(str(month_data.get("salario_ocasional", 0)))
                expected_inss = Decimal(str(month_data.get("expected_inss", 0)))
                expected_ir = Decimal(str(month_data.get("expected_ir", 0)))
                
                if verbose:
                    print(f"\n--- Mes {month_num} ---")
                    print(f"Salario Ordinario: C$ {salario_ordinario:,.2f}")
                    if salario_ocasional > 0:
                        print(f"Salario Ocasional: C$ {salario_ocasional:,.2f}")
                
                # Update employee salary for this month
                empleado.salario_mensual = salario_ordinario
                db_session.commit()
                
                # Calculate period dates
                if month_num == 1:
                    periodo_inicio = fiscal_year_start
                else:
                    periodo_inicio = date(fiscal_year_start.year, month_num, 1)
                
                # Calculate last day of month
                if month_num == 12:
                    periodo_fin = date(fiscal_year_start.year, 12, 31)
                else:
                    next_month = date(fiscal_year_start.year, month_num + 1, 1)
                    periodo_fin = next_month - timedelta(days=1)
                
                # Create planilla for this month
                planilla = Planilla(
                    codigo=f"NIC-{fiscal_year_start.year}-{month_num:02d}",
                    descripcion=f"Nómina {_get_month_name(month_num)} {fiscal_year_start.year}",
                    tipo_planilla_id=tipo_planilla.id,
                    empresa_id=empresa.id,
                    moneda_id=nio.id,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    fecha_pago=periodo_fin,
                    estado="borrador",
                    activo=True,
                )
                db_session.add(planilla)
                db_session.flush()
                
                # Link employee to planilla
                db_session.add(PlanillaEmpleado(planilla_id=planilla.id, empleado_id=empleado.id))
                
                # Link deductions to planilla
                db_session.add(PlanillaDeduccion(planilla_id=planilla.id, deduccion_id=inss_deduccion.id))
                db_session.add(PlanillaDeduccion(planilla_id=planilla.id, deduccion_id=ir_deduccion.id))
                
                # Link occasional income if present
                if salario_ocasional > 0 and percepcion_ocasional:
                    db_session.add(PlanillaPercepcion(
                        planilla_id=planilla.id,
                        percepcion_id=percepcion_ocasional.id,
                    ))
                
                db_session.commit()
                
                # Execute payroll
                engine = NominaEngine(
                    planilla=planilla,
                    fecha_calculo=periodo_fin,
                    usuario=usuario,
                )
                
                # Add occasional income as novelty if present
                if salario_ocasional > 0:
                    # In a real scenario, this would be added through the novedades system
                    pass
                
                engine.ejecutar()
                db_session.commit()
                
                # Get accumulated values after this month
                acumulado = db_session.query(AcumuladoAnual).filter_by(
                    empleado_id=empleado.id,
                    tipo_planilla_id=tipo_planilla.id,
                ).first()
                
                # Calculate actual INSS and IR from nomina
                nomina = db_session.query(Nomina).filter_by(planilla_id=planilla.id).first()
                nomina_empleado = db_session.query(NominaEmpleado).filter_by(
                    nomina_id=nomina.id,
                    empleado_id=empleado.id,
                ).first() if nomina else None
                
                actual_inss = Decimal("0")
                actual_ir = Decimal("0")
                
                if nomina_empleado:
                    # Get INSS from deducciones
                    for deduccion_item in nomina_empleado.deducciones_items:
                        if deduccion_item.deduccion_id == inss_deduccion.id:
                            actual_inss = deduccion_item.monto
                        elif deduccion_item.deduccion_id == ir_deduccion.id:
                            actual_ir = deduccion_item.monto
                
                # Validate results
                month_result = {
                    "month": month_num,
                    "salario_ordinario": float(salario_ordinario),
                    "salario_ocasional": float(salario_ocasional),
                    "expected_inss": float(expected_inss),
                    "actual_inss": float(actual_inss),
                    "inss_match": abs(actual_inss - expected_inss) < Decimal("0.02"),
                    "expected_ir": float(expected_ir),
                    "actual_ir": float(actual_ir),
                    "ir_match": abs(actual_ir - expected_ir) < Decimal("0.02"),
                    "accumulated_gross": float(acumulado.salario_bruto_acumulado) if acumulado else 0,
                    "accumulated_inss": float(acumulado.deducciones_antes_impuesto_acumulado) if acumulado else 0,
                    "periods_processed": acumulado.periodos_procesados if acumulado else 0,
                }
                
                results["results"].append(month_result)
                
                if verbose:
                    print(f"INSS Esperado: C$ {expected_inss:,.2f} | Actual: C$ {actual_inss:,.2f} | {'✓' if month_result['inss_match'] else '✗'}")
                    print(f"IR Esperado:   C$ {expected_ir:,.2f} | Actual: C$ {actual_ir:,.2f} | {'✓' if month_result['ir_match'] else '✗'}")
                    if acumulado:
                        print(f"Acumulado Bruto: C$ {acumulado.salario_bruto_acumulado:,.2f}")
                        print(f"Períodos: {acumulado.periodos_procesados}")
                
                # Track validation errors
                if not month_result["inss_match"]:
                    error = f"Month {month_num}: INSS mismatch - Expected {expected_inss}, got {actual_inss}"
                    results["errors"].append(error)
                    results["success"] = False
                
                if not month_result["ir_match"]:
                    error = f"Month {month_num}: IR mismatch - Expected {expected_ir}, got {actual_ir}"
                    results["errors"].append(error)
                    results["success"] = False
            
            # Store final accumulated values
            if acumulado:
                results["accumulated"] = {
                    "salario_bruto_acumulado": float(acumulado.salario_bruto_acumulado),
                    "deducciones_antes_impuesto_acumulado": float(acumulado.deducciones_antes_impuesto_acumulado),
                    "impuesto_retenido_acumulado": float(acumulado.impuesto_retenido_acumulado),
                    "periodos_procesados": acumulado.periodos_procesados,
                }
            
            if verbose:
                print(f"\n{'='*80}")
                if results["success"]:
                    print("✅ TEST PASSED: All validations successful")
                else:
                    print(f"❌ TEST FAILED: {len(results['errors'])} validation error(s)")
                    for error in results["errors"]:
                        print(f"   - {error}")
                print(f"{'='*80}\n")
            
        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Exception: {str(e)}")
            if verbose:
                print(f"\n❌ ERROR: {str(e)}\n")
            raise
        
        return results


def _get_month_name(month: int) -> str:
    """Get Spanish month name."""
    months = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    return months.get(month, f"Mes {month}")
