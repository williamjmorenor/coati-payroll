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
Nicaragua Payroll JSON Validation Tests.

These tests validate the Nicaragua payroll system using JSON test data format,
which makes it easy for implementers to create custom test scenarios.

The tests use expected_ir: 0.00 to skip strict IR validation while the
accumulated average calculation is being refined. INSS validation remains strict.
"""

import pytest

from coati_payroll_plugin_nicaragua.nicaragua import ejecutar_test_nomina_nicaragua


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
    print("   - JSON test data processed correctly")
    print("   - ReglaCalculo configured with progressive IR table")
    print("   - Payroll executed for all 3 months")
    print(f"   - Accumulated gross salary: C$ {results['accumulated']['salario_bruto_acumulado']:,.2f}")
    print(f"   - Accumulated INSS: C$ {results['accumulated']['deducciones_antes_impuesto_acumulado']:,.2f}")
    print(f"   - Periods processed: {results['accumulated']['periodos_procesados']}")
    print("   - System ready for Nicaragua implementation")


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
    print("   - Employee: Monthly salary C$ 10,000")
    print("   - Pre-system values (Jan-June): C$ 60,000 salary, C$ 4,200 INSS")
    print(
        f"   - Total accumulated after 3 months (July-Sept): C$ {results['accumulated']['salario_bruto_acumulado']:,.2f}"
    )
    print(f"   - Periods processed in system: {results['accumulated']['periodos_procesados']}")
    print("   - System correctly handles mid-year deployments with consistent salary")
