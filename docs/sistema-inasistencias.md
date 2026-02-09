# Sistema de Registro de Inasistencias

## Descripción General

El sistema de Coati Payroll incluye un módulo completo para el registro y procesamiento de inasistencias (ausencias) de los empleados. Este módulo permite configurar tres tipos diferentes de inasistencias según su impacto en el pago del trabajador.

## Tipos de Inasistencias

### 1. Inasistencias que NO se descuentan del pago

Estas son ausencias justificadas que no afectan el salario del empleado. Por ejemplo:
- Citas médicas justificadas
- Permisos especiales
- Días festivos trabajados compensados

**Configuración:**
- `es_inasistencia = True`
- `descontar_pago_inasistencia = False`

**Efecto:** El sistema registra la ausencia para fines de auditoría y control, pero NO deduce ningún monto del salario del empleado.

### 2. Inasistencias que SÍ se descuentan del pago

Estas son ausencias injustificadas o no autorizadas que resultan en una deducción proporcional del salario. Por ejemplo:
- Ausencias injustificadas
- Llegadas tardías no autorizadas
- Abandono de puesto

**Configuración:**
- `es_inasistencia = True`
- `descontar_pago_inasistencia = True`

**Efecto:** El sistema calcula el valor proporcional de la ausencia y lo deduce del salario base del empleado antes de calcular otras deducciones.

**Cálculo:**
```
Descuento por día = Salario Mensual / Días del Mes
Descuento por hora = (Salario Mensual / Días del Mes) / Horas por Día
```

### 3. Inasistencias pagadas en concepto distinto

Estas son ausencias que se descuentan del salario pero se compensan o pagan a través de otro concepto. Por ejemplo:
- Licencias especiales con compensación diferida
- Ausencias con pago diferenciado
- Permisos compensados con bonificaciones

**Configuración:**
- `es_inasistencia = True`
- `descontar_pago_inasistencia = True`
- Debe existir una deducción o percepción con el mismo `codigo_concepto`

**Efecto:** El sistema:
1. Deduce el valor de la ausencia del salario base
2. Previene la aplicación duplicada de la deducción del catálogo
3. Permite aplicar el concepto compensatorio por separado

## Estructura de Datos

### Modelo `NominaNovedad`

```python
class NominaNovedad:
    # Campos de identificación
    nomina_id: str                    # FK a Nomina
    empleado_id: str                  # FK a Empleado
    codigo_concepto: str              # Código del concepto
    
    # Valor de la novedad
    tipo_valor: str                   # 'dias' | 'horas' | 'cantidad' | 'monto' | 'porcentaje'
    valor_cantidad: Decimal           # Cantidad de unidades (ej: 2 días, 8 horas)
    fecha_novedad: date               # Fecha del evento
    
    # Flags para inasistencias
    es_inasistencia: bool             # Marca si es una ausencia
    descontar_pago_inasistencia: bool # Si se debe descontar del pago
```

### Modelo `EmpleadoCalculo`

El objeto `EmpleadoCalculo` rastrea información de ausencias durante el cálculo de nómina:

```python
class EmpleadoCalculo:
    # Tracking de inasistencias
    inasistencia_dias: Decimal                  # Total de días ausentes con descuento
    inasistencia_horas: Decimal                 # Total de horas ausentes con descuento
    inasistencia_descuento: Decimal             # Monto total descontado por ausencias
    salario_neto_inasistencia: Decimal          # Salario después de descuentos por ausencia
    inasistencia_codigos_descuento: set[str]    # Códigos de conceptos ya descontados
```

## Flujo de Procesamiento

### Paso 1: Carga de Novedades

El `NoveltyProcessor` carga las novedades del empleado para el período:

```python
novedades, ausencia_resumen, codigos_descuento = processor.load_novelties_with_absences(
    empleado, periodo_inicio, periodo_fin
)
```

**Retorna:**
- `novedades`: Diccionario con todos los conceptos y sus valores
- `ausencia_resumen`: Diccionario con `{'dias': Decimal, 'horas': Decimal}`
- `codigos_descuento`: Set de códigos que ya fueron descontados por ausencia

### Paso 2: Cálculo de Descuento por Ausencia

El `PayrollExecutionService` calcula el monto a descontar:

```python
descuento = (salario_diario * dias_ausencia) + (salario_hora * horas_ausencia)
```

Donde:
- `salario_diario = salario_mensual / dias_mes_nomina`
- `salario_hora = salario_diario / horas_jornada_diaria`

### Paso 3: Aplicación del Descuento

El descuento se aplica al salario base antes de calcular otras deducciones:

```python
salario_neto_inasistencia = salario_mensual - descuento_inasistencia
```

### Paso 4: Prevención de Doble Descuento

El `DeductionCalculator` verifica si el código de una deducción ya fue aplicado por ausencia:

```python
if deduccion.codigo in emp_calculo.inasistencia_codigos_descuento:
    continue  # Saltar esta deducción para evitar doble descuento
```

## Configuración del Sistema

### Parámetros Necesarios

En la tabla `configuracion` se deben configurar:

```python
configuracion = Configuracion(
    dias_mes_nomina=30,           # Días base para cálculo mensual
    horas_jornada_diaria=8,       # Horas de trabajo por día
)
```

### Creación de Novedades de Ausencia

#### Ejemplo 1: Ausencia Justificada (sin descuento)

```python
novedad = NominaNovedad(
    nomina_id=nomina.id,
    empleado_id=empleado.id,
    codigo_concepto="AUSENCIA_JUSTIFICADA",
    valor_cantidad=Decimal("1.00"),
    tipo_valor="dias",
    fecha_novedad=date(2025, 1, 15),
    es_inasistencia=True,
    descontar_pago_inasistencia=False,  # NO descontar
)
```

#### Ejemplo 2: Ausencia Injustificada (con descuento)

```python
novedad = NominaNovedad(
    nomina_id=nomina.id,
    empleado_id=empleado.id,
    codigo_concepto="AUSENCIA_INJUSTIFICADA",
    valor_cantidad=Decimal("2.00"),
    tipo_valor="dias",
    fecha_novedad=date(2025, 1, 20),
    es_inasistencia=True,
    descontar_pago_inasistencia=True,  # SÍ descontar
)
```

#### Ejemplo 3: Ausencia con Compensación

```python
# 1. Crear la novedad de ausencia
novedad = NominaNovedad(
    nomina_id=nomina.id,
    empleado_id=empleado.id,
    codigo_concepto="LICENCIA_ESPECIAL",  # Mismo código que la deducción
    valor_cantidad=Decimal("1.00"),
    tipo_valor="dias",
    fecha_novedad=date(2025, 1, 25),
    es_inasistencia=True,
    descontar_pago_inasistencia=True,
)

# 2. Asegurar que existe una deducción con el mismo código
# Esta deducción NO se aplicará automáticamente debido al mecanismo
# de prevención de doble descuento
```

## Consultas y Reportes

### Obtener Total de Ausencias por Empleado

```sql
SELECT 
    e.codigo_empleado,
    e.primer_nombre,
    e.primer_apellido,
    COUNT(*) as total_ausencias,
    SUM(CASE WHEN nn.descontar_pago_inasistencia THEN nn.valor_cantidad ELSE 0 END) as dias_descontados,
    SUM(CASE WHEN NOT nn.descontar_pago_inasistencia THEN nn.valor_cantidad ELSE 0 END) as dias_justificados
FROM nomina_novedad nn
INNER JOIN empleado e ON nn.empleado_id = e.id
WHERE nn.es_inasistencia = TRUE
  AND nn.tipo_valor = 'dias'
  AND nn.fecha_novedad BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY e.codigo_empleado, e.primer_nombre, e.primer_apellido
ORDER BY total_ausencias DESC;
```

### Obtener Montos Descontados por Ausencia

```sql
SELECT 
    n.numero_nomina,
    e.codigo_empleado,
    en.inasistencia_dias,
    en.inasistencia_horas,
    en.inasistencia_descuento,
    en.salario_neto
FROM empleado_nomina en
INNER JOIN nomina n ON en.nomina_id = n.id
INNER JOIN empleado e ON en.empleado_id = e.id
WHERE en.inasistencia_descuento > 0
ORDER BY n.numero_nomina, e.codigo_empleado;
```

## Validaciones y Reglas de Negocio

### Validaciones Automáticas

1. **Configuración requerida:** El sistema valida que existan los parámetros `dias_mes_nomina` y `horas_jornada_diaria`
2. **Valores positivos:** Las ausencias deben tener valores positivos
3. **Tipo de valor válido:** El campo `tipo_valor` debe ser 'dias' o 'horas' para que se calcule el descuento
4. **Prevención de doble descuento:** El sistema automáticamente previene la aplicación duplicada de deducciones

### Mejores Prácticas

1. **Nomenclatura consistente:** Usar códigos descriptivos para los conceptos de ausencia
2. **Documentación:** Mantener en la descripción el tipo y efecto de cada ausencia
3. **Auditoría:** Registrar siempre la fecha del evento de ausencia
4. **Revisión periódica:** Verificar que los descuentos calculados son correctos

## Pruebas

El sistema incluye pruebas exhaustivas en `tests/test_engines/test_absence_deduction_avoidance.py`:

```bash
# Ejecutar pruebas de ausencias
pytest tests/test_engines/test_absence_deduction_avoidance.py -v

# Ejecutar todas las pruebas
pytest -x -q
```

## Soporte y Referencias

- **Código fuente:**
  - `coati_payroll/nomina_engine/processors/novelty_processor.py`
  - `coati_payroll/nomina_engine/calculators/deduction_calculator.py`
  - `coati_payroll/nomina_engine/services/payroll_execution_service.py`
  - `coati_payroll/nomina_engine/domain/employee_calculation.py`
  
- **Modelo de datos:** `coati_payroll/model.py` (clase `NominaNovedad`)

- **Tests:** `tests/test_engines/test_absence_deduction_avoidance.py`

## Historial de Cambios

- **2025-02-09:** Implementación inicial del sistema de registro de inasistencias con soporte para tres tipos de ausencias y prevención de doble descuento.
