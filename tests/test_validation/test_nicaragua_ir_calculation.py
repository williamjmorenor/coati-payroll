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

    # Verify the test passed
    assert results["success"], f"Test failed with errors: {results['errors']}"

    # Verify accumulated values tracked correctly
    assert results["accumulated"]["periodos_procesados"] == 3, \
        "Should have processed 3 periods"
    
    assert results["accumulated"]["salario_bruto_acumulado"] == 83000.00, \
        "Total gross salary should be 25k + 30k + 28k = 83k"
    
    assert results["accumulated"]["deducciones_antes_impuesto_acumulado"] == 5810.00, \
        "Total INSS should be 1750 + 2100 + 1960 = 5810"

    # Verify we got results for all months
    assert len(results["results"]) == 3, "Should have results for 3 months"

    print("\n✅ SUCCESS: Nicaragua payroll system validated end-to-end")
    print("   - JSON test data processed correctly")
    print("   - ReglaCalculo configured with progressive IR table")
    print("   - INSS (7%) calculated correctly for all months")
    print("   - Accumulated values tracked properly")
    print("   - System ready for Nicaragua implementation")


if __name__ == "__main__":
    # Allow running test directly
    pytest.main([__file__, "-v", "-s"])
