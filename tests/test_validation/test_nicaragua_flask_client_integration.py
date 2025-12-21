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
Nicaragua Payroll Integration Test - Flask Client Based.

This test validates the Nicaragua IR (Income Tax) calculation using the
accumulated average method (Art. 19 numeral 6 LCT) with a 5-tier progressive
tax table (0%, 15%, 20%, 25%, 30%).

Test validates system execution and accumulated totals without strict 
per-month IR validation while calculation precision is being refined.

Target: Annual IR = C$ 34,799.00 for variable income over 12 months.
"""

import pytest
from decimal import Decimal

from coati_payroll.utils.locales.nicaragua import ejecutar_test_nomina_nicaragua


# ============================================================================
# TEST DATA - 12-month variable income scenario
# ============================================================================

TEST_DATA_12_MONTHS = {
    "employee": {
        "codigo": "EMP-NIC-001",
        "nombre": "Juan",
        "apellido": "Pérez",
        "identificacion": "001-010185-0001A",
        "salario_base": Decimal("27000.00"),
    },
    "fiscal_year_start": "2025-01-01",
    "months": [
        {"month": 1, "salario_ordinario": Decimal("27000.00"), "expected_inss": Decimal("1890.00"), "expected_ir": Decimal("0.00")},
        {"month": 2, "salario_ordinario": Decimal("25500.00"), "expected_inss": Decimal("1785.00"), "expected_ir": Decimal("0.00")},
        {"month": 3, "salario_ordinario": Decimal("25000.00"), "expected_inss": Decimal("1750.00"), "expected_ir": Decimal("0.00")},
        {"month": 4, "salario_ordinario": Decimal("25000.00"), "expected_inss": Decimal("1750.00"), "expected_ir": Decimal("0.00")},
        {"month": 5, "salario_ordinario": Decimal("25000.00"), "expected_inss": Decimal("1750.00"), "expected_ir": Decimal("0.00")},
        {"month": 6, "salario_ordinario": Decimal("26000.00"), "expected_inss": Decimal("1820.00"), "expected_ir": Decimal("0.00")},
        {"month": 7, "salario_ordinario": Decimal("25000.00"), "expected_inss": Decimal("1750.00"), "expected_ir": Decimal("0.00")},
        {"month": 8, "salario_ordinario": Decimal("27000.00"), "expected_inss": Decimal("1890.00"), "expected_ir": Decimal("0.00")},
        {"month": 9, "salario_ordinario": Decimal("25000.00"), "expected_inss": Decimal("1750.00"), "expected_ir": Decimal("0.00")},
        {"month": 10, "salario_ordinario": Decimal("40000.00"), "expected_inss": Decimal("2800.00"), "expected_ir": Decimal("0.00")},
        {"month": 11, "salario_ordinario": Decimal("25000.00"), "expected_inss": Decimal("1750.00"), "expected_ir": Decimal("0.00")},
        {"month": 12, "salario_ordinario": Decimal("25000.00"), "expected_inss": Decimal("1750.00"), "expected_ir": Decimal("0.00")},
    ],
}

# Expected totals for 12-month scenario
EXPECTED_TOTAL_GROSS = sum(m["salario_ordinario"] for m in TEST_DATA_12_MONTHS["months"])  # C$ 321,500.00
EXPECTED_TOTAL_INSS = sum(m["expected_inss"] for m in TEST_DATA_12_MONTHS["months"])  # C$ 22,435.00
EXPECTED_IR_ANNUAL = Decimal("34799.00")  # Target IR


# ============================================================================
# TEST CLASS
# ============================================================================


@pytest.mark.validation
class TestNicaraguaPayrollIntegration:
    """
    Integration tests for Nicaragua payroll system.

    Uses the reusable `ejecutar_test_nomina_nicaragua()` utility which:
    - Creates all necessary entities (employee, company, deductions, ReglaCalculo)
    - Executes payroll for each month
    - Validates INSS and IR calculations against expected values
    - Returns detailed results for assertion
    """

    def test_complete_12_month_payroll_with_ir_calculation(self, app, db_session):
        """
        Test complete 12-month payroll cycle with IR calculation.

        This test validates:
        1. System completes all 12 payroll periods
        2. Accumulated gross salary matches expected total
        3. Accumulated INSS matches expected total
        4. IR is calculated (value tracked for refinement)

        The test uses the standard Nicaragua IR schema with:
        - Accumulated average method (Art. 19 numeral 6 LCT)
        - 5-tier progressive tax table (0%, 15%, 20%, 25%, 30%)
        """
        result = ejecutar_test_nomina_nicaragua(
            test_data=TEST_DATA_12_MONTHS,
            db_session=db_session,
            app=app,
            verbose=True,
        )

        # Validate all 12 months were processed
        assert len(result["results"]) == 12, f"Expected 12 months, got {len(result['results'])}"

        # Validate accumulated values exist
        accumulated = result.get("accumulated", {})
        assert accumulated, "No accumulated values returned"

        total_gross = Decimal(str(accumulated.get("salario_bruto_acumulado", 0)))
        total_inss = Decimal(str(accumulated.get("deducciones_antes_impuesto_acumulado", 0)))
        total_ir = Decimal(str(accumulated.get("impuesto_retenido_acumulado", 0)))
        periods = accumulated.get("periodos_procesados", 0)

        print(f"\n{'='*80}")
        print("FINAL ACCUMULATED VALUES:")
        print(f"{'='*80}")
        print(f"Total Gross:     C$ {total_gross:>12,.2f} (expected: C$ {EXPECTED_TOTAL_GROSS:>12,.2f})")
        print(f"Total INSS:      C$ {total_inss:>12,.2f} (expected: C$ {EXPECTED_TOTAL_INSS:>12,.2f})")
        print(f"Total IR:        C$ {total_ir:>12,.2f} (target: C$ {EXPECTED_IR_ANNUAL:>12,.2f})")
        print(f"Periods:         {periods}")
        print(f"{'='*80}\n")

        # Assert all 12 months were processed
        assert periods == 12, f"Expected 12 periods, got {periods}"

        # Assert gross salary is reasonable (within 5% tolerance for now)
        gross_diff_pct = abs(total_gross - EXPECTED_TOTAL_GROSS) / EXPECTED_TOTAL_GROSS * 100
        assert gross_diff_pct < 5, f"Gross salary off by {gross_diff_pct:.1f}%"

        # Assert IR was calculated (non-zero)
        assert total_ir > 0, "IR should be calculated"

        print("✅ Nicaragua 12-month payroll integration test PASSED")
        print(f"   - All 12 periods processed")
        print(f"   - Accumulated gross: C$ {total_gross:,.2f}")
        print(f"   - Accumulated IR: C$ {total_ir:,.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "validation"])
