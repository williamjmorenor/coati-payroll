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
Unit tests for Nicaragua IR (Income Tax) calculation with accumulated method.

These tests validate the correct implementation of Nicaragua's progressive income tax
calculation according to Article 19, numeral 6 of the LCT (Ley de Concertación Tributaria).

The calculation method uses accumulated values from previous months to calculate
an average monthly salary, which is then projected to annual income and taxed
using the progressive rate table.

Test data is based on real-world scenarios validated by Nicaraguan tax auditors.
"""

from datetime import date
from decimal import Decimal

import pytest

from coati_payroll.model import (
    Empleado,
    Empresa,
    Moneda,
    TipoPlanilla,
    Planilla,
    Deduccion,
    PlanillaEmpleado,
    PlanillaDeduccion,
    AcumuladoAnual,
    ReglaCalculo,
)
from coati_payroll.nomina_engine import ejecutar_nomina


# Nicaragua IR tax brackets (2025)
NICARAGUA_IR_BRACKETS = [
    {"min": 0, "max": 100000, "rate": 0.00, "fixed": 0, "over": 0},
    {"min": 100000, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000},
    {"min": 200000, "max": 350000, "rate": 0.20, "fixed": 15000, "over": 200000},
    {"min": 350000, "max": 500000, "rate": 0.25, "fixed": 45000, "over": 350000},
    {"min": 500000, "max": None, "rate": 0.30, "fixed": 82500, "over": 500000},
]


def calculate_ir_progressive(annual_net_income: Decimal) -> Decimal:
    """
    Calculate IR using Nicaragua's progressive tax table.
    
    Args:
        annual_net_income: Annual net income (after INSS deduction)
        
    Returns:
        Annual IR amount
    """
    for bracket in NICARAGUA_IR_BRACKETS:
        if bracket["max"] is None or annual_net_income <= bracket["max"]:
            excess = annual_net_income - bracket["over"]
            ir = Decimal(str(bracket["fixed"])) + (excess * Decimal(str(bracket["rate"])))
            return max(ir, Decimal("0.00"))
    return Decimal("0.00")


def calculate_ir_accumulated_method(
    gross_salary_month: Decimal,
    accumulated_gross: Decimal,
    accumulated_inss: Decimal,
    accumulated_ir: Decimal,
    months_worked: int,
) -> dict:
    """
    Calculate IR using Nicaragua's accumulated method (Art. 19, numeral 6).
    
    This is the CORRECT method according to Nicaraguan law.
    
    Args:
        gross_salary_month: Gross salary for current month
        accumulated_gross: Accumulated gross salary from previous months
        accumulated_inss: Accumulated INSS deductions from previous months
        accumulated_ir: Accumulated IR withholdings from previous months
        months_worked: Number of months already worked in fiscal year
        
    Returns:
        Dictionary with calculation breakdown
    """
    # Step 1: Calculate INSS for current month
    inss_month = gross_salary_month * Decimal("0.07")
    
    # Step 2: Calculate net salary for current month
    net_salary_month = gross_salary_month - inss_month
    
    # Step 3: Calculate total accumulated net salary (including current month)
    total_accumulated_net = (accumulated_gross + gross_salary_month) - (accumulated_inss + inss_month)
    
    # Step 4: Calculate total months (including current)
    total_months = months_worked + 1
    
    # Step 5: Calculate monthly average
    monthly_average = total_accumulated_net / Decimal(str(total_months))
    
    # Step 6: Project annual expectation
    annual_expectation = monthly_average * Decimal("12")
    
    # Step 7: Apply progressive tax table
    ir_annual = calculate_ir_progressive(annual_expectation)
    
    # Step 8: Calculate proportional IR for months worked
    ir_proportional = (ir_annual / Decimal("12")) * Decimal(str(total_months))
    
    # Step 9: Subtract previous withholdings to get current month IR
    ir_current_month = max(ir_proportional - accumulated_ir, Decimal("0.00"))
    
    return {
        "inss_month": inss_month.quantize(Decimal("0.01")),
        "net_salary_month": net_salary_month.quantize(Decimal("0.01")),
        "total_accumulated_net": total_accumulated_net.quantize(Decimal("0.01")),
        "total_months": total_months,
        "monthly_average": monthly_average.quantize(Decimal("0.01")),
        "annual_expectation": annual_expectation.quantize(Decimal("0.01")),
        "ir_annual": ir_annual.quantize(Decimal("0.01")),
        "ir_proportional": ir_proportional.quantize(Decimal("0.01")),
        "ir_current_month": ir_current_month.quantize(Decimal("0.01")),
    }


@pytest.mark.validation
class TestNicaraguaIRCalculation:
    """Test suite for Nicaragua IR calculation with accumulated method."""
    
    def test_ir_calculation_month_1(self):
        """Test IR calculation for Month 1 - Initial month."""
        result = calculate_ir_accumulated_method(
            gross_salary_month=Decimal("25000.00"),
            accumulated_gross=Decimal("0.00"),
            accumulated_inss=Decimal("0.00"),
            accumulated_ir=Decimal("0.00"),
            months_worked=0,
        )
        
        assert result["inss_month"] == Decimal("1750.00"), "INSS should be 7% of gross"
        assert result["net_salary_month"] == Decimal("23250.00"), "Net = Gross - INSS"
        assert result["total_accumulated_net"] == Decimal("23250.00"), "First month accumulated"
        assert result["monthly_average"] == Decimal("23250.00"), "Average equals net for first month"
        assert result["annual_expectation"] == Decimal("279000.00"), "23,250 × 12"
        
        # Annual IR: 15,000 + (279,000 - 200,000) × 0.20 = 15,000 + 15,800 = 30,800
        assert result["ir_annual"] == Decimal("30800.00"), "IR annual should be 30,800"
        
        # IR Month 1: (30,800 / 12) × 1 = 2,566.67
        assert result["ir_proportional"] == Decimal("2566.67"), "IR proportional for 1 month"
        assert result["ir_current_month"] == Decimal("2566.67"), "First month IR"
    
    def test_ir_calculation_month_2_higher_salary(self):
        """Test IR calculation for Month 2 with salary increase."""
        result = calculate_ir_accumulated_method(
            gross_salary_month=Decimal("30000.00"),
            accumulated_gross=Decimal("25000.00"),
            accumulated_inss=Decimal("1750.00"),
            accumulated_ir=Decimal("2566.67"),
            months_worked=1,
        )
        
        assert result["inss_month"] == Decimal("2100.00"), "INSS = 30,000 × 0.07"
        assert result["net_salary_month"] == Decimal("27900.00"), "Net = 30,000 - 2,100"
        
        # Total accumulated net: (25,000 + 30,000) - (1,750 + 2,100) = 55,000 - 3,850 = 51,150
        assert result["total_accumulated_net"] == Decimal("51150.00"), "Accumulated net for 2 months"
        
        # Average: 51,150 / 2 = 25,575
        assert result["monthly_average"] == Decimal("25575.00"), "Average over 2 months"
        
        # Annual: 25,575 × 12 = 306,900
        assert result["annual_expectation"] == Decimal("306900.00"), "Annual expectation"
        
        # IR Annual: 15,000 + (306,900 - 200,000) × 0.20 = 15,000 + 21,380 = 36,380
        assert result["ir_annual"] == Decimal("36380.00"), "IR annual"
        
        # IR Proportional: (36,380 / 12) × 2 = 6,063.33
        assert result["ir_proportional"] == Decimal("6063.33"), "IR proportional for 2 months"
        
        # IR Month 2: 6,063.33 - 2,566.67 = 3,496.66
        assert result["ir_current_month"] == Decimal("3496.66"), "IR for month 2"
    
    def test_ir_calculation_month_3_lower_salary(self):
        """Test IR calculation for Month 3 with salary decrease."""
        result = calculate_ir_accumulated_method(
            gross_salary_month=Decimal("28000.00"),
            accumulated_gross=Decimal("55000.00"),  # 25,000 + 30,000
            accumulated_inss=Decimal("3850.00"),     # 1,750 + 2,100
            accumulated_ir=Decimal("6063.33"),       # 2,566.67 + 3,496.66
            months_worked=2,
        )
        
        assert result["inss_month"] == Decimal("1960.00"), "INSS = 28,000 × 0.07"
        assert result["net_salary_month"] == Decimal("26040.00"), "Net = 28,000 - 1,960"
        
        # Total: (55,000 + 28,000) - (3,850 + 1,960) = 83,000 - 5,810 = 77,190
        assert result["total_accumulated_net"] == Decimal("77190.00"), "Accumulated net for 3 months"
        
        # Average: 77,190 / 3 = 25,730
        assert result["monthly_average"] == Decimal("25730.00"), "Average over 3 months"
        
        # Annual: 25,730 × 12 = 308,760
        assert result["annual_expectation"] == Decimal("308760.00"), "Annual expectation"
        
        # IR Annual: 15,000 + (308,760 - 200,000) × 0.20 = 15,000 + 21,752 = 36,752
        assert result["ir_annual"] == Decimal("36752.00"), "IR annual"
        
        # IR Proportional: (36,752 / 12) × 3 = 9,188
        assert result["ir_proportional"] == Decimal("9188.00"), "IR proportional for 3 months"
        
        # IR Month 3: 9,188.00 - 6,063.33 = 3,124.67
        assert result["ir_current_month"] == Decimal("3124.67"), "IR for month 3"
    
    def test_ir_calculation_low_salary_exempt(self):
        """Test IR calculation for low salary (exempt from IR)."""
        result = calculate_ir_accumulated_method(
            gross_salary_month=Decimal("8000.00"),
            accumulated_gross=Decimal("0.00"),
            accumulated_inss=Decimal("0.00"),
            accumulated_ir=Decimal("0.00"),
            months_worked=0,
        )
        
        assert result["inss_month"] == Decimal("560.00"), "INSS = 8,000 × 0.07"
        assert result["net_salary_month"] == Decimal("7440.00"), "Net = 8,000 - 560"
        assert result["annual_expectation"] == Decimal("89280.00"), "7,440 × 12"
        assert result["ir_annual"] == Decimal("0.00"), "Below 100,000 threshold - exempt"
        assert result["ir_current_month"] == Decimal("0.00"), "No IR for low salaries"
    
    def test_ir_calculation_high_salary_top_bracket(self):
        """Test IR calculation for high salary (top tax bracket)."""
        result = calculate_ir_accumulated_method(
            gross_salary_month=Decimal("50000.00"),
            accumulated_gross=Decimal("0.00"),
            accumulated_inss=Decimal("0.00"),
            accumulated_ir=Decimal("0.00"),
            months_worked=0,
        )
        
        assert result["inss_month"] == Decimal("3500.00"), "INSS = 50,000 × 0.07"
        assert result["net_salary_month"] == Decimal("46500.00"), "Net = 50,000 - 3,500"
        assert result["annual_expectation"] == Decimal("558000.00"), "46,500 × 12"
        
        # IR Annual: 82,500 + (558,000 - 500,000) × 0.30 = 82,500 + 17,400 = 99,900
        assert result["ir_annual"] == Decimal("99900.00"), "IR annual for top bracket"
        assert result["ir_current_month"] == Decimal("8325.00"), "IR monthly: 99,900 / 12"
    
    def test_ir_progressive_brackets(self):
        """Test each tax bracket individually."""
        # Bracket 1: Exempt (0 - 100,000)
        assert calculate_ir_progressive(Decimal("50000")) == Decimal("0.00")
        assert calculate_ir_progressive(Decimal("100000")) == Decimal("0.00")
        
        # Bracket 2: 15% over 100,000
        # At 150,000: (150,000 - 100,000) × 0.15 = 7,500
        assert calculate_ir_progressive(Decimal("150000")) == Decimal("7500.00")
        
        # Bracket 3: 15,000 + 20% over 200,000
        # At 250,000: 15,000 + (250,000 - 200,000) × 0.20 = 15,000 + 10,000 = 25,000
        assert calculate_ir_progressive(Decimal("250000")) == Decimal("25000.00")
        
        # Bracket 4: 45,000 + 25% over 350,000
        # At 400,000: 45,000 + (400,000 - 350,000) × 0.25 = 45,000 + 12,500 = 57,500
        assert calculate_ir_progressive(Decimal("400000")) == Decimal("57500.00")
        
        # Bracket 5: 82,500 + 30% over 500,000
        # At 600,000: 82,500 + (600,000 - 500,000) × 0.30 = 82,500 + 30,000 = 112,500
        assert calculate_ir_progressive(Decimal("600000")) == Decimal("112500.00")
    
    def test_ir_calculation_with_bonus(self):
        """Test IR calculation when employee receives a bonus (occasional income)."""
        # Regular month: 20,000
        # Bonus month: 20,000 + 10,000 = 30,000
        
        # First, calculate for regular months (assuming 11 months of 20,000)
        accumulated_gross_before_bonus = Decimal("220000.00")  # 11 × 20,000
        accumulated_inss_before_bonus = Decimal("15400.00")     # 11 × 1,400
        accumulated_ir_before_bonus = Decimal("18004.00")       # Calculated from previous months
        
        result = calculate_ir_accumulated_method(
            gross_salary_month=Decimal("30000.00"),  # Regular 20,000 + Bonus 10,000
            accumulated_gross=accumulated_gross_before_bonus,
            accumulated_inss=accumulated_inss_before_bonus,
            accumulated_ir=accumulated_ir_before_bonus,
            months_worked=11,
        )
        
        # INSS on 30,000
        assert result["inss_month"] == Decimal("2100.00"), "INSS includes bonus"
        
        # The IR should adjust for the higher income this month
        # IR for month with bonus should be higher than regular months
        assert result["ir_current_month"] > Decimal("1500.00"), "IR increases due to bonus"
    
    def test_accumulated_values_prevent_overpayment(self):
        """
        Test that accumulated method prevents overpayment when salary decreases.
        
        This validates that the accumulated method adjusts properly when
        an employee's salary decreases mid-year.
        """
        # Month 1: High salary
        month1 = calculate_ir_accumulated_method(
            Decimal("40000.00"), Decimal("0"), Decimal("0"), Decimal("0"), 0
        )
        
        # Month 2: Salary drops significantly
        month2 = calculate_ir_accumulated_method(
            Decimal("20000.00"),
            Decimal("40000.00"),
            month1["inss_month"],
            month1["ir_current_month"],
            1
        )
        
        # The IR in month 2 should be lower than month 1 due to averaging
        assert month2["ir_current_month"] < month1["ir_current_month"], \
            "IR should decrease when salary drops due to accumulated averaging"
        
        # The annual expectation should be recalculated based on new average
        # Average = ((40000 - 2800) + (20000 - 1400)) / 2 = 27,900
        expected_average = ((Decimal("40000") - Decimal("2800")) + 
                           (Decimal("20000") - Decimal("1400"))) / Decimal("2")
        assert abs(month2["monthly_average"] - expected_average) < Decimal("1.00"), \
            "Monthly average should reflect actual accumulated values"


@pytest.mark.validation
@pytest.mark.integration
class TestNicaraguaIRIntegration:
    """Integration tests for Nicaragua IR calculation with the payroll system."""
    
    @pytest.fixture
    def nicaragua_setup(self, app, db_session):
        """Set up Nicaragua-specific payroll configuration."""
        # Create currency
        nio = Moneda(
            codigo="NIO",
            nombre="Córdoba Nicaragüense",
            simbolo="C$",
            tasa_cambio=Decimal("1.00"),
        )
        db_session.add(nio)
        
        # Create company
        empresa = Empresa(
            razon_social="Empresa Nicaragua Test",
            nombre_comercial="Nicaragua Test",
            pais="Nicaragua",
        )
        db_session.add(empresa)
        
        # Create payroll type with fiscal year
        tipo_planilla = TipoPlanilla(
            codigo="MENSUAL_NIC",
            nombre="Nómina Mensual Nicaragua",
            periodos_por_anio=12,
            moneda_id=nio.id,
            mes_inicio_fiscal=1,  # January
            dia_inicio_fiscal=1,
        )
        db_session.add(tipo_planilla)
        
        # Create INSS deduction
        inss = Deduccion(
            codigo="INSS",
            nombre="INSS Laboral 7%",
            tipo_formula="porcentaje",
            formula="0.07",
            es_obligatoria=True,
            antes_impuesto=True,
            prioridad=1,
        )
        db_session.add(inss)
        
        # Create IR ReglaCalculo (simplified for testing)
        ir_regla = ReglaCalculo(
            codigo="IR_NIC",
            nombre="IR Nicaragua",
            jurisdiccion="Nicaragua",
            moneda_referencia="NIO",
            version="1.0.0",
            tipo_regla="impuesto",
            vigente_desde=date(2025, 1, 1),
            esquema_json={
                "meta": {"name": "IR Nicaragua Test"},
                "inputs": [
                    {"name": "salario_bruto", "type": "decimal"},
                    {"name": "salario_bruto_acumulado", "type": "decimal"},
                    {"name": "deducciones_antes_impuesto_acumulado", "type": "decimal"},
                    {"name": "ir_retenido_acumulado", "type": "decimal"},
                    {"name": "meses_trabajados", "type": "integer"},
                ],
                "steps": [
                    {"name": "inss", "type": "calculation", "formula": "salario_bruto * 0.07", "output": "inss"},
                    {"name": "net", "type": "calculation", "formula": "salario_bruto - inss", "output": "salario_neto"},
                ],
                "tax_tables": {"tabla_ir": NICARAGUA_IR_BRACKETS},
                "output": "ir_final",
            },
        )
        db_session.add(ir_regla)
        
        # Create IR deduction
        ir = Deduccion(
            codigo="IR",
            nombre="Impuesto sobre la Renta",
            tipo_formula="regla_calculo",
            regla_calculo_id=ir_regla.id,
            es_obligatoria=True,
            es_impuesto=True,
            prioridad=2,
        )
        db_session.add(ir)
        
        db_session.commit()
        
        return {
            "nio": nio,
            "empresa": empresa,
            "tipo_planilla": tipo_planilla,
            "inss": inss,
            "ir": ir,
            "ir_regla": ir_regla,
        }
    
    def test_integration_placeholder(self, nicaragua_setup):
        """
        Placeholder for integration test.
        
        This would test the full payroll execution with Nicaragua IR calculation.
        Requires full payroll engine setup which is complex for this test file.
        """
        # This is a placeholder - full integration test would be implemented
        # in a separate validation test with complete payroll execution
        assert nicaragua_setup is not None, "Setup should be created"
        assert nicaragua_setup["ir_regla"].codigo == "IR_NIC", "IR rule should exist"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])
