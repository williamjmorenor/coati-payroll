#!/usr/bin/env python3
"""
Validación rigurosa del cálculo de IR en Nicaragua.

Este script valida que el sistema calcula correctamente el IR anual de 34,799.00
para el trabajador de ejemplo con ingresos variables durante 12 meses.

Datos del trabajador:
- Salario ordinario: C$ 300,000 anuales (25,000 mensuales en promedio)
- Ingresos ocasionales: C$ 17,000 (bonos, comisiones, incentivos)
- IR esperado anual: C$ 34,799.00
"""

import json
from decimal import Decimal

# Datos del trabajador basados en los archivos adjuntos proporcionados
test_data_nicaragua = {
    "employee": {
        "codigo": "EMP-001",
        "nombre": "Trabajador",
        "apellido": "Test",
        "identificacion": "001-000000-0001Z",
        "salario_base": 25000.00,  # Salario ordinario promedio
    },
    "fiscal_year_start": "2025-01-01",
    "months": [
        # Mes 1: Enero
        {
            "month": 1,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 1000.00,
            "bonos": 0.00,
            "incentivos": 1000.00,
            "salario_ocasional": 1000.00,
            "total_bruto": 27000.00,
            "expected_inss": 1890.00,  # 7% de (25,000 + 500 horas extra + 1,000 comisión)
            "expected_ir": 2938.67,
        },
        # Mes 2: Febrero
        {
            "month": 2,
            "salario_ordinario": 25000.00,
            "horas_extra": 500.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25500.00,
            "expected_inss": 1785.00,
            "expected_ir": 2659.67,
        },
        # Mes 3: Marzo
        {
            "month": 3,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25000.00,
            "expected_inss": 1750.00,
            "expected_ir": 2566.67,
        },
        # Mes 4: Abril
        {
            "month": 4,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25000.00,
            "expected_inss": 1750.00,
            "expected_ir": 2566.67,
        },
        # Mes 5: Mayo
        {
            "month": 5,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25000.00,
            "expected_inss": 1750.00,
            "expected_ir": 2566.67,
        },
        # Mes 6: Junio
        {
            "month": 6,
            "salario_ordinario": 25000.00,
            "horas_extra": 1000.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 1000.00,
            "salario_ocasional": 1000.00,
            "total_bruto": 27000.00,
            "expected_inss": 1890.00,
            "expected_ir": 2938.67,
        },
        # Mes 7: Julio
        {
            "month": 7,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25000.00,
            "expected_inss": 1750.00,
            "expected_ir": 2566.67,
        },
        # Mes 8: Agosto
        {
            "month": 8,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 2000.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 27000.00,
            "expected_inss": 1890.00,
            "expected_ir": 2938.67,
        },
        # Mes 9: Septiembre
        {
            "month": 9,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25000.00,
            "expected_inss": 1750.00,
            "expected_ir": 2566.67,
        },
        # Mes 10: Octubre (bono)
        {
            "month": 10,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 15000.00,  # Bono ocasional
            "incentivos": 0.00,
            "salario_ocasional": 15000.00,
            "total_bruto": 40000.00,
            "expected_inss": 2800.00,  # 1,750 + 1,050 (7% del bono)
            "expected_ir": 5356.67,  # IR ordinario + IR ocasional
        },
        # Mes 11: Noviembre
        {
            "month": 11,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25000.00,
            "expected_inss": 1750.00,
            "expected_ir": 2566.67,
        },
        # Mes 12: Diciembre
        {
            "month": 12,
            "salario_ordinario": 25000.00,
            "horas_extra": 0.00,
            "comisiones": 0.00,
            "bonos": 0.00,
            "incentivos": 0.00,
            "salario_ocasional": 0.00,
            "total_bruto": 25000.00,
            "expected_inss": 1750.00,
            "expected_ir": 2566.67,
        },
    ],
}

# Totales anuales esperados
EXPECTED_TOTALS = {
    "salario_ordinario": 300000.00,
    "horas_extra": 1500.00,
    "comisiones": 3000.00,
    "bonos": 15000.00,
    "incentivos": 2000.00,
    "salario_ocasional": 17000.00,
    "total_bruto": 321500.00,
    "total_inss": 22505.00,  # INSS anual acumulado
    "total_ir_annual": 34799.00,  # IR anual total esperado (CRÍTICO)
}


def calculate_ir_manually():
    """
    Calcula el IR manualmente usando el método acumulado para validar.
    
    Este cálculo debe producir exactamente 34,799.00 en diciembre.
    """
    months = test_data_nicaragua["months"]
    cumulative_gross = Decimal("0")
    cumulative_inss = Decimal("0")
    cumulative_ir = Decimal("0")
    monthly_irs = []
    
    print("\n" + "="*100)
    print("CÁLCULO MANUAL DEL IR SEGÚN MÉTODO ACUMULADO (Art. 19 numeral 6 LCT)")
    print("="*100)
    
    for i, month_data in enumerate(months):
        month_num = month_data["month"]
        bruto = Decimal(str(month_data["total_bruto"]))
        
        # PASO 1: Calcular INSS del mes
        inss_mes = bruto * Decimal("0.07")
        
        # PASO 2: Acumular
        cumulative_gross += bruto
        cumulative_inss += inss_mes
        
        # PASO 3: Calcular salario neto acumulado
        salario_neto_acumulado = cumulative_gross - cumulative_inss
        
        # PASO 4: Calcular meses totales
        meses_totales = i + 1
        
        # PASO 5: Promedio mensual
        promedio_mensual = salario_neto_acumulado / Decimal(str(meses_totales))
        
        # PASO 6: Proyectar expectativa anual
        expectativa_anual = promedio_mensual * Decimal("12")
        
        # PASO 7: Aplicar tabla progresiva
        ir_anual = _aplicar_tabla_progresiva(expectativa_anual)
        
        # PASO 8: IR proporcional a meses trabajados
        ir_proporcional = (ir_anual / Decimal("12")) * Decimal(str(meses_totales))
        
        # PASO 9: IR del mes = diferencia
        ir_mes = max(ir_proporcional - cumulative_ir, Decimal("0"))
        cumulative_ir = ir_proporcional
        
        monthly_irs.append(ir_mes)
        
        print(f"\nMES {month_num:2d}:")
        print(f"  Salario Bruto Mes:              C$ {bruto:>12,.2f}")
        print(f"  Salario Bruto Acumulado:        C$ {cumulative_gross:>12,.2f}")
        print(f"  INSS Mes:                       C$ {inss_mes:>12,.2f}")
        print(f"  INSS Acumulado:                 C$ {cumulative_inss:>12,.2f}")
        print(f"  Salario Neto Acumulado:         C$ {salario_neto_acumulado:>12,.2f}")
        print(f"  Meses Totales:                      {meses_totales:>12}")
        print(f"  Promedio Mensual:               C$ {promedio_mensual:>12,.2f}")
        print(f"  Expectativa Anual:              C$ {expectativa_anual:>12,.2f}")
        print(f"  IR Anual Calculado:             C$ {ir_anual:>12,.2f}")
        print(f"  IR Proporcional (x{meses_totales}/12):        C$ {ir_proporcional:>12,.2f}")
        print(f"  IR Acumulado Anterior:          C$ {(cumulative_ir - ir_mes):>12,.2f}")
        print(f"  IR del Mes:                     C$ {ir_mes:>12,.2f}")
        print(f"  IR Acumulado:                   C$ {cumulative_ir:>12,.2f}")
    
    print("\n" + "="*100)
    print("RESUMEN ANUAL:")
    print("="*100)
    print(f"Salario Bruto Total:                C$ {cumulative_gross:>12,.2f}")
    print(f"INSS Total:                         C$ {cumulative_inss:>12,.2f}")
    print(f"IR Total Acumulado (DICIEMBRE):     C$ {cumulative_ir:>12,.2f}")
    print(f"Esperado:                           C$ {EXPECTED_TOTALS['total_ir_annual']:>12,.2f}")
    print(f"Diferencia:                         C$ {abs(cumulative_ir - Decimal(str(EXPECTED_TOTALS['total_ir_annual']))):>12,.2f}")
    
    match = abs(cumulative_ir - Decimal(str(EXPECTED_TOTALS["total_ir_annual"]))) < Decimal("1.00")
    if match:
        print("\n✅ VALIDACIÓN EXITOSA: El IR calculado coincide con el esperado")
    else:
        print("\n❌ VALIDACIÓN FALLIDA: Existe discrepancia en el cálculo del IR")
    
    print("="*100 + "\n")
    
    return {
        "total_gross": cumulative_gross,
        "total_inss": cumulative_inss,
        "total_ir": cumulative_ir,
        "monthly_irs": monthly_irs,
        "matches_expected": match,
    }


def _aplicar_tabla_progresiva(renta_anual: Decimal) -> Decimal:
    """
    Aplica la tabla progresiva del IR de Nicaragua.
    
    Tabla vigente (Ley 891):
    - C$ 0 - 100,000: 0%
    - C$ 100,000 - 200,000: 15% sobre exceso de 100,000
    - C$ 200,000 - 350,000: C$ 15,000 + 20% sobre exceso de 200,000
    - C$ 350,000 - 500,000: C$ 45,000 + 25% sobre exceso de 350,000
    - C$ 500,000+: C$ 82,500 + 30% sobre exceso de 500,000
    """
    if renta_anual <= Decimal("100000"):
        return Decimal("0")
    elif renta_anual <= Decimal("200000"):
        return (renta_anual - Decimal("100000")) * Decimal("0.15")
    elif renta_anual <= Decimal("350000"):
        return Decimal("15000") + (renta_anual - Decimal("200000")) * Decimal("0.20")
    elif renta_anual <= Decimal("500000"):
        return Decimal("45000") + (renta_anual - Decimal("350000")) * Decimal("0.25")
    else:
        return Decimal("82500") + (renta_anual - Decimal("500000")) * Decimal("0.30")


if __name__ == "__main__":
    print("\n" + "*"*100)
    print("VALIDACIÓN RIGUROSA: Cálculo de IR en Nicaragua")
    print("*"*100)
    
    result = calculate_ir_manually()
    
    # Mostrar datos para el test del sistema
    print("\nJSON para prueba de sistema:")
    print(json.dumps(test_data_nicaragua, indent=2))
    
    print("\n" + "*"*100)
    if result["matches_expected"]:
        print("✅ RESULTADO: El cálculo manual produce el IR esperado de C$ 34,799.00")
        print("El sistema debe replicar exactamente este resultado.")
    else:
        print("❌ RESULTADO: Hay discrepancia en el cálculo.")
    print("*"*100 + "\n")
