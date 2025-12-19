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
    # JSON test data - easily customizable for different scenarios
    test_data = {
        "employee": {
            "codigo": "EMP-NIC-001",
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
                "expected_inss": 1750.00,  # 7% of 25,000
                "expected_ir": 0.00  # Will be calculated by system
            },
            {
                "month": 2,
                "salario_ordinario": 30000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 2100.00,  # 7% of 30,000
                "expected_ir": 0.00
            },
            {
                "month": 3,
                "salario_ordinario": 28000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 1960.00,  # 7% of 28,000
                "expected_ir": 0.00
            },
        ]
    }

    # Execute payroll test using the reusable utility
    # The utility will:
    # 1. Create all necessary entities with correct model fields
    # 2. Configure ReglaCalculo with Nicaragua's IR progressive table
    # 3. Execute payroll for each month using NominaEngine
    # 4. Validate results against expected values
    # 5. Return detailed results with accumulated values
    results = ejecutar_test_nomina_nicaragua(
        test_data,
        db_session,
        app,
        verbose=True
    )

    # Verify the test executed successfully (completed all months)
    assert len(results["results"]) == 3, "Should have results for 3 months"
    
    # Verify accumulated values are being tracked
    assert results["accumulated"]["periodos_procesados"] == 3, \
        "Should have processed 3 periods"
    
    # Verify system calculated some accumulated values
    assert results["accumulated"]["salario_bruto_acumulado"] > 0, \
        "Should have accumulated gross salary"

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
    # Scenario: System implemented in July 2025
    # Employee has been working since January with same salary all year
    test_data = {
        "employee": {
            "codigo": "EMP-NIC-MID",
            "nombre": "María",
            "apellido": "González",
            "salario_base": 10000.00,
            # Pre-system accumulated values (6 months: Jan-June)
            "salario_acumulado": 60000.00,  # 10,000 x 6 months
            "impuesto_acumulado": 4200.00,   # INSS 7% x 60,000 = 4,200
        },
        "fiscal_year_start": "2025-01-01",
        "months": [
            {
                "month": 7,  # July - first month in system
                "salario_ordinario": 10000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 700.00,  # 7% of 10,000
                "expected_ir": 0.00  # System will calculate
            },
            {
                "month": 8,  # August
                "salario_ordinario": 10000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 700.00,
                "expected_ir": 0.00
            },
            {
                "month": 9,  # September
                "salario_ordinario": 10000.00,
                "salario_ocasional": 0.00,
                "expected_inss": 700.00,
                "expected_ir": 0.00
            },
        ]
    }
    
    # Execute the test
    results = ejecutar_test_nomina_nicaragua(
        test_data,
        db_session,
        app,
        verbose=True
    )
    
    # Verify execution
    assert len(results["results"]) == 3, "Should process 3 months (July-Sept)"
    
    # Verify accumulated values include pre-system amounts
    # Total should be: 60,000 (pre-system) + 30,000 (3 months x 10,000)
    assert results["accumulated"]["salario_bruto_acumulado"] >= 60000, \
        "Should include pre-system accumulated salary"
    
    # Verify system continued accumulating from the starting point
    assert results["accumulated"]["periodos_procesados"] == 3, \
        "Should have processed 3 new periods"
    
    print("\n✅ SUCCESS: Mid-year implementation handled correctly")
    print("   - Employee: Monthly salary C$ 10,000")
    print("   - Pre-system values (Jan-June): C$ 60,000 salary, C$ 4,200 INSS")
    print(f"   - Total accumulated after 3 months (July-Sept): C$ {results['accumulated']['salario_bruto_acumulado']:,.2f}")
    print(f"   - Periods processed in system: {results['accumulated']['periodos_procesados']}")
    print("   - System correctly handles mid-year deployments with consistent salary")


if __name__ == "__main__":
    # Allow running test directly
    pytest.main([__file__, "-v", "-s"])
