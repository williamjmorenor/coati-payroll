#!/usr/bin/env python3
"""Verificar cálculo manual del Ejemplo 2, Mes 3."""

from decimal import Decimal

# Mes 1
mes1_bruto = Decimal('10000')
mes1_inss = mes1_bruto * Decimal('0.07')
mes1_neto = mes1_bruto - mes1_inss

# Mes 2
mes2_bruto = Decimal('10000')
mes2_inss = mes2_bruto * Decimal('0.07')
mes2_neto = mes2_bruto - mes2_inss

# Mes 3
mes3_bruto = Decimal('13000')  # 10,000 + 3,000 bono
mes3_inss = mes3_bruto * Decimal('0.07')
mes3_neto = mes3_bruto - mes3_inss

# Acumulado
acumulado_neto = mes1_neto + mes2_neto + mes3_neto
promedio = acumulado_neto / Decimal('3')
expectativa = promedio * Decimal('12')

# Calcular IR según tabla
if expectativa <= 100000:
    ir_anual = Decimal('0')
elif expectativa <= 200000:
    ir_anual = (expectativa - Decimal('100000')) * Decimal('0.15')
elif expectativa <= 350000:
    ir_anual = Decimal('15000') + (expectativa - Decimal('200000')) * Decimal('0.20')
elif expectativa <= 500000:
    ir_anual = Decimal('45000') + (expectativa - Decimal('350000')) * Decimal('0.25')
else:
    ir_anual = Decimal('82500') + (expectativa - Decimal('500000')) * Decimal('0.30')

ir_proporcional = (ir_anual / Decimal('12')) * Decimal('3')
ir_anterior = Decimal('145') * Decimal('2')  # Meses 1 y 2
ir_mes = ir_proporcional - ir_anterior

print("="*60)
print("CÁLCULO MANUAL - EJEMPLO 2, MES 3")
print("="*60)
print(f"Mes 1 - Bruto: C$ {mes1_bruto:,.2f}, Neto: C$ {mes1_neto:,.2f}")
print(f"Mes 2 - Bruto: C$ {mes2_bruto:,.2f}, Neto: C$ {mes2_neto:,.2f}")
print(f"Mes 3 - Bruto: C$ {mes3_bruto:,.2f}, Neto: C$ {mes3_neto:,.2f}")
print(f"\nAcumulado Neto: C$ {acumulado_neto:,.2f}")
print(f"Promedio Mensual: C$ {promedio:,.2f}")
print(f"Expectativa Anual: C$ {expectativa:,.2f}")
print(f"\nIR Anual: C$ {ir_anual:,.2f}")
print(f"IR Proporcional (3 meses): C$ {ir_proporcional:,.2f}")
print(f"IR Anterior (meses 1-2): C$ {ir_anterior:,.2f}")
print(f"\nIR del Mes 3: C$ {ir_mes:,.2f}")
print(f"IR Esperado: C$ 145.00")
print(f"Diferencia: C$ {abs(ir_mes - Decimal('145')):,.2f}")
print("="*60)

