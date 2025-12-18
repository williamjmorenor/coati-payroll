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

IMPORTANT: This utility creates a complete ReglaCalculo with the full JSON schema
for Nicaragua's progressive IR tax table (5 tiers: 0%, 15%, 20%, 25%, 30%).
This validates that the system can properly configure and execute tax calculations
using JSON schemas that users would enter through the UI interface.
Nothing is hardcoded - all configuration is done via ReglaCalculo model.

VALUABLE FOR IMPLEMENTERS: The function accepts an optional `regla_calculo_schema`
parameter, allowing implementers to pass their own JSON schemas for calculation rules.
This makes it a powerful tool for testing and validating custom tax configurations
before deploying them to production systems. Implementers can verify that their
JSON schemas produce the expected results across multiple payroll periods.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict

from coati_payroll.auth import proteger_passwd
from coati_payroll.enums import TipoUsuario
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
    PlanillaIngreso,
    PlanillaReglaCalculo,
    ReglaCalculo,
    TipoPlanilla,
    Usuario,
)
from coati_payroll.nomina_engine import NominaEngine


def ejecutar_test_nomina_nicaragua(
    test_data: Dict[str, Any],
    db_session: Any,
    app: Any,
    regla_calculo_schema: Dict[str, Any] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Execute Nicaragua payroll test based on JSON test data.

    This reusable function creates all necessary entities (employee, company, deductions, etc.)
    including a complete ReglaCalculo with the JSON schema for Nicaragua's progressive IR tax,
    and executes payroll for multiple months based on the provided test data. It validates
    that the calculated INSS and IR values match the expected values.

    The ReglaCalculo JSON schema created here represents exactly what a user would configure
    through the system's UI, proving the system can handle complex tax calculations without
    any hardcoded logic.

    IMPORTANT: By passing a custom regla_calculo_schema, implementers can test different
    calculation rules and verify that their JSON schemas produce expected results. This makes
    this utility a valuable tool for validating tax calculation configurations before
    deploying them to production.

    Args:
        test_data: Dictionary containing test configuration and monthly data.
                   Expected structure:
                   {
                       "employee": {
                           "codigo_empleado": "EMP-001",
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
        regla_calculo_schema: Optional custom JSON schema for ReglaCalculo.
                              If None, uses the default Nicaragua IR schema with
                              5-tier progressive tax table (0%, 15%, 20%, 25%, 30%).
                              This allows implementers to test their own calculation
                              rules and validate results.
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
                nombre = employee_config.get('nombre', 'Test')
                apellido = employee_config.get('apellido', 'Employee')
                print(f"NICARAGUA PAYROLL TEST: {nombre} {apellido}")
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
                activo=True,
            )
            db_session.add(tipo_planilla)
            db_session.flush()

            # Create INSS deduction (7%)
            inss_deduccion = Deduccion(
                codigo="INSS_NIC",
                nombre="INSS Laboral 7%",
                descripcion="Aporte al seguro social del empleado",
                formula_tipo="porcentaje",
                porcentaje=Decimal("7.00"),
                antes_impuesto=True,
                activo=True,
            )
            db_session.add(inss_deduccion)
            db_session.flush()

            # Create ReglaCalculo for IR Nicaragua (Progressive Tax Table)
            # This JSON schema represents what a user would configure through the UI
            # If a custom schema was provided, use it; otherwise use the default Nicaragua schema
            if regla_calculo_schema is None:
                if verbose:
                    print("\nUsing default Nicaragua IR schema (5-tier progressive: 0%, 15%, 20%, 25%, 30%)")
                ir_json_schema = {
                    "meta": {
                        "name": "IR Nicaragua - Método Acumulado",
                        "legal_reference": "Ley 891 - Art. 23 LCT",
                        "calculation_method": "accumulated_average"
                    },
                    "inputs": [
                        {"name": "salario_bruto", "type": "decimal",
                         "source": "empleado.salario_base"},
                        {"name": "salario_bruto_acumulado", "type": "decimal",
                         "source": "acumulado.salario_bruto_acumulado"},
                        {"name": "deducciones_antes_impuesto_acumulado",
                         "type": "decimal",
                         "source": "acumulado.deducciones_antes_impuesto_acumulado"},
                        {"name": "ir_retenido_acumulado", "type": "decimal",
                         "source": "acumulado.impuesto_retenido_acumulado"},
                        {"name": "meses_trabajados", "type": "integer",
                         "source": "acumulado.periodos_procesados"}
                    ],
                    "steps": [
                        {"name": "inss_mes", "type": "calculation",
                         "formula": "salario_bruto * 0.07", "output": "inss_mes"},
                        {"name": "salario_neto_mes", "type": "calculation",
                         "formula": "salario_bruto - inss_mes",
                         "output": "salario_neto_mes"},
                        {"name": "salario_neto_total", "type": "calculation",
                         "formula": "(salario_bruto_acumulado + salario_bruto) - "
                                    "(deducciones_antes_impuesto_acumulado + inss_mes)",
                         "output": "salario_neto_total"},
                        {"name": "meses_totales", "type": "calculation",
                         "formula": "meses_trabajados + 1",
                         "output": "meses_totales"},
                        {"name": "promedio_mensual", "type": "calculation",
                         "formula": "salario_neto_total / meses_totales",
                         "output": "promedio_mensual"},
                        {"name": "expectativa_anual", "type": "calculation",
                         "formula": "promedio_mensual * 12",
                         "output": "expectativa_anual"},
                        {"name": "ir_anual", "type": "tax_lookup",
                         "table": "tabla_ir", "input": "expectativa_anual",
                         "output": "ir_anual"},
                        {"name": "ir_proporcional", "type": "calculation",
                         "formula": "(ir_anual / 12) * meses_totales",
                         "output": "ir_proporcional"},
                        {"name": "ir_final", "type": "calculation",
                         "formula": "max(ir_proporcional - ir_retenido_acumulado, 0)",
                         "output": "ir_final"}
                    ],
                    "tax_tables": {
                        "tabla_ir": [
                            {"min": 0, "max": 100000, "rate": 0.00,
                             "fixed": 0, "over": 0},
                            {"min": 100000, "max": 200000, "rate": 0.15,
                             "fixed": 0, "over": 100000},
                            {"min": 200000, "max": 350000, "rate": 0.20,
                             "fixed": 15000, "over": 200000},
                            {"min": 350000, "max": 500000, "rate": 0.25,
                             "fixed": 45000, "over": 350000},
                            {"min": 500000, "max": None, "rate": 0.30,
                             "fixed": 82500, "over": 500000}
                        ]
                    },
                    "output": "ir_final"
                }
            else:
                if verbose:
                    schema_name = regla_calculo_schema.get("meta", {}).get("name", "Custom")
                    print(f"\nUsing custom ReglaCalculo schema: {schema_name}")
                ir_json_schema = regla_calculo_schema

            regla_ir = ReglaCalculo(
                codigo="IR_NICARAGUA",
                nombre="IR Nicaragua - Tabla Progresiva 2025",
                descripcion=(
                    "Impuesto sobre la Renta con método acumulado "
                    "según Art. 19 numeral 6 de la Ley de Concertación Tributaria"
                ),
                jurisdiccion="Nicaragua",
                moneda_referencia="NIO",
                version="1.0.0",
                tipo_regla="impuesto",
                esquema_json=ir_json_schema,
                vigente_desde=fiscal_year_start,
                vigente_hasta=None,
                activo=True,
            )
            db_session.add(regla_ir)
            db_session.flush()

            # Create IR deduction linked to ReglaCalculo
            ir_deduccion = Deduccion(
                codigo="IR_NIC",
                nombre="Impuesto sobre la Renta Nicaragua",
                descripcion="IR con método acumulado Art. 19 num. 6",
                formula_tipo="regla_calculo",
                es_impuesto=True,
                activo=True,
            )
            db_session.add(ir_deduccion)
            db_session.flush()

            # Link ReglaCalculo to Deduccion
            regla_ir.deduccion_id = ir_deduccion.id
            db_session.flush()

            # Create test user
            usuario = Usuario()
            usuario.usuario = "test_nic"
            usuario.nombre = "Test"
            usuario.apellido = "Nicaragua"
            usuario.correo_electronico = "test@nicaragua.test"
            usuario.acceso = proteger_passwd("test-password")
            usuario.tipo = TipoUsuario.ADMIN
            usuario.activo = True
            db_session.add(usuario)
            db_session.flush()

            # Create employee
            empleado = Empleado(
                codigo_empleado=employee_config.get("codigo", "EMP-TEST"),
                primer_nombre=employee_config.get("nombre", "Test"),
                primer_apellido=employee_config.get("apellido", "Employee"),
                identificacion_personal=employee_config.get("identificacion", "ID-TEST-001"),
                fecha_alta=fiscal_year_start,
                salario_base=Decimal(str(employee_config.get("salario_base", 25000.00))),
                moneda_id=nio.id,
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
                empleado.salario_base = salario_ordinario
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
                    nombre=f"NIC-{fiscal_year_start.year}-{month_num:02d}",
                    descripcion=f"Nómina {_get_month_name(month_num)} {fiscal_year_start.year}",
                    tipo_planilla_id=tipo_planilla.id,
                    empresa_id=empresa.id,
                    moneda_id=nio.id,
                    periodo_fiscal_inicio=fiscal_year_start,
                    periodo_fiscal_fin=date(fiscal_year_start.year, 12, 31),
                    activo=True,
                )
                db_session.add(planilla)
                db_session.flush()

                # Link employee to planilla
                db_session.add(PlanillaEmpleado(planilla_id=planilla.id, empleado_id=empleado.id))

                # Link deductions to planilla
                db_session.add(PlanillaDeduccion(
                    planilla_id=planilla.id,
                    deduccion_id=inss_deduccion.id
                ))
                db_session.add(PlanillaDeduccion(
                    planilla_id=planilla.id,
                    deduccion_id=ir_deduccion.id
                ))

                # Link ReglaCalculo to planilla
                db_session.add(PlanillaReglaCalculo(
                    planilla_id=planilla.id,
                    regla_calculo_id=regla_ir.id
                ))

                # Link occasional income if present
                if salario_ocasional > 0 and percepcion_ocasional:
                    db_session.add(PlanillaIngreso(
                        planilla_id=planilla.id,
                        percepcion_id=percepcion_ocasional.id,
                    ))

                db_session.commit()

                # Execute payroll using the convenience function that handles eager loading
                from coati_payroll.nomina_engine import ejecutar_nomina
                planilla_id = planilla.id
                nomina, errors, warnings = ejecutar_nomina(
                    planilla_id=planilla_id,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    fecha_calculo=periodo_fin,
                    usuario=usuario.usuario,
                )

                if errors:
                    error_msg = f"Errors executing payroll for month {month_num}: {', '.join(errors)}"
                    if verbose:
                        print(f"❌ {error_msg}")
                    results["errors"].append(error_msg)
                    results["success"] = False
                    continue

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
                    # Get INSS and IR from nomina details
                    for detalle in nomina_empleado.nomina_detalles:
                        if detalle.deduccion_id == inss_deduccion.id:
                            actual_inss = detalle.monto
                        elif detalle.deduccion_id == ir_deduccion.id:
                            actual_ir = detalle.monto

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
                    inss_symbol = '✓' if month_result['inss_match'] else '✗'
                    ir_symbol = '✓' if month_result['ir_match'] else '✗'
                    print(
                        f"INSS Esperado: C$ {expected_inss:,.2f} | "
                        f"Actual: C$ {actual_inss:,.2f} | {inss_symbol}"
                    )
                    print(
                        f"IR Esperado:   C$ {expected_ir:,.2f} | "
                        f"Actual: C$ {actual_ir:,.2f} | {ir_symbol}"
                    )
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
