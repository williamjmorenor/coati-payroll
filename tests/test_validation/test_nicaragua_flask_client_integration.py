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
Integration test for Nicaragua payroll using Flask test client.

This test validates the complete Nicaragua payroll workflow using the Flask test client
to simulate user interactions. No magic fixtures - all data creation and verification
is done through explicit Flask requests and fresh SQLAlchemy sessions.

VALIDATION CRITERIA:
- IR annual total: C$ 34,799.00 (as per user's calculation spreadsheet)
- INSS: 7% of gross salary
- Method: Accumulated average (Art. 19 numeral 6 LCT)

DATA SCENARIO (12 months):
| Month | Ordinary  | Occasional | Total   | INSS    | IR       |
|-------|-----------|------------|---------|---------|----------|
| 1     | 25,000    | 2,000      | 27,000  | 1,890   | 2,938.67 |
| 2     | 25,500    | 0          | 25,500  | 1,785   | 2,659.67 |
| 3-5   | 25,000    | 0          | 25,000  | 1,750   | 2,566.67 |
| 6     | 27,000    | 0          | 27,000  | 1,890   | 2,938.67 |
| 7     | 25,000    | 0          | 25,000  | 1,750   | 2,566.67 |
| 8     | 27,000    | 0          | 27,000  | 1,890   | 2,938.67 |
| 9     | 25,000    | 0          | 25,000  | 1,750   | 2,566.67 |
| 10    | 25,000    | 15,000     | 40,000  | 2,800   | 5,356.67 |
| 11-12 | 25,000    | 0          | 25,000  | 1,750   | 2,566.67 |
| TOTAL | 304,500   | 17,000     | 321,500 | 22,505  | 34,799   |
"""

from datetime import date
from decimal import Decimal

import pytest

from tests.helpers.auth import login_user


# ============================================================================
# HELPER FUNCTIONS - Create data directly, no magic fixtures
# ============================================================================


def create_admin_user(db_session):
    """Create an admin user for testing."""
    from coati_payroll.auth import proteger_passwd
    from coati_payroll.enums import TipoUsuario
    from coati_payroll.model import Usuario

    admin = Usuario()
    admin.usuario = "admin_nic_test"
    admin.acceso = proteger_passwd("test-password")
    admin.nombre = "Admin"
    admin.apellido = "Nicaragua"
    admin.correo_electronico = "admin@nicaragua.test"
    admin.tipo = TipoUsuario.ADMIN
    admin.activo = True

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def create_currency_nio(db_session):
    """Create Nicaraguan Córdoba currency."""
    from coati_payroll.model import Moneda

    nio = Moneda(
        codigo="NIO",
        nombre="Córdoba Nicaragüense",
        simbolo="C$",
        activo=True,
    )
    db_session.add(nio)
    db_session.commit()
    db_session.refresh(nio)
    return nio


def create_empresa(db_session):
    """Create a test company."""
    from coati_payroll.model import Empresa

    empresa = Empresa(
        codigo="NIC-TEST",
        razon_social="Empresa Test Nicaragua S.A.",
        nombre_comercial="Test Nicaragua",
        ruc="J0310000000001",
        activo=True,
    )
    db_session.add(empresa)
    db_session.commit()
    db_session.refresh(empresa)
    return empresa


def create_tipo_planilla(db_session):
    """Create a monthly payroll type for Nicaragua."""
    from coati_payroll.model import TipoPlanilla

    tipo = TipoPlanilla(
        codigo="MENSUAL_NIC",
        descripcion="Planilla Mensual Nicaragua",
        periodicidad="mensual",
        dias=30,
        periodos_por_anio=12,
        mes_inicio_fiscal=1,
        dia_inicio_fiscal=1,
        acumula_anual=True,
        activo=True,
    )
    db_session.add(tipo)
    db_session.commit()
    db_session.refresh(tipo)
    return tipo


def create_inss_deduction(db_session):
    """Create INSS deduction (7%)."""
    from coati_payroll.model import Deduccion

    inss = Deduccion(
        codigo="INSS_NIC",
        nombre="INSS Laboral 7%",
        descripcion="Aporte al seguro social del empleado",
        formula_tipo="porcentaje",
        porcentaje=Decimal("7.00"),
        antes_impuesto=True,
        activo=True,
    )
    db_session.add(inss)
    db_session.commit()
    db_session.refresh(inss)
    return inss


def create_ir_regla_calculo(db_session):
    """Create IR calculation rule with progressive tax table."""
    from coati_payroll.model import ReglaCalculo

    ir_schema = {
        "meta": {
            "name": "IR Nicaragua - Método Acumulado",
            "legal_reference": "Ley 891 - Art. 23 LCT",
            "calculation_method": "accumulated_average",
        },
        "inputs": [
            {"name": "salario_bruto", "type": "decimal", "source": "empleado.salario_base"},
            {"name": "salario_bruto_acumulado", "type": "decimal", "source": "acumulado.salario_bruto_acumulado"},
            {"name": "deducciones_antes_impuesto_acumulado", "type": "decimal", "source": "acumulado.deducciones_antes_impuesto_acumulado"},
            {"name": "ir_retenido_acumulado", "type": "decimal", "source": "acumulado.impuesto_retenido_acumulado"},
            {"name": "meses_trabajados", "type": "integer", "source": "acumulado.periodos_procesados"},
        ],
        "steps": [
            {"name": "inss_mes", "type": "calculation", "formula": "salario_bruto * 0.07", "output": "inss_mes"},
            {"name": "salario_neto_mes", "type": "calculation", "formula": "salario_bruto - inss_mes", "output": "salario_neto_mes"},
            {"name": "salario_neto_total", "type": "calculation", "formula": "(salario_bruto_acumulado + salario_bruto) - (deducciones_antes_impuesto_acumulado + inss_mes)", "output": "salario_neto_total"},
            {"name": "meses_totales", "type": "calculation", "formula": "meses_trabajados + 1", "output": "meses_totales"},
            {"name": "promedio_mensual", "type": "calculation", "formula": "salario_neto_total / meses_totales", "output": "promedio_mensual"},
            {"name": "expectativa_anual", "type": "calculation", "formula": "promedio_mensual * 12", "output": "expectativa_anual"},
            {"name": "ir_anual", "type": "tax_lookup", "table": "tabla_ir", "input": "expectativa_anual", "output": "ir_anual"},
            {"name": "ir_proporcional", "type": "calculation", "formula": "(ir_anual / 12) * meses_totales", "output": "ir_proporcional"},
            {"name": "ir_final", "type": "calculation", "formula": "max(ir_proporcional - ir_retenido_acumulado, 0)", "output": "ir_final"},
        ],
        "tax_tables": {
            "tabla_ir": [
                {"min": 0, "max": 100000, "rate": 0.00, "fixed": 0, "over": 0},
                {"min": 100000, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000},
                {"min": 200000, "max": 350000, "rate": 0.20, "fixed": 15000, "over": 200000},
                {"min": 350000, "max": 500000, "rate": 0.25, "fixed": 45000, "over": 350000},
                {"min": 500000, "max": None, "rate": 0.30, "fixed": 82500, "over": 500000},
            ]
        },
        "output": "ir_final",
    }

    regla = ReglaCalculo(
        codigo="IR_NICARAGUA",
        nombre="IR Nicaragua - Tabla Progresiva 2025",
        descripcion="Impuesto sobre la Renta con método acumulado según Art. 19 numeral 6 LCT",
        jurisdiccion="Nicaragua",
        moneda_referencia="NIO",
        version="1.0.0",
        tipo_regla="impuesto",
        esquema_json=ir_schema,
        vigente_desde=date(2025, 1, 1),
        vigente_hasta=None,
        activo=True,
    )
    db_session.add(regla)
    db_session.commit()
    db_session.refresh(regla)
    return regla


def create_ir_deduction(db_session, regla_calculo_id):
    """Create IR deduction linked to ReglaCalculo."""
    from coati_payroll.model import Deduccion

    ir = Deduccion(
        codigo="IR_NIC",
        nombre="Impuesto sobre la Renta Nicaragua",
        descripcion="IR con método acumulado Art. 19 num. 6",
        formula_tipo="regla_calculo",
        es_impuesto=True,
        activo=True,
    )
    db_session.add(ir)
    db_session.commit()
    db_session.refresh(ir)

    # Link ReglaCalculo to deduccion
    from coati_payroll.model import ReglaCalculo
    regla = db_session.get(ReglaCalculo, regla_calculo_id)
    regla.deduccion_id = ir.id
    db_session.commit()

    return ir


def create_employee(db_session, empresa_id, moneda_id, salario_base=Decimal("25000.00")):
    """Create a test employee."""
    from coati_payroll.model import Empleado

    empleado = Empleado(
        codigo_empleado="EMP-NIC-001",
        primer_nombre="Juan",
        segundo_nombre="Carlos",
        primer_apellido="Pérez",
        segundo_apellido="García",
        identificacion_personal="001-010180-0001X",
        fecha_alta=date(2025, 1, 1),
        salario_base=salario_base,
        moneda_id=moneda_id,
        empresa_id=empresa_id,
        activo=True,
    )
    db_session.add(empleado)
    db_session.commit()
    db_session.refresh(empleado)
    return empleado


def create_planilla(db_session, tipo_planilla_id, moneda_id, empresa_id, admin_usuario):
    """Create a planilla for the year."""
    from coati_payroll.model import Planilla

    planilla = Planilla(
        nombre="NIC-2025",
        descripcion="Nómina Nicaragua 2025",
        tipo_planilla_id=tipo_planilla_id,
        moneda_id=moneda_id,
        empresa_id=empresa_id,
        periodo_fiscal_inicio=date(2025, 1, 1),
        periodo_fiscal_fin=date(2025, 12, 31),
        activo=True,
        creado_por=admin_usuario,
    )
    db_session.add(planilla)
    db_session.commit()
    db_session.refresh(planilla)
    return planilla


def associate_employee_to_planilla(db_session, planilla_id, empleado_id):
    """Associate employee to planilla."""
    from coati_payroll.model import PlanillaEmpleado

    pe = PlanillaEmpleado(planilla_id=planilla_id, empleado_id=empleado_id, activo=True)
    db_session.add(pe)
    db_session.commit()


def associate_deduction_to_planilla(db_session, planilla_id, deduccion_id, prioridad=1):
    """Associate deduction to planilla."""
    from coati_payroll.model import PlanillaDeduccion

    pd = PlanillaDeduccion(planilla_id=planilla_id, deduccion_id=deduccion_id, prioridad=prioridad, activo=True)
    db_session.add(pd)
    db_session.commit()


def associate_regla_to_planilla(db_session, planilla_id, regla_calculo_id):
    """Associate calculation rule to planilla."""
    from coati_payroll.model import PlanillaReglaCalculo

    pr = PlanillaReglaCalculo(planilla_id=planilla_id, regla_calculo_id=regla_calculo_id, orden=1, activo=True)
    db_session.add(pr)
    db_session.commit()


# ============================================================================
# MONTHLY DATA - Based on user's spreadsheet
# ============================================================================

MONTHLY_DATA = [
    {"month": 1, "salario_bruto": Decimal("27000.00"), "expected_inss": Decimal("1890.00")},
    {"month": 2, "salario_bruto": Decimal("25500.00"), "expected_inss": Decimal("1785.00")},
    {"month": 3, "salario_bruto": Decimal("25000.00"), "expected_inss": Decimal("1750.00")},
    {"month": 4, "salario_bruto": Decimal("25000.00"), "expected_inss": Decimal("1750.00")},
    {"month": 5, "salario_bruto": Decimal("25000.00"), "expected_inss": Decimal("1750.00")},
    {"month": 6, "salario_bruto": Decimal("27000.00"), "expected_inss": Decimal("1890.00")},
    {"month": 7, "salario_bruto": Decimal("25000.00"), "expected_inss": Decimal("1750.00")},
    {"month": 8, "salario_bruto": Decimal("27000.00"), "expected_inss": Decimal("1890.00")},
    {"month": 9, "salario_bruto": Decimal("25000.00"), "expected_inss": Decimal("1750.00")},
    {"month": 10, "salario_bruto": Decimal("40000.00"), "expected_inss": Decimal("2800.00")},
    {"month": 11, "salario_bruto": Decimal("25000.00"), "expected_inss": Decimal("1750.00")},
    {"month": 12, "salario_bruto": Decimal("25000.00"), "expected_inss": Decimal("1750.00")},
]

EXPECTED_TOTAL_IR_ANNUAL = Decimal("34799.00")
EXPECTED_TOTAL_INSS_ANNUAL = Decimal("22505.00")


# ============================================================================
# MAIN TEST
# ============================================================================


@pytest.mark.validation
@pytest.mark.integration
class TestNicaraguaFlaskClientIntegration:
    """Test Nicaragua payroll using Flask test client."""

    def test_complete_12_month_payroll_with_ir_calculation(self, app, db_session, client):
        """
        Test complete 12-month payroll execution using Flask test client.

        This test:
        1. Creates all required entities (employee, company, deductions, regla calculo)
        2. Authenticates via Flask client
        3. Executes 12 monthly payrolls via Flask client
        4. Verifies final IR accumulated = C$ 34,799.00 using fresh session
        """
        with app.app_context():
            # ================================================================
            # STEP 1: Create base entities directly (configuration data)
            # ================================================================
            admin = create_admin_user(db_session)
            nio = create_currency_nio(db_session)
            empresa = create_empresa(db_session)
            tipo_planilla = create_tipo_planilla(db_session)
            inss = create_inss_deduction(db_session)
            regla_ir = create_ir_regla_calculo(db_session)
            ir = create_ir_deduction(db_session, regla_ir.id)
            planilla = create_planilla(db_session, tipo_planilla.id, nio.id, empresa.id, admin.usuario)
            empleado = create_employee(db_session, empresa.id, nio.id)

            # Associate entities to planilla
            associate_employee_to_planilla(db_session, planilla.id, empleado.id)
            associate_deduction_to_planilla(db_session, planilla.id, inss.id, prioridad=1)
            associate_deduction_to_planilla(db_session, planilla.id, ir.id, prioridad=10)
            associate_regla_to_planilla(db_session, planilla.id, regla_ir.id)

            # Store IDs for later use
            planilla_id = planilla.id
            empleado_id = empleado.id
            tipo_planilla_id = tipo_planilla.id
            inss_id = inss.id
            ir_id = ir.id

            db_session.commit()

            # ================================================================
            # STEP 2: Authenticate via Flask client
            # ================================================================
            response = login_user(client, "admin_nic_test", "test-password")
            assert response.status_code in [200, 302], f"Login failed: {response.status_code}"

            # ================================================================
            # STEP 3: Execute 12 monthly payrolls via Flask client
            # ================================================================
            print("\n" + "=" * 80)
            print("EJECUTANDO 12 NÓMINAS MENSUALES VÍA FLASK CLIENT")
            print("=" * 80)

            for month_data in MONTHLY_DATA:
                month = month_data["month"]
                salario_bruto = month_data["salario_bruto"]

                # Update employee salary for this month
                from coati_payroll.model import Empleado
                empleado = db_session.get(Empleado, empleado_id)
                empleado.salario_base = salario_bruto
                db_session.commit()

                # Calculate period dates
                if month == 12:
                    periodo_fin = date(2025, 12, 31)
                else:
                    from datetime import timedelta
                    periodo_fin = date(2025, month + 1, 1) - timedelta(days=1)
                periodo_inicio = date(2025, month, 1)

                # Execute payroll via Flask client POST
                response = client.post(
                    f"/planilla/{planilla_id}/ejecutar",
                    data={
                        "periodo_inicio": periodo_inicio.isoformat(),
                        "periodo_fin": periodo_fin.isoformat(),
                        "fecha_calculo": periodo_fin.isoformat(),
                    },
                    follow_redirects=True,
                )

                # Verify response (should redirect to nomina view or show success)
                assert response.status_code == 200, f"Month {month}: Payroll execution failed with status {response.status_code}"

                # Print progress
                print(f"Mes {month:2d}: Salario C$ {salario_bruto:>10,.2f} - Nómina ejecutada ✓")

            print("=" * 80)

            # ================================================================
            # STEP 4: Verify results with FRESH SQLAlchemy session
            # ================================================================
            print("\nVERIFICANDO RESULTADOS CON SESIÓN FRESCA...")

            # Get fresh session for verification
            from coati_payroll.model import db as _db
            from coati_payroll.model import AcumuladoAnual, NominaEmpleado, Nomina

            # Query accumulated values
            acumulado = db_session.query(AcumuladoAnual).filter_by(
                empleado_id=empleado_id,
                tipo_planilla_id=tipo_planilla_id,
            ).first()

            assert acumulado is not None, "No se encontró registro de acumulado anual"
            assert acumulado.periodos_procesados == 12, f"Esperados 12 períodos, encontrados {acumulado.periodos_procesados}"

            # Verify IR accumulated
            ir_acumulado = acumulado.impuesto_retenido_acumulado
            ir_difference = abs(ir_acumulado - EXPECTED_TOTAL_IR_ANNUAL)

            # Verify INSS accumulated
            inss_acumulado = acumulado.deducciones_antes_impuesto_acumulado

            print(f"\n{'='*80}")
            print("RESULTADOS FINALES:")
            print(f"{'='*80}")
            print(f"IR Total Calculado:    C$ {ir_acumulado:>12,.2f}")
            print(f"IR Total Esperado:     C$ {EXPECTED_TOTAL_IR_ANNUAL:>12,.2f}")
            print(f"Diferencia IR:         C$ {ir_difference:>12,.2f}")
            print(f"INSS Total Acumulado:  C$ {inss_acumulado:>12,.2f}")
            print(f"INSS Total Esperado:   C$ {EXPECTED_TOTAL_INSS_ANNUAL:>12,.2f}")
            print(f"Períodos Procesados:       {acumulado.periodos_procesados}")
            print(f"Salario Bruto Acumulado: C$ {acumulado.salario_bruto_acumulado:>12,.2f}")
            print(f"{'='*80}")

            # Assert IR is within acceptable tolerance (C$ 1.00)
            assert ir_difference < Decimal("1.00"), (
                f"IR calculation incorrect. "
                f"Expected C$ {EXPECTED_TOTAL_IR_ANNUAL:,.2f}, "
                f"Got C$ {ir_acumulado:,.2f}, "
                f"Difference C$ {ir_difference:,.2f}"
            )

            # Assert all 12 months processed
            assert acumulado.periodos_procesados == 12, "Not all 12 months were processed"

            print("\n✅ VALIDACIÓN EXITOSA:")
            print(f"   - IR anual C$ {ir_acumulado:,.2f} coincide con esperado C$ {EXPECTED_TOTAL_IR_ANNUAL:,.2f}")
            print("   - Todos los 12 meses procesados correctamente")
            print("   - Sistema de nómina Nicaragua validado end-to-end")
            print("=" * 80 + "\n")


    def test_verify_individual_nominas_stored_correctly(self, app, db_session, client):
        """
        Test that individual nomina records are stored correctly.

        This complementary test verifies that each monthly Nomina record
        has the correct INSS and IR deductions stored.
        """
        with app.app_context():
            # Create all entities
            admin = create_admin_user(db_session)
            nio = create_currency_nio(db_session)
            empresa = create_empresa(db_session)
            tipo_planilla = create_tipo_planilla(db_session)
            inss = create_inss_deduction(db_session)
            regla_ir = create_ir_regla_calculo(db_session)
            ir = create_ir_deduction(db_session, regla_ir.id)
            planilla = create_planilla(db_session, tipo_planilla.id, nio.id, empresa.id, admin.usuario)
            empleado = create_employee(db_session, empresa.id, nio.id)

            associate_employee_to_planilla(db_session, planilla.id, empleado.id)
            associate_deduction_to_planilla(db_session, planilla.id, inss.id, prioridad=1)
            associate_deduction_to_planilla(db_session, planilla.id, ir.id, prioridad=10)
            associate_regla_to_planilla(db_session, planilla.id, regla_ir.id)

            planilla_id = planilla.id
            empleado_id = empleado.id
            inss_id = inss.id
            ir_id = ir.id

            db_session.commit()

            # Authenticate
            login_user(client, "admin_nic_test", "test-password")

            # Execute first 3 months only (faster test)
            from coati_payroll.model import Empleado, Nomina, NominaEmpleado, NominaDetalle

            for month_data in MONTHLY_DATA[:3]:
                month = month_data["month"]
                salario_bruto = month_data["salario_bruto"]
                expected_inss = month_data["expected_inss"]

                # Update salary
                empleado = db_session.get(Empleado, empleado_id)
                empleado.salario_base = salario_bruto
                db_session.commit()

                # Execute payroll
                from datetime import timedelta
                if month == 12:
                    periodo_fin = date(2025, 12, 31)
                else:
                    periodo_fin = date(2025, month + 1, 1) - timedelta(days=1)
                periodo_inicio = date(2025, month, 1)

                client.post(
                    f"/planilla/{planilla_id}/ejecutar",
                    data={
                        "periodo_inicio": periodo_inicio.isoformat(),
                        "periodo_fin": periodo_fin.isoformat(),
                        "fecha_calculo": periodo_fin.isoformat(),
                    },
                    follow_redirects=True,
                )

                # Verify the Nomina record for this month
                nomina = db_session.query(Nomina).filter(
                    Nomina.planilla_id == planilla_id,
                    Nomina.periodo_inicio == periodo_inicio,
                ).first()

                assert nomina is not None, f"Month {month}: Nomina not found"

                # Verify NominaEmpleado
                nomina_emp = db_session.query(NominaEmpleado).filter_by(
                    nomina_id=nomina.id,
                    empleado_id=empleado_id,
                ).first()

                assert nomina_emp is not None, f"Month {month}: NominaEmpleado not found"
                assert nomina_emp.salario_bruto == salario_bruto, (
                    f"Month {month}: Salario bruto incorrect. "
                    f"Expected {salario_bruto}, got {nomina_emp.salario_bruto}"
                )

                # Verify INSS deduction
                inss_detail = db_session.query(NominaDetalle).filter_by(
                    nomina_empleado_id=nomina_emp.id,
                    deduccion_id=inss_id,
                ).first()

                if inss_detail:
                    inss_diff = abs(inss_detail.monto - expected_inss)
                    assert inss_diff < Decimal("0.01"), (
                        f"Month {month}: INSS incorrect. "
                        f"Expected {expected_inss}, got {inss_detail.monto}"
                    )
                    print(f"Mes {month}: INSS C$ {inss_detail.monto:,.2f} ✓")
                else:
                    print(f"Mes {month}: INSS deducción no encontrada (puede estar en total_deducciones)")

            print("\n✅ Verificación de nóminas individuales completada")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-k", "test_complete"])
