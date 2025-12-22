# Proyecto: Sistema de Nómina Coati (Nicaragua)

## Estado Actual
Validación de IR implementada exitosamente - **COMPLETADO**

## Validación del Cálculo de IR

### Requisito ✅
Sistema calcula correctamente **IR anual de C$ 34,799.00** para trabajador con:
- Salario ordinario anual: C$ 300,000
- Ingresos ocasionales: C$ 17,000
- Total bruto anual: C$ 321,500
- Método: Acumulado (Art. 19 numeral 6 LCT)

## Tests Implementados

### Tests de Validación de IR - ✅ 41 TESTS PASANDO
- `tests/test_validation/test_nicaragua_ir_calculation.py` - 41 tests validando cálculo exacto de IR
- Alcanzado: IR exacto C$ 34,799.00 sin tolerancia

### Tests End-to-End de Vacaciones - 9/11 TESTS PASANDO
- Nuevo: `tests/test_vistas/test_vacation_e2e.py` - Tests basados en patrón test_prestamo_e2e.py
- Cubre: Políticas, cuentas, solicitudes de vacaciones
- Status: 9 tests pasando, 2 con problemas de fixture DB (no de lógica)

### Tests de Acumulación de Prestaciones - ✅ ACTUALIZADO
- `tests/test_validation/test_prestaciones_accumulation.py`
- Corregido: Método de cálculo para meses calendario completos (sin prorrateo)
- Resultado esperado: C$ 1,249.50 por mes (15000 × 8.33%)

## Archivos Principales

### Motores de Cálculo
- `coati_payroll/nomina_engine.py` - Motor de nómina con cálculos exactos
- `coati_payroll/formula_engine.py` - Motor de evaluación de fórmulas
- `coati_payroll/vacation_service.py` - Servicio de gestión de vacaciones

### Vistas (Frontend)
- `coati_payroll/vistas/vacation.py` - Gestión de políticas, cuentas y solicitudes de vacaciones (1035 líneas)

### Guías de Implementación
- `docs/local_guides/nicaragua-ir-paso-a-paso.md` - Guía paso a paso
- `docs/local_guides/nicaragua-implementacion-tecnica.md` - Detalles técnicos

## Diseño de Períodos de Pago

### Regla Crítica: Calendarios vs Prorratos
```
Meses calendario completos (1er día a último día):
- NO se prorratean
- Usan salario base completo
- Ejemplo: 1-31 enero = salario_base × porcentaje

Períodos parciales:
- SÍ se prorratean
- Divisor: 30 días estándar (TipoPlanilla.dias)
- Ejemplo: 15 días = (salario_base / 30) × 15 × porcentaje
```

## Configuración Clave del Sistema

### INSS (Deducción)
- Formula: `formula_tipo="porcentaje_bruto"`
- Tasa: 7% del salario bruto
- Base: Incluye percepciones (no solo salario base)

### Prestaciones (Aguinaldo, Indemnización)
- Formula: `formula_tipo="porcentaje_salario"`
- Acumulación: Anual o de por vida
- Cálculo: Sin prorrateo en meses calendario completos

## Próximos Pasos
1. ✅ Implementación de IR - COMPLETADO
2. ✅ Tests de IR - COMPLETADO
3. ✅ Tests de vacaciones - EN PROGRESO (9/11 pasando)
4. ⏳ Corregir tests de vacaciones (2 tests) - Bajo fixture DB, no de lógica
5. ⏳ Documentar API de servicios

## Notas Técnicas
- Tabla de IR: 5 tramos progresivos (0%, 15%, 20%, 25%, 30%)
- INSS: 7% deducible como porcentaje del bruto
- Período fiscal: Enero a diciembre
- Moneda: Córdoba Nicaragüense (NIO)
- País: Nicaragua (ISO 3166-1 alpha-2: NI)
