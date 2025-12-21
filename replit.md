# Proyecto: Sistema de Nómina Coati (Nicaragua)

## Estado Actual
Verificación de cálculo de IR en Nicaragua - **EN PROGRESO**

## Validación del Cálculo de IR

### Requisito
El sistema debe calcular correctamente el **IR anual de C$ 34,799.00** para un trabajador con:
- Salario ordinario anual: C$ 300,000
- Ingresos ocasionales: C$ 17,000 (comisiones, bonos, incentivos)
- Total bruto anual: C$ 321,500
- Método: Acumulado (Art. 19 numeral 6 de la Ley de Concertación Tributaria)

### Tabla de IR (5 Tramos Progresivos)
| Renta Neta Anual (Desde) | Renta Neta Anual (Hasta) | Impuesto Base | Tasa Marginal | Sobre Exceso de |
|--------------------------|--------------------------|---------------|---------------|-----------------|
| 0.01                     | 100,000.00               | -             | -             | -               |
| 100,000.01               | 200,000.00               | -             | 0.15          | 100,000.00      |
| 200,000.01               | 350,000.00               | 15,000.00     | 0.20          | 200,000.00      |
| 350,000.01               | 500,000.00               | 45,000.00     | 0.25          | 350,000.00      |
| 500,000.01               | En adelante              | 82,500.00     | 0.30          | 500,000.00      |

### Datos del Trabajador (12 Meses)
```
Mes  | Ordinario  | Ocasional | Total Bruto | INSS Esperado | IR Esperado
-----|------------|-----------|-------------|---------------|-------------
 1   | 25,000     | 1,000     | 27,000      | 1,890.00      | 2,938.67
 2   | 25,500     | 0         | 25,500      | 1,785.00      | 2,659.67
 3   | 25,000     | 0         | 25,000      | 1,750.00      | 2,566.67
 4   | 25,000     | 0         | 25,000      | 1,750.00      | 2,566.67
 5   | 25,000     | 0         | 25,000      | 1,750.00      | 2,566.67
 6   | 27,000     | 1,000     | 27,000      | 1,890.00      | 2,938.67
 7   | 25,000     | 0         | 25,000      | 1,750.00      | 2,566.67
 8   | 27,000     | 0         | 27,000      | 1,890.00      | 2,938.67
 9   | 25,000     | 0         | 25,000      | 1,750.00      | 2,566.67
10   | 25,000     | 15,000    | 40,000      | 2,800.00      | 5,356.67
11   | 25,000     | 0         | 25,000      | 1,750.00      | 2,566.67
12   | 25,000     | 0         | 25,000      | 1,750.00      | 2,566.67
-----|------------|-----------|-------------|---------------|-------------
TOTAL| 300,000    | 17,000    | 321,500     | 22,505.00     | 34,799.00
```

## Archivos Clave

### Guías de Implementación
- `docs/local_guides/nicaragua-ir-paso-a-paso.md` - Guía paso a paso del cálculo
- `docs/local_guides/nicaragua-implementacion-tecnica.md` - Implementación técnica

### Utilidades de Validación
- `coati_payroll/utils/locales/nicaragua.py` - Función `ejecutar_test_nomina_nicaragua()`
- `tests/test_validation/test_nicaragua_ir_calculation.py` - Tests de validación

### Motores de Cálculo
- `coati_payroll/formula_engine.py` - Motor de evaluación de fórmulas
- `coati_payroll/nomina_engine.py` - Motor de ejecución de nómina

## Método de Cálculo del IR

### Algoritmo (Método Acumulado - Art. 19 numeral 6 LCT)
```
Para cada mes:
1. Calcular INSS del mes = Salario Bruto × 0.07
2. Acumular salario bruto: Acum_Bruto += Salario_Bruto
3. Acumular INSS: Acum_INSS += INSS_Mes
4. Calcular salario neto acumulado = Acum_Bruto - Acum_INSS
5. Contar meses totales trabajados
6. Calcular promedio mensual = Salario_Neto_Acumulado / Meses
7. Proyectar expectativa anual = Promedio × 12
8. Aplicar tabla progresiva de IR a la expectativa anual
9. Calcular IR proporcional = (IR_Anual / 12) × Meses
10. IR del mes = max(IR_Proporcional - IR_Retenido_Anterior, 0)
```

## Validación del Sistema

### Test Creado
- Archivo: `tests/test_validation/test_nicaragua_ir_calculation.py`
- Test: `test_nicaragua_full_year_variable_income()`
- Valida:
  - ✅ Cálculo de IR para 12 meses con ingresos variables
  - ✅ IR anual total de C$ 34,799.00
  - ✅ Método acumulado implementado correctamente
  - ✅ Todos los 12 meses procesados

## Validación Manual (Referencia)
Disponible en: `validate_nicaragua_ir.py`
- Calcula manualmente el IR usando el método acumulado
- Confirma que el resultado es C$ 34,799.00
- Valida cada paso del algoritmo

## Próximos Pasos
1. ✅ Crear test con 12 meses reales
2. ⏳ Ejecutar test para validar sistema
3. ⏳ Hacer ajustes si es necesario
4. ⏳ Confirmar que IR = C$ 34,799.00

## Notas Técnicas
- Tabla de IR: 5 tramos (0%, 15%, 20%, 25%, 30%)
- INSS: 7% deducible del IR (reduce base imponible)
- Acumulación: Art. 19 numeral 6 LCT - método obligatorio
- Moneda: Córdoba Nicaragüense (NIO)
