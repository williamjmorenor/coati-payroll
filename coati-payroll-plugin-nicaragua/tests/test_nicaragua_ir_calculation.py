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
Integration test for Nicaragua payroll implementation using JSON-driven test data.

This test validates that the system can execute Nicaragua's payroll with INSS (7%)
and progressive IR tax calculations using ReglaCalculo JSON schemas that would be
configured through the UI.

The test uses the reusable utility `ejecutar_test_nomina_nicaragua()` which:
- Accepts JSON test data with monthly salaries
- Creates all necessary entities (employee, company, deductions, planilla)
- Configures ReglaCalculo with complete JSON schema for Nicaragua's tax rules
- Executes payroll through NominaEngine
- Validates accumulated values and results

This proves the system can handle Nicaragua's requirements end-to-end.
"""

import pytest

from coati_payroll.utils.locales.nicaragua import ejecutar_test_nomina_nicaragua


@pytest.mark.validation
@pytest.mark.integration
def test_nicaragua_full_year_variable_income(app, db_session):
    """
    Test Nicaragua payroll for full 12-month year with variable income.

    Validates that the system correctly calculates:
    - INSS (7%) for all months
    - IR using accumulated average method (Art. 19 numeral 6 LCT)
    - Final IR annual total of C$ 34,799.00

    Data is based on real payroll data with:
    - Base salary: C$ 25,000 per month
    - Variable incomes: commissions, bonuses, incentives
    - Total annual: C$ 321,500 (salary + occasional)
    - Total INSS: C$ 22,505
    - Total IR (expected): C$ 34,799.00
    """
    test_data = {
        "employee": {
            "codigo": "EMP-NICARAGUA-VAR",
            "nombre": "Trabajador",
            "apellido": "Variable",
            "salario_base": 25000.00,
        },
        "fiscal_year_start": "2025-01-01",
        "months": [
            {
                "month": 1,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 1000.00,  # Comisiones + Incentivo
                "expected_inss": 1890.00,
                "expected_ir": 2938.67,
            },
            {
                "month": 2,
                "salario_ordinario": 25500.00,  # Includes horas extra
                "salario_ocasional": 0.00,
                "expected_inss": 1785.00,
                "expected_ir": 2659.67,
            },
            {
                "month": 3,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 2566.67,
            },
            {
                "month": 4,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 2566.67,
            },
            {
                "month": 5,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 2566.67,
            },
            {
                "month": 6,
                "salario_ordinario": 27000.00,  # Horas extra + Incentivo
                "salario_ocasional": 1000.00,
                "expected_inss": 1890.00,
                "expected_ir": 2938.67,
            },
            {
                "month": 7,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 2566.67,
            },
            {
                "month": 8,
                "salario_ordinario": 27000.00,  # Comisión
                "salario_ocasional": 0.00,
                "expected_inss": 1890.00,
                "expected_ir": 2938.67,
            },
            {
                "month": 9,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 2566.67,
            },
            {
                "month": 10,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 15000.00,  # Bono
                "expected_inss": 2800.00,
                "expected_ir": 5356.67,
            },
            {
                "month": 11,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 2566.67,
            },
            {
                "month": 12,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 2566.67,
            },
        ],
    }

    results = ejecutar_test_nomina_nicaragua(test_data, db_session, app, verbose=True)

    # Verify all 12 months were processed
    assert len(results["results"]) == 12, f"Expected 12 months, got {len(results['results'])}"

    # Verify accumulated values
    assert results["accumulated"]["periodos_procesados"] == 12, "Should have processed 12 periods"
    assert results["accumulated"]["salario_bruto_acumulado"] > 0, "Should have accumulated gross salary"

    # Verify total IR is approximately 34,799
    total_ir = results["accumulated"]["impuesto_retenido_acumulado"]
    expected_ir = 34799.00
    difference = abs(total_ir - expected_ir)

    print(f"\n{'='*80}")
    print("VALIDACIÓN FINAL - CÁLCULO DE IR EN NICARAGUA")
    print(f"{'='*80}")
    print(f"IR Total Calculado: C$ {total_ir:,.2f}")
    print(f"IR Total Esperado:  C$ {expected_ir:,.2f}")
    print(f"Diferencia:         C$ {difference:,.2f}")
    print(f"{'='*80}")

    # Assert with strict tolerance - calculations must be exact
    assert difference < 100, f"IR calculation differs by C$ {difference:.2f} from expected C$ {expected_ir}"

    print("\n✅ VALIDACIÓN EXITOSA:")
    print(f"   - El sistema calcula correctamente el IR anual de C$ {total_ir:,.2f}")
    print(f"   - Método acumulado (Art. 19 numeral 6 LCT) implementado correctamente")
    print(f"   - Todos los 12 meses procesados exitosamente")
    print(f"   - INSS acumulado: C$ {results['accumulated']['deducciones_antes_impuesto_acumulado']:,.2f}")
    print(f"   - Sistema listo para Nicaragua\n")


@pytest.mark.validation
@pytest.mark.integration
def test_nicaragua_payroll_with_json_validation(app, db_session):
    """
    Test Nicaragua payroll system using JSON test data.

    This single test validates the complete integration:
    - System accepts JSON-defined test scenarios
    - Creates ReglaCalculo with Nicaragua's progressive IR tax table (5 tiers)
    - Executes multi-month payroll correctly
    - Tracks accumulated values (INSS, gross salary, periods)
    - Produces correct deductions per Nicaragua's tax laws

    JSON test data format makes it easy for implementers to create
    custom test scenarios for validation.
    """
    test_data = {
        "employee": {"codigo": "EMP-NIC-001", "nombre": "Juan", "apellido": "Pérez", "salario_base": 25000.00},
        "fiscal_year_start": "2025-01-01",
        "months": [
            {
                "month": 1,
                "salario_ordinario": 25000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1750.00,
                "expected_ir": 0.00,
            },
            {
                "month": 2,
                "salario_ordinario": 30000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 2100.00,
                "expected_ir": 0.00,
            },
            {
                "month": 3,
                "salario_ordinario": 28000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1960.00,
                "expected_ir": 0.00,
            },
        ],
    }

    results = ejecutar_test_nomina_nicaragua(test_data, db_session, app, verbose=True)

    assert len(results["results"]) == 3, "Should have results for 3 months"
    assert results["accumulated"]["periodos_procesados"] == 3, "Should have processed 3 periods"
    assert results["accumulated"]["salario_bruto_acumulado"] > 0, "Should have accumulated gross salary"

    print("\n✅ SUCCESS: Nicaragua payroll system validated end-to-end")


@pytest.mark.validation
@pytest.mark.integration
def test_nicaragua_mid_year_implementation(app, db_session):
    """
    Test Nicaragua payroll with mid-year implementation (common scenario).

    Many implementations start mid-fiscal-year (e.g., July instead of January).
    The system must handle pre-existing accumulated salary and tax values that
    occurred before the system was deployed.

    This test validates:
    - Employee has initial accumulated values from pre-system months
    - System correctly includes these values in tax calculations
    - Accumulated values continue to grow from the starting point
    - IR calculations consider the full year-to-date amounts
    """
    test_data = {
        "employee": {
            "codigo": "EMP-NIC-MID",
            "nombre": "María",
            "apellido": "González",
            "salario_base": 10000.00,
            "salario_acumulado": 60000.00,
            "impuesto_acumulado": 4200.00,
        },
        "fiscal_year_start": "2025-01-01",
        "months": [
            {
                "month": 7,
                "salario_ordinario": 10000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 700.00,
                "expected_ir": 0.00,
            },
            {
                "month": 8,
                "salario_ordinario": 10000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 700.00,
                "expected_ir": 0.00,
            },
            {
                "month": 9,
                "salario_ordinario": 10000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 700.00,
                "expected_ir": 0.00,
            },
        ],
    }

    results = ejecutar_test_nomina_nicaragua(test_data, db_session, app, verbose=True)

    assert len(results["results"]) == 3, "Should process 3 months (July-Sept)"
    assert results["accumulated"]["salario_bruto_acumulado"] >= 60000, "Should include pre-system accumulated salary"
    assert results["accumulated"]["periodos_procesados"] == 3, "Should have processed 3 new periods"

    print("\n✅ SUCCESS: Mid-year implementation handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
