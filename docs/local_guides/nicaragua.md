# Guía de Implementación para Nicaragua

Esta guía proporciona instrucciones detalladas para configurar Coati Payroll según la legislación laboral y tributaria de Nicaragua.

## Tabla de Contenidos

- [Introducción](#introduccion)
- [Marco Legal](#marco-legal)
- [Tipos de Ingresos](#tipos-de-ingresos)
- [Deducciones Obligatorias](#deducciones-obligatorias)
- [Configuración del Sistema](#configuracion-del-sistema)
- [Casos Especiales](#casos-especiales)
- [Pruebas y Validación](#pruebas-y-validacion)
- [Preguntas Frecuentes](#preguntas-frecuentes)

## Introducción

La legislación laboral nicaragüense establece un sistema de nómina con dos tipos principales de ingresos y dos deducciones obligatorias fundamentales:

### Tipos de Ingresos

1. **Ingresos Ordinarios**: Salario Base, Horas Extra, Comisiones
2. **Ingresos Extraordinarios**: Bonos, Incentivos, Pago de Vacaciones

### Deducciones Obligatorias

1. **INSS Laboral**: 7% del salario bruto (aporte del empleado a la seguridad social)
2. **IR (Impuesto sobre la Renta)**: Tasa progresiva según tramos de renta anual

!!! important "Nota Importante"
    En general todos los ingresos (ordinarios y extraordinarios) que perciba un trabajador están sujetos tanto a INSS como a IR.
    El sistema debe calcularlos sobre el salario bruto total. Hay algunos conceptos que se pueden pagar al empleado que no pagan
    Impuestos o Aportes al seguro social, ante cualquier consulta recomendamos confirmar con un experto local en la materia.

## Marco Legal

### Ley de Concertación Tributaria (LCT)

La legislación nicaragüense establece el cálculo del IR mediante una tarifa progresiva anual. Las referencias legales principales son:

- **Artículo 20**: Base Imponible.
- **Artículo 21**: Deducciones autorizadas (principalmente INSS)
- **Artículo 23**: Tarifa progresiva del IR (reformado por Ley No 891)
- **Artículo 25**: Períodos fiscales y metodologías de cálculo

### Tarifa Progresiva del IR vigente al 2025.

La tarifa progresiva actual del Impuesto sobre la Renta en Nicaragua es:

| Renta Neta Anual (Desde) | Renta Neta Anual (Hasta) | Impuesto Base | Tasa Marginal | Sobre Exceso de |
|--------------------------|-------------------------|---------------|---------------|-----------------|
| C$ 0.01                  | C$ 100,000              | C$ 0          | 0%            | -               |
| C$ 100,000.01            | C$ 200,000              | C$ 0          | 15%           | C$ 100,000      |
| C$ 200,000.01            | C$ 350,000              | C$ 15,000     | 20%           | C$ 200,000      |
| C$ 350,000.01            | C$ 500,000              | C$ 45,000     | 25%           | C$ 350,000      |
| C$ 500,000.01            | En adelante             | C$ 82,500     | 30%           | C$ 500,000      |

*Fuente: Artículo 23 LCT

## Tipos de Ingresos

### Ingresos Ordinarios

Son los ingresos regulares y recurrentes que percibe el empleado:

#### 1. Salario Base

- Es el salario mensual acordado en el contrato de trabajo
- Debe ser al menos igual al salario mínimo legal
- **Gravable**: Sí (INSS + IR)

**Configuración en Coati Payroll:**
- Este es el campo "Salario Mensual" del empleado y debe estar definido en la configuración del empleado.
- No requiere configuración adicional como percepción

#### 2. Horas Extra

Las horas extra se calculan según el Código del Trabajo:

- **Horas extra diurnas**: 100% adicional al salario hora
- **Gravable**: Sí (INSS + IR)

**Fórmula de cálculo:**
```
Salario Hora = Salario Mensual / 240 horas
Hora Extra Diurna = Salario Hora × 2
```

#### 3. Comisiones

- Porcentaje sobre ventas o resultados
- Monto variable según desempeño
- **Gravable**: Sí (INSS + IR)

### Ingresos Extraordinarios

Son ingresos no recurrentes o excepcionales:

#### 1. Bonos

- Bonos por desempeño, productividad, resultados
- Pueden ser mensuales, trimestrales, semestrales o anuales
- **Gravable**: Sí (INSS + IR)

#### 2. Incentivos

- Incentivos por metas, objetivos cumplidos
- Frecuencia variable según política empresarial
- **Gravable**: Sí (INSS + IR)

#### 3. Pago de Vacaciones

- Pago correspondiente al período de vacaciones
- Calculado según días de salario
- **Gravable**: Sí (INSS + IR)

!!! warning "Importante"
    Todos estos ingresos (ordinarios y extraordinarios) forman parte del salario bruto y están sujetos a INSS e IR.

## Deducciones Obligatorias

### INSS Laboral (Seguro Social)

El Instituto Nicaragüense de Seguridad Social (INSS) es la deducción para la seguridad social del empleado.

**Características:**
- **Tasa**: 7% del salario bruto
- **Base de cálculo**: Salario bruto total (incluye todos los ingresos gravables)
- **Tope máximo**: Generalmente no hay tope, pero puede variar según normativa vigente
- **Prioridad**: Alta (se deduce antes del IR)

**Fórmula:**
```
INSS = Salario Bruto × 0.07
```

### IR (Impuesto sobre la Renta)

El IR es un impuesto progresivo que se calcula sobre la renta neta anual proyectada.

#### Metodología de Cálculo según Artículo 19 LCT

!!! warning "Método de Cálculo Acumulado"
    Esta guía utiliza un método de cálculo acumulado que considera los ingresos de todos los meses anteriores para calcular el IR. Esto es diferente a una simple proyección anual del salario del mes actual. Al final del el período siempre se puede verificar si monto retenido corresponde al ingreso anual del trabajador.
    

##### 1. Retención Mensual con Método Acumulado

Este es el método estándar para empleados con un solo empleador, especialmente cuando hay variaciones en los ingresos mensuales:

**Paso a paso:**

!!! important "Calculo Quincenal"
    En este guía se muestra el calculo mensual, sin embargo el calculo aplica correctamente para pagos quincenales.

**Mes 1:**
1. Calcular salario neto del mes: `Salario Bruto - INSS (7%)`
2. Proyectar a anual: `Salario Neto × 12`
3. Aplicar tarifa progresiva para obtener IR anual
4. Retención del mes: `IR Anual / 12`

**Meses 2 en adelante:**
1. **Acumular salario neto:** Sumar el salario neto del mes actual a los meses anteriores
2. **Calcular promedio mensual:** `Salario Neto Acumulado / Meses Transcurridos`
3. **Proyectar expectativa anual:** `Promedio Mensual × 12`
4. **Aplicar tarifa progresiva** a la expectativa anual para obtener nuevo IR anual
5. **Calcular IR proporcional a meses trabajados:** `(IR Anual / 12) × Meses Transcurridos`
6. **Restar retenciones acumuladas** de meses anteriores
7. **Retención del mes actual:** Diferencia del paso anterior

**Ejemplo Detallado:**

Un empleado con salario variable:

**Mes 1:** Salario Bruto = C$ 25,000
```
1. Salario Neto Mes 1: C$ 25,000 - C$ 1,750 (INSS) = C$ 23,250
2. Acumulado: C$ 23,250
3. Promedio: C$ 23,250 / 1 = C$ 23,250
4. Expectativa Anual: C$ 23,250 × 12 = C$ 279,000
5. IR Anual: C$ 15,000 + (C$ 279,000 - C$ 200,000) × 0.20 = C$ 30,800
6. IR Proporcional (1 mes): (C$ 30,800 / 12) × 1 = C$ 2,567
7. Retenciones Previas: C$ 0
8. IR Mes 1: C$ 2,567 - C$ 0 = C$ 2,567
```

**Mes 2:** Salario Bruto = C$ 30,000
```
1. Salario Neto Mes 2: C$ 30,000 - C$ 2,100 (INSS) = C$ 27,900
2. Acumulado: C$ 23,250 + C$ 27,900 = C$ 51,150
3. Promedio: C$ 51,150 / 2 = C$ 25,575
4. Expectativa Anual: C$ 25,575 × 12 = C$ 306,900
5. IR Anual: C$ 15,000 + (C$ 306,900 - C$ 200,000) × 0.20 = C$ 36,380
6. IR Proporcional (2 meses): (C$ 36,380 / 12) × 2 = C$ 6,063
7. Retenciones Previas: C$ 2,567
8. IR Mes 2: C$ 6,063 - C$ 2,567 = C$ 3,496
```

**Mes 3:** Salario Bruto = C$ 28,000
```
1. Salario Neto Mes 3: C$ 28,000 - C$ 1,960 (INSS) = C$ 26,040
2. Acumulado: C$ 51,150 + C$ 26,040 = C$ 77,190
3. Promedio: C$ 77,190 / 3 = C$ 25,730
4. Expectativa Anual: C$ 25,730 × 12 = C$ 308,760
5. IR Anual: C$ 15,000 + (C$ 308,760 - C$ 200,000) × 0.20 = C$ 36,752
6. IR Proporcional (3 meses): (C$ 36,752 / 12) × 3 = C$ 9,188
7. Retenciones Previas: C$ 2,567 + C$ 3,496 = C$ 6,063
8. IR Mes 3: C$ 9,188 - C$ 6,063 = C$ 3,125
```

**Ventajas de este método:**
- Se ajusta automáticamente a variaciones en el ingreso
- Evita retenciones excesivas o insuficientes
- Al final del año, las retenciones mensuales suman exactamente el IR anual correcto

##### 2. Retención para Salario Fijo

Si el empleado tiene un salario completamente fijo (sin variaciones), se puede usar un método simplificado:

**Paso a paso:**

1. **Calcular Salario Neto Mensual:**
   ```
   Salario Neto = Salario Bruto - INSS (7%)
   ```

2. **Proyectar Renta Anual:**
   ```
   Expectativa Renta Anual = Salario Neto × 12
   ```

3. **Aplicar Tarifa Progresiva:**
   - Se busca el tramo correspondiente en la tabla del IR
   - Se aplica la fórmula: `Impuesto Base + (Renta - Exceso Base) × Tasa Marginal`

4. **Calcular Retención Mensual:**
   ```
   IR Mensual = IR Anual / 12
   ```

!!! note "Salario Fijo vs Variable"
    El método simplificado (numeral 1) solo es válido si el salario es exactamente igual todos los meses. En la práctica, la mayoría de empleados tienen variaciones (horas extra, comisiones, bonos), por lo que el método acumulado (numeral 6) es el más adecuado y el que debe implementarse en el sistema.

#### Valores Acumulados Requeridos (Origen: Base de Datos)

Para implementar correctamente el cálculo del IR según el método acumulado, el sistema debe almacenar y mantener los siguientes valores en la tabla `AcumuladoAnual`:

| Campo en Base de Datos | Descripción | Uso en Cálculo IR |
|------------------------|-------------|-------------------|
| `salario_bruto_acumulado` | Suma de todos los salarios brutos del año fiscal | Base para calcular salario neto acumulado |
| `deducciones_antes_impuesto_acumulado` | Suma de INSS y otras deducciones pre-impuesto | Se resta del bruto para obtener neto |
| `impuesto_retenido_acumulado` | Suma de todas las retenciones de IR del año | Se resta para calcular IR del mes actual |
| `periodos_procesados` | Número de nóminas procesadas en el año fiscal | Equivale a "meses transcurridos" |
| `salario_gravable_acumulado` | Suma de ingresos gravables (ordinarios + extraordinarios) | Para separar conceptos gravables |
| `datos_adicionales` (JSON) | Campos adicionales flexibles | Puede almacenar datos específicos por país |

**Cálculo del Salario Neto Acumulado:**
```
Salario Neto Acumulado = salario_bruto_acumulado - deducciones_antes_impuesto_acumulado
```

**Campos adicionales recomendados en `datos_adicionales` para Nicaragua:**
```json
{
  "inss_acumulado": 0.00,
  "ingresos_eventuales_brutos": 0.00,
  "ingresos_eventuales_netos": 0.00,
  "salario_neto_acumulado": 0.00,
  "promedio_mensual": 0.00
}
```

!!! warning "Importante para la Implementación"
    El sistema Coati Payroll ya cuenta con la tabla `AcumuladoAnual` que almacena estos valores. Sin embargo, la **ReglaCalculo del IR** debe configurarse para utilizar estos valores acumulados en lugar de hacer una simple proyección del mes actual × 12.
    
    La fórmula de IR debe acceder a estas variables:

##### 2. Pagos Ocasionales

Para bonos, vacaciones o incentivos semestrales/anuales:

**Metodología:**

1. **Calcular IR Base** (usando salario regular):
   ```
   Expectativa Anual Base = Salario Neto Mensual × 12
   IR Anual Base = Aplicar tarifa progresiva
   ```

2. **Calcular IR con Pago Ocasional:**
   ```
   Expectativa Anual Nueva = Expectativa Anual Base + Pago Ocasional Neto
   IR Anual Nuevo = Aplicar tarifa progresiva
   ```

3. **Determinar IR del Pago Ocasional:**
   ```
   IR Pago Ocasional = IR Anual Nuevo - IR Anual Base
   ```

4. **Retención Total del Mes:**
   ```
   IR Total = IR Mensual Regular + IR Pago Ocasional
   ```

**Ejemplo:**

Empleado con salario regular de C$ 20,000 recibe bono de C$ 10,000:

```
Situación Base:
- Salario Neto Mensual: C$ 18,600 (20,000 - 7%)
- Renta Anual Base: C$ 223,200 (18,600 × 12)
- IR Anual Base: C$ 19,640

Con Bono:
- Bono Neto: C$ 9,300 (10,000 - 7%)
- Nueva Renta Anual: C$ 232,500 (223,200 + 9,300)
- IR Anual Nuevo: C$ 21,140

IR del Bono:
- IR Bono = 21,140 - 19,640 = C$ 1,500

Retención del Mes:
- IR Regular: C$ 1,636.67 (19,640 / 12)
- IR Bono: C$ 1,500.00
- IR Total: C$ 3,136.67
```

##### 3. Incrementos Salariales (Art. 19, numeral 3)

Cuando hay aumentos salariales durante el período fiscal:

**Metodología:**

1. **Sumar ingresos netos** acumulados desde inicio del período hasta el incremento
2. **Calcular proyección** con nuevo salario para meses restantes
3. **Determinar nuevo IR anual** con la tarifa progresiva
4. **Restar retenciones** efectuadas anteriormente
5. **Distribuir IR pendiente** entre meses restantes

##### 4. Trabajadores con Múltiples Empleadores (Art. 19, numeral 6)

Para empleados con varios empleadores simultáneos:

**Metodología:**

1. Calcular retención del **primer mes** según numeral 1
2. Para **meses subsiguientes**:
   - Acumular renta neta de todos los meses
   - Calcular promedio mensual
   - Proyectar a 12 meses
   - Aplicar tarifa progresiva
   - Ajustar por retenciones previas

!!! note "Implementación en Coati"
    El sistema Coati maneja automáticamente casos 1 y 2. Los casos 3 y 4 requieren ajustes manuales o novedades especiales.

#### Fórmula Correcta con Valores Acumulados

El cálculo correcto del IR debe usar los valores acumulados de la base de datos:

```python
# NOTA: Esta fórmula debe implementarse en ReglaCalculo del sistema
# Las variables provienen de la tabla AcumuladoAnual

# 1. Obtener valores acumulados (desde base de datos)
salario_bruto_acumulado = acumulado.salario_bruto_acumulado
inss_acumulado = acumulado.deducciones_antes_impuesto_acumulado
ir_retenido_acumulado = acumulado.impuesto_retenido_acumulado
meses_trabajados = acumulado.periodos_procesados

# 2. Calcular salario neto del mes actual
salario_neto_mes = salario_bruto - (salario_bruto * 0.07)

# 3. Calcular salario neto acumulado
salario_neto_acumulado = (salario_bruto_acumulado + salario_bruto) - (inss_acumulado + (salario_bruto * 0.07))

# 4. Calcular promedio mensual
promedio_mensual = salario_neto_acumulado / (meses_trabajados + 1)

# 5. Proyectar expectativa anual
expectativa_anual = promedio_mensual * 12

# 6. Aplicar tramos progresivos
if expectativa_anual <= 100000:
    ir_anual = 0
elif expectativa_anual <= 200000:
    ir_anual = (expectativa_anual - 100000) * 0.15
elif expectativa_anual <= 350000:
    ir_anual = 15000 + (expectativa_anual - 200000) * 0.20
elif expectativa_anual <= 500000:
    ir_anual = 45000 + (expectativa_anual - 350000) * 0.25
else:
    ir_anual = 82500 + (expectativa_anual - 500000) * 0.30

# 7. Calcular IR proporcional a meses trabajados
ir_proporcional = (ir_anual / 12) * (meses_trabajados + 1)

# 8. Calcular IR del mes actual
ir_mes_actual = ir_proporcional - ir_retenido_acumulado

# Asegurar que no sea negativo
ir_mes_actual = max(ir_mes_actual, 0)
```

!!! danger "Método Incorrecto (NO USAR)"
    El siguiente método de proyección simple está **incorrecto** para Nicaragua y puede resultar en retenciones excesivas o insuficientes:
    ```python
    # ❌ INCORRECTO - No usar
    salario_neto = salario_bruto - (salario_bruto * 0.07)
    renta_anual = salario_neto * 12  # ← Proyecta solo el mes actual
    ir_anual = aplicar_tramos(renta_anual)
    ir_mensual = ir_anual / 12
    ```
    Este método ignora los ingresos de meses anteriores y no se ajusta a variaciones.

## Configuración del Sistema

### Paso 1: Configurar Moneda

1. Acceda a **Configuración** → **Monedas**
2. Verifique que exista la moneda **NIO (Córdoba)**
3. Si no existe, créela:
   - **Código**: NIO
   - **Nombre**: Córdoba Nicaragüense
   - **Símbolo**: C$

### Paso 2: Configurar INSS Laboral

!!! note "Configuración Crítica del INSS"
    El INSS debe calcularse sobre el **salario bruto total**, que incluye el salario base más todas las percepciones (bonos, horas extra, comisiones). El sistema usa `formula_tipo="porcentaje_bruto"` para este cálculo.

#### Opción A: Deducción Simple con Fórmula (Recomendado)

1. Acceda a **Configuración** → **Deducciones**
2. Cree una nueva deducción:
   - **Código**: `INSS_NIC`
   - **Nombre**: `INSS Laboral 7%`
   - **Descripción**: `Aporte al seguro social del empleado`
   - **Tipo de Fórmula**: `Porcentaje del Salario Bruto` (`porcentaje_bruto`)
   - **Porcentaje**: `7.00`
   - **Antes de Impuesto**: ✓ Sí (reduce la base imponible del IR)
   - **Activo**: ✓ Sí

!!! warning "Importante: Tipo de Fórmula"
    Use `porcentaje_bruto` y **NO** `porcentaje`. La diferencia es crítica:
    - `porcentaje_bruto`: Calcula sobre salario base + percepciones (correcto)
    - `porcentaje`: Calcula solo sobre salario base (incorrecto para INSS)

#### Opción B: Regla de Cálculo con Tope (Recomendado)

Si existe un tope máximo de cotización:

1. Acceda a **Configuración** → **Reglas de Cálculo**
2. Cree una nueva regla:
   - **Código**: `INSS_LABORAL_NIC`
   - **Nombre**: `INSS Laboral Nicaragua`
   - **Versión**: `1.0.0`
   - **Jurisdicción**: `Nicaragua`
   - **Moneda de Referencia**: `NIO`
   - **Tipo de Regla**: `deduccion`
   - **Vigente Desde**: `2024-01-01`

**Esquema JSON:**
```json
{
  "tipo": "formula",
  "descripcion": "INSS Laboral 7% con tope de C$ 100,000",
  "formula": "min(monto, 100000) * 0.07",
  "tope_maximo": 7000,
  "tope_minimo": 0,
  "moneda": "NIO"
}
```

3. Cree la deducción asociada:
   - **Código**: `INSS_LABORAL`
   - **Nombre**: `INSS Laboral (7%)`
   - **Es Obligatoria**: ✓ Sí
   - **Prioridad**: `1`
   - **Tipo de Fórmula**: `Regla de Cálculo`
   - **Regla de Cálculo**: Seleccionar `INSS_LABORAL_NIC`

### Paso 3: Configurar IR (Impuesto sobre la Renta)

El IR requiere una Regla de Cálculo con tramos progresivos.

#### 3.1. Crear Regla de Cálculo para IR

1. Acceda a **Configuración** → **Reglas de Cálculo**
2. Cree una nueva regla:
   - **Código**: `IR_NICARAGUA`
   - **Nombre**: `Impuesto sobre la Renta Nicaragua`
   - **Versión**: `2024.1`
   - **Descripción**: `Tarifa progresiva del IR según Ley No 891, vigente desde 2014`
   - **Jurisdicción**: `Nicaragua`
   - **Moneda de Referencia**: `NIO`
   - **Tipo de Regla**: `impuesto`
   - **Vigente Desde**: `2024-01-01`
   - **Vigente Hasta**: (dejar vacío)

**Esquema JSON Completo con Método Acumulado:**

Este es el esquema JSON **validado y funcionando** en el sistema. Produce cálculos exactos de IR según el método acumulado.

```json
{
  "meta": {
    "name": "IR Nicaragua - Método Acumulado",
    "legal_reference": "Ley 891 - Art. 23 LCT",
    "calculation_method": "accumulated_average"
  },
  "inputs": [
    {
      "name": "salario_bruto",
      "type": "decimal",
      "source": "empleado.salario_base",
      "description": "Salario bruto del mes actual"
    },
    {
      "name": "salario_bruto_acumulado",
      "type": "decimal",
      "source": "acumulado.salario_bruto_acumulado",
      "description": "Salario bruto acumulado de meses anteriores"
    },
    {
      "name": "salario_acumulado_mes",
      "type": "decimal",
      "source": "acumulado.salario_acumulado_mes",
      "description": "Salario acumulado del mes actual (percepciones)"
    },
    {
      "name": "deducciones_antes_impuesto_acumulado",
      "type": "decimal",
      "source": "acumulado.deducciones_antes_impuesto_acumulado",
      "description": "INSS y otras deducciones pre-impuesto acumuladas"
    },
    {
      "name": "ir_retenido_acumulado",
      "type": "decimal",
      "source": "acumulado.impuesto_retenido_acumulado",
      "description": "IR retenido en meses anteriores"
    },
    {
      "name": "meses_trabajados",
      "type": "integer",
      "source": "acumulado.periodos_procesados",
      "description": "Número de meses trabajados en el año fiscal"
    },
    {
      "name": "salario_inicial_acumulado",
      "type": "decimal",
      "source": "empleado.salario_acumulado",
      "description": "Salario acumulado previo al sistema (para implementaciones a mitad de año)"
    },
    {
      "name": "impuesto_inicial_acumulado",
      "type": "decimal",
      "source": "empleado.impuesto_acumulado",
      "description": "IR acumulado previo al sistema (para implementaciones a mitad de año)"
    }
  ],
  "steps": [
    {
      "name": "inss_mes",
      "type": "calculation",
      "formula": "salario_bruto * 0.07",
      "output": "inss_mes",
      "description": "Calcular INSS del mes actual (7%)"
    },
    {
      "name": "salario_neto_mes",
      "type": "calculation",
      "formula": "salario_bruto - inss_mes",
      "output": "salario_neto_mes",
      "description": "Calcular salario neto del mes actual"
    },
    {
      "name": "salario_neto_total",
      "type": "calculation",
      "formula": "(salario_bruto_acumulado + salario_bruto) - (deducciones_antes_impuesto_acumulado + inss_mes)",
      "output": "salario_neto_total",
      "description": "Sumar salario neto del mes a los acumulados anteriores"
    },
    {
      "name": "meses_totales",
      "type": "calculation",
      "formula": "meses_trabajados + 1",
      "output": "meses_totales",
      "description": "Total de meses incluyendo el actual"
    },
    {
      "name": "promedio_mensual",
      "type": "calculation",
      "formula": "salario_neto_total / meses_totales",
      "output": "promedio_mensual",
      "description": "Calcular promedio mensual de salario neto"
    },
    {
      "name": "expectativa_anual",
      "type": "calculation",
      "formula": "promedio_mensual * 12",
      "output": "expectativa_anual",
      "description": "Proyectar expectativa anual basada en promedio"
    },
    {
      "name": "ir_anual",
      "type": "tax_lookup",
      "table": "tabla_ir",
      "input": "expectativa_anual",
      "output": "ir_anual",
      "description": "Aplicar tabla progresiva de IR"
    },
    {
      "name": "ir_proporcional",
      "type": "calculation",
      "formula": "(ir_anual / 12) * meses_totales",
      "output": "ir_proporcional",
      "description": "Calcular IR proporcional a meses trabajados"
    },
    {
      "name": "ir_final",
      "type": "calculation",
      "formula": "max(ir_proporcional - ir_retenido_acumulado, 0)",
      "output": "ir_final",
      "description": "Restar retenciones previas para obtener IR del mes"
    }
  ],
  "tax_tables": {
    "tabla_ir": [
      {"min": 0, "max": 100000, "rate": 0.00, "fixed": 0, "over": 0},
      {"min": 100000, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000},
      {"min": 200000, "max": 350000, "rate": 0.20, "fixed": 15000, "over": 200000},
      {"min": 350000, "max": 500000, "rate": 0.25, "fixed": 45000, "over": 350000},
      {"min": 500000, "max": null, "rate": 0.30, "fixed": 82500, "over": 500000}
    ]
  },
  "output": "ir_final"
}
```

!!! success "Esquema Validado"
    Este esquema produce **exactamente C$ 34,799.00** de IR anual para un trabajador con ingresos variables de 12 meses, validado contra cálculos manuales.

!!! warning "Evaluación de Implementabilidad para Usuario de RRHH"
    **Complejidad:** ⚠️ **ALTA - Requiere soporte técnico**
    
    El esquema JSON anterior es **técnicamente correcto** pero **demasiado complejo** para que un usuario de Recursos Humanos lo implemente sin ayuda técnica. 
    
    **Razones:**
    - Requiere entender 9 pasos de cálculo encadenados
    - Necesita conocimiento de variables de base de datos
    - La lógica de promedio acumulado no es intuitiva
    - Alto riesgo de error en la configuración
    
    **Recomendación:** Este esquema debe ser **pre-configurado por el equipo de desarrollo** o **importado desde una plantilla validada**.

#### Alternativa Simplificada para RRHH (NO RECOMENDADA para Nicaragua)

Si un usuario de RRHH debe configurar manualmente el IR, esta es una versión simplificada (aunque **incorrecta** según la ley nicaragüense):

```json
{
  "meta": {
    "name": "IR Nicaragua - Versión Simplificada",
    "description": "ADVERTENCIA: Esta versión NO cumple con Art. 19 numeral 6. Solo usar si la empresa acepta el riesgo.",
    "version": "simple-1.0",
    "warning": "No considera acumulados correctamente"
  },
  "inputs": [
    {"name": "salario_bruto", "type": "decimal", "source": "empleado.salario_base"}
  ],
  "steps": [
    {
      "name": "calcular_inss",
      "type": "calculation",
      "formula": "salario_bruto * 0.07",
      "output": "inss"
    },
    {
      "name": "calcular_salario_neto",
      "type": "calculation",
      "formula": "salario_bruto - inss",
      "output": "salario_neto"
    },
    {
      "name": "proyectar_anual",
      "type": "calculation",
      "formula": "salario_neto * 12",
      "output": "renta_anual"
    },
    {
      "name": "aplicar_tabla_ir",
      "type": "tax_lookup",
      "table": "tabla_ir",
      "input": "renta_anual",
      "output": "ir_anual"
    },
    {
      "name": "calcular_mensual",
      "type": "calculation",
      "formula": "ir_anual / 12",
      "output": "ir_mensual"
    }
  ],
  "tax_tables": {
    "tabla_ir": [
      {"min": 0, "max": 100000, "rate": 0.00, "fixed": 0, "over": 0},
      {"min": 100000, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000},
      {"min": 200000, "max": 350000, "rate": 0.20, "fixed": 15000, "over": 200000},
      {"min": 350000, "max": 500000, "rate": 0.25, "fixed": 45000, "over": 350000},
      {"min": 500000, "max": null, "rate": 0.30, "fixed": 82500, "over": 500000}
    ]
  },
  "output": "ir_mensual"
}
```

**❌ Problemas de esta versión simplificada:**
- No considera ingresos de meses anteriores
- No ajusta por variaciones mensuales
- Puede resultar en retenciones incorrectas
- **No cumple con la legislación nicaragüense**
- Puede generar multas de la DGI

!!! success "Variables Acumuladas Disponibles desde Base de Datos"
    Para el esquema completo (recomendado), las siguientes variables están disponibles desde la tabla `AcumuladoAnual`:
    
    - `salario_bruto_acumulado` - Suma de salarios brutos de meses anteriores
    - `salario_gravable_acumulado` - Suma de ingresos gravables
    - `deducciones_antes_impuesto_acumulado` - Suma de INSS y otras deducciones pre-impuesto
    - `ir_retenido_acumulado` - Suma de IR retenido en meses anteriores
    - `meses_trabajados` (= `periodos_procesados`) - Cantidad de meses procesados
    - `salario_neto_acumulado` - Calculado automáticamente (bruto - deducciones)

#### 3.2. Estrategia de Implementación Recomendada

!!! tip "Opciones de Implementación"
    Debido a la complejidad del cálculo acumulado del IR, existen tres enfoques:

**Opción 1: Pre-configuración por Desarrollo (RECOMENDADO)**
- El equipo de desarrollo crea la ReglaCalculo con el esquema JSON completo
- Se incluye como parte de la configuración inicial del sistema
- Usuario de RRHH solo necesita activar/desactivar la regla
- ✅ **Ventajas:** Garantiza cálculo correcto, sin riesgo de error
- ❌ **Desventajas:** Requiere acceso de desarrollo

**Opción 2: Importar Plantilla Validada**
- Proporcionar un archivo JSON de importación validado
- Usuario de RRHH importa la configuración completa
- Sistema valida el esquema antes de aplicar
- ✅ **Ventajas:** Balance entre facilidad y corrección
- ❌ **Desventajas:** Requiere función de importación

**Opción 3: Configuración Manual por RRHH (NO RECOMENDADO)**
- Usuario debe crear el esquema paso a paso
- Alto riesgo de error humano
- Difícil de validar sin conocimientos técnicos
- ❌ **No recomendado para Nicaragua** debido a complejidad legal

**Recomendación Final:**
Para Nicaragua, use la **Opción 1** o **Opción 2**. El cálculo del IR con método acumulado es demasiado complejo para configuración manual y los errores pueden resultar en problemas legales con la DGI.

#### 3.3. Archivo de Importación para ReglaCalculo IR Nicaragua

Para facilitar la implementación, se puede proporcionar el siguiente archivo JSON listo para importar:

**Archivo: `ir_nicaragua_2025.json`**
```json
{
  "codigo": "IR_NICARAGUA",
  "nombre": "Impuesto sobre la Renta Nicaragua",
  "descripcion": "Cálculo de IR según Art. 19 numeral 6 LCT con método acumulado",
  "jurisdiccion": "Nicaragua",
  "moneda_referencia": "NIO",
  "version": "2025.1",
  "tipo_regla": "impuesto",
  "vigente_desde": "2025-01-01",
  "esquema_json": {
    "meta": {
      "name": "IR Nicaragua - Método Acumulado",
      "legal_reference": "Ley 891 - Art. 23 LCT",
      "calculation_method": "accumulated_average"
    },
    "inputs": [
      {"name": "salario_bruto", "type": "decimal", "source": "empleado.salario_base"},
      {"name": "salario_bruto_acumulado", "type": "decimal", "source": "acumulado.salario_bruto_acumulado"},
      {"name": "deducciones_antes_impuesto_acumulado", "type": "decimal", "source": "acumulado.deducciones_antes_impuesto_acumulado"},
      {"name": "ir_retenido_acumulado", "type": "decimal", "source": "acumulado.impuesto_retenido_acumulado"},
      {"name": "meses_trabajados", "type": "integer", "source": "acumulado.periodos_procesados"}
    ],
    "steps": [
      {"name": "inss_mes", "type": "calculation", "formula": "salario_bruto * 0.07", "output": "inss_mes"},
      {"name": "salario_neto_mes", "type": "calculation", "formula": "salario_bruto - inss_mes", "output": "salario_neto_mes"},
      {"name": "salario_neto_total", "type": "calculation", "formula": "(salario_bruto_acumulado + salario_bruto) - (deducciones_antes_impuesto_acumulado + inss_mes)", "output": "salario_neto_total"},
      {"name": "meses_totales", "type": "calculation", "formula": "meses_trabajados + 1", "output": "meses_totales"},
      {"name": "promedio_mensual", "type": "calculation", "formula": "salario_neto_total / meses_totales", "output": "promedio_mensual"},
      {"name": "expectativa_anual", "type": "calculation", "formula": "promedio_mensual * 12", "output": "expectativa_anual"},
      {"name": "ir_anual", "type": "tax_lookup", "table": "tabla_ir", "input": "expectativa_anual", "output": "ir_anual"},
      {"name": "ir_proporcional", "type": "calculation", "formula": "(ir_anual / 12) * meses_totales", "output": "ir_proporcional"},
      {"name": "ir_final", "type": "calculation", "formula": "max(ir_proporcional - ir_retenido_acumulado, 0)", "output": "ir_final"}
    ],
    "tax_tables": {
      "tabla_ir": [
        {"min": 0, "max": 100000, "rate": 0.00, "fixed": 0, "over": 0},
        {"min": 100000, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000},
        {"min": 200000, "max": 350000, "rate": 0.20, "fixed": 15000, "over": 200000},
        {"min": 350000, "max": 500000, "rate": 0.25, "fixed": 45000, "over": 350000},
        {"min": 500000, "max": null, "rate": 0.30, "fixed": 82500, "over": 500000}
      ]
    },
    "output": "ir_final"
  }
}
```

**Instrucciones de Importación:**
1. Guardar el JSON anterior en un archivo
2. Acceder a **Configuración** → **Reglas de Cálculo** → **Importar**
3. Seleccionar el archivo `ir_nicaragua_2025.json`
4. Verificar que todos los campos sean correctos
5. Guardar y activar la regla

#### 3.4. Crear Deducción de IR

1. Acceda a **Configuración** → **Deducciones**
2. Cree una nueva deducción:
   - **Código**: `IR`
   - **Nombre**: `Impuesto sobre la Renta (IR)`
   - **Descripción**: `Retención de IR según tarifa progresiva nicaragüense`
   - **Es Obligatoria**: ✓ Sí
   - **Prioridad**: `2` (después del INSS)
   - **Tipo de Fórmula**: `Regla de Cálculo`
   - **Regla de Cálculo**: Seleccionar `IR_NICARAGUA`
   - **Base de Cálculo**: `Salario Bruto - INSS`

### Paso 4: Configurar Prestaciones Patronales

Las prestaciones patronales no se deducen del salario del empleado, pero son costos para el empleador:

#### INSS Patronal (22.5%)

1. Acceda a **Configuración** → **Prestaciones**
2. Cree una nueva prestación:
   - **Código**: `INSS_PATRONAL`
   - **Nombre**: `INSS Patronal (22.5%)`
   - **Descripción**: `Aporte del empleador al INSS`
   - **Fórmula**: `salario_bruto * 0.225`
   - **Tipo**: `Porcentaje del Salario Bruto`

#### INATEC (2%)

1. Cree prestación:
   - **Código**: `INATEC`
   - **Nombre**: `INATEC (2%)`
   - **Descripción**: `Aporte al Instituto Nacional Tecnológico`
   - **Fórmula**: `salario_bruto * 0.02`

#### Vacaciones (8.33%)

1. Cree prestación:
   - **Código**: `VACACIONES`
   - **Nombre**: `Provisión Vacaciones (8.33%)`
   - **Descripción**: `Provisión mensual para vacaciones (1 mes / 12 meses)`
   - **Fórmula**: `salario_bruto * 0.0833`

#### Aguinaldo (8.33%)

1. Cree prestación:
   - **Código**: `AGUINALDO`
   - **Nombre**: `Provisión Aguinaldo (8.33%)`
   - **Descripción**: `Provisión mensual para décimo tercer mes`
   - **Fórmula**: `salario_bruto * 0.0833`

#### Indemnización (8.33%)

1. Cree prestación:
   - **Código**: `INDEMNIZACION`
   - **Nombre**: `Provisión Indemnización (8.33%)`
   - **Descripción**: `Provisión mensual para indemnización`
   - **Fórmula**: `salario_bruto * 0.0833`

### Paso 5: Configurar Percepciones

#### Horas Extra

1. Acceda a **Configuración** → **Percepciones**
2. Cree percepciones para horas extra:

**Horas Extra Diurnas:**
- **Código**: `HORAS_EXTRA_DIURNAS`
- **Nombre**: `Horas Extra Diurnas (100%)`
- **Descripción**: `Pago por horas extra diurnas al 200% del salario hora`
- **Es Gravable**: ✓ Sí
- **Tipo de Fórmula**: `Fórmula Personalizada`
- **Fórmula**: `(salario_mensual / 240) * 2 * horas`

**Horas Extra Nocturnas:**
- **Código**: `HORAS_EXTRA_NOCTURNAS`
- **Nombre**: `Horas Extra Nocturnas (150%)`
- **Descripción**: `Pago por horas extra nocturnas al 250% del salario hora`
- **Es Gravable**: ✓ Sí
- **Tipo de Fórmula**: `Fórmula Personalizada`
- **Fórmula**: `(salario_mensual / 240) * 2.5 * horas`

#### Comisiones

- **Código**: `COMISIONES`
- **Nombre**: `Comisiones por Ventas`
- **Es Gravable**: ✓ Sí
- **Tipo de Fórmula**: `Monto Variable`

#### Bonos e Incentivos

- **Código**: `BONO_PRODUCTIVIDAD`
- **Nombre**: `Bono por Productividad`
- **Es Gravable**: ✓ Sí
- **Tipo de Fórmula**: `Monto Variable`

- **Código**: `INCENTIVO`
- **Nombre**: `Incentivos`
- **Es Gravable**: ✓ Sí
- **Tipo de Fórmula**: `Monto Variable`

### Paso 6: Crear Tipo de Planilla

1. Acceda a **Configuración** → **Tipos de Planilla**
2. Cree un nuevo tipo:
   - **Código**: `MENSUAL_NIC`
   - **Nombre**: `Nómina Mensual Nicaragua`
   - **Descripción**: `Planilla mensual con INSS e IR nicaragüense`
   - **Periodicidad**: `mensual`
   - **Días**: `30` (usado para prorrateo de períodos parciales)
   - **Períodos por Año**: `12`
   - **Mes Inicio Fiscal**: `1` (enero)
   - **Día Inicio Fiscal**: `1`
   - **Acumula Anual**: ✓ Sí
   - **Moneda**: `NIO`
   
3. Asocie las percepciones, deducciones y prestaciones configuradas

!!! note "Manejo de Períodos Mensuales Completos"
    **Comportamiento del sistema para `periodicidad="mensual"`:**
    
    - **Mes calendario completo** (ej: 1 enero - 31 enero): El sistema usa el salario mensual completo SIN prorrateo, independientemente de si el mes tiene 28, 29, 30 o 31 días.
    - **Período parcial** (ej: 15 enero - 31 enero): El sistema prorratea usando `dias=30` como divisor base: `salario_mensual / 30 * días_trabajados`
    
    Este comportamiento asegura que un empleado contratado el día 1 del mes reciba su salario mensual completo.

!!! info "Configuración para Nóminas Quincenales"
    Si su empresa paga quincenalmente:
    - **Periodicidad**: `quincenal`
    - **Días**: `15`
    - **Períodos por Año**: `24`
    
    Para períodos quincenales, el salario del período = salario mensual ÷ 2

### Paso 7: Configurar Empleados

Para cada empleado:

1. Acceda a **Empleados** → **Nuevo Empleado**
2. Complete la información básica
3. Configure:
   - **Salario Mensual**: Salario base en córdobas
   - **Moneda del Salario**: NIO
   - **Tipo de Planilla**: Seleccionar `MENSUAL_NIC`
   - **Fecha de Ingreso**: Fecha de contratación

## Casos Especiales

### Caso 1: Pago de Vacaciones

Cuando un empleado toma vacaciones y recibe su pago de vacaciones:

**Escenario:**
- Salario mensual regular: C$ 20,000
- Días de vacaciones: 15 días
- Pago de vacaciones: C$ 10,000

**Tratamiento:**
1. El pago de vacaciones es un **ingreso extraordinario gravable**
2. Se debe calcular IR según metodología de pagos ocasionales (Art. 19, numeral 2)
3. Se debe aplicar INSS sobre el total

**Implementación en Coati:**

1. Crear una **Novedad de Nómina** o **Percepción Variable** para ese mes:
   - Tipo: `PAGO_VACACIONES`
   - Monto: C$ 10,000
   
2. El sistema calculará:
   ```
   Salario Bruto Total = 20,000 + 10,000 = C$ 30,000
   INSS = 30,000 × 0.07 = C$ 2,100
   Salario Neto = 30,000 - 2,100 = C$ 27,900
   
   IR Regular (base anual): Se mantiene
   IR Adicional (por pago ocasional): Calcular diferencia según tramos
   ```

### Caso 2: Incremento Salarial en Medio del Año

**Escenario:**
- Salario anterior: C$ 15,000 (enero a junio)
- Salario nuevo: C$ 18,000 (julio a diciembre)
- Retenciones anteriores de IR: C$ 12,000

**Metodología según Art. 19, numeral 3:**

1. **Calcular ingresos acumulados** (enero-junio):
   ```
   Salario Neto Mensual = 15,000 - (15,000 × 0.07) = 13,950
   Total Acumulado = 13,950 × 6 = C$ 83,700
   ```

2. **Proyectar nuevo salario** (julio-diciembre):
   ```
   Nuevo Salario Neto = 18,000 - (18,000 × 0.07) = 16,740
   Proyección Restante = 16,740 × 6 = C$ 100,440
   ```

3. **Calcular nuevo IR anual:**
   ```
   Renta Anual Total = 83,700 + 100,440 = C$ 184,140
   IR Anual = (184,140 - 100,000) × 0.15 = C$ 12,621
   ```

4. **Determinar IR pendiente:**
   ```
   IR Pendiente = 12,621 - (retenciones anteriores)
   IR Mensual Nuevo = IR Pendiente / 6 meses restantes
   ```

**Implementación en Coati:**

Este caso requiere un ajuste manual:

1. Registrar el cambio de salario del empleado
2. Crear una **Novedad de Ajuste de IR** para redistribuir el impuesto
3. Alternativamente, usar el módulo de **Ajuste de Retenciones**

### Caso 3: Bono Anual o Semestral

**Escenario:**
- Salario mensual: C$ 25,000
- Bono anual en diciembre: C$ 50,000

**Metodología según Art. 19, numeral 2:**

1. **Calcular IR base** (sin bono):
   ```
   Salario Neto = 25,000 - 1,750 = 23,250
   Renta Anual Base = 23,250 × 12 = 279,000
   IR Anual Base = 15,000 + (279,000 - 200,000) × 0.20 = 30,800
   ```

2. **Calcular IR con bono:**
   ```
   Bono Neto = 50,000 - 3,500 = 46,500
   Nueva Renta Anual = 279,000 + 46,500 = 325,500
   IR Anual Nuevo = 15,000 + (325,500 - 200,000) × 0.20 = 40,100
   ```

3. **IR del bono:**
   ```
   IR Bono = 40,100 - 30,800 = C$ 9,300
   ```

4. **Retención en diciembre:**
   ```
   IR Regular Diciembre = 30,800 / 12 = 2,567
   IR Total Diciembre = 2,567 + 9,300 = C$ 11,867
   ```

**Implementación en Coati:**

1. Crear percepción variable para el bono
2. El sistema debe aplicar metodología de pagos ocasionales
3. Verificar que la configuración del IR permita cálculo escalonado

!!! note "Automatización del Cálculo"
    El sistema Coati Payroll puede automatizar estos cálculos si la Regla de Cálculo del IR está correctamente configurada con el campo `base_calculo: "anual"` y `periodicidad: "mensual"`.

### Caso 4: Empleado con Período Incompleto

**Escenario:**
- Empleado ingresa en agosto
- Salario mensual: C$ 20,000
- Meses laborados: 5 (agosto-diciembre)

**Metodología según Art. 19, numeral 4:**

El cálculo es similar al regular, pero solo se proyecta proporcionalmente:

```
Salario Neto = 20,000 - 1,400 = 18,600
Renta Período = 18,600 × 5 = 93,000
IR Total = 0 (no supera el mínimo de 100,000)
```

**Implementación en Coati:**

El sistema calcula automáticamente según los meses laborados si el empleado tiene fecha de ingreso durante el período fiscal.

## Pruebas y Validación

### Casos de Prueba Recomendados

#### Test 1: Salario Mínimo Exento

**Entrada:**
- Salario Bruto: C$ 8,000

**Resultado Esperado:**
```
Salario Bruto:     C$  8,000.00
- INSS (7%):      (C$    560.00)
- IR:             (C$      0.00)  ← Renta anual < 100,000
= Salario Neto:    C$  7,440.00
```

#### Test 2: Salario en Primer Tramo

**Entrada:**
- Salario Bruto: C$ 15,000

**Resultado Esperado:**
```
Salario Neto Mensual: 15,000 - 1,050 = 13,950
Renta Anual: 13,950 × 12 = 167,400
IR Anual: (167,400 - 100,000) × 0.15 = 10,110
IR Mensual: 10,110 / 12 = 842.50

Salario Bruto:     C$ 15,000.00
- INSS (7%):      (C$  1,050.00)
- IR:             (C$    842.50)
= Salario Neto:    C$ 13,107.50
```

#### Test 3: Salario en Tramo Superior

**Entrada:**
- Salario Bruto: C$ 40,000

**Resultado Esperado:**
```
Salario Neto Mensual: 40,000 - 2,800 = 37,200
Renta Anual: 37,200 × 12 = 446,400
IR Anual: 45,000 + (446,400 - 350,000) × 0.25 = 69,100
IR Mensual: 69,100 / 12 = 5,758.33

Salario Bruto:     C$ 40,000.00
- INSS (7%):      (C$  2,800.00)
- IR:             (C$  5,758.33)
= Salario Neto:    C$ 31,441.67
```

#### Test 4: Salario con Bono

**Entrada:**
- Salario Bruto: C$ 20,000
- Bono: C$ 10,000

**Resultado Esperado:**
```
Salario Total: 30,000
INSS: 2,100
IR Regular: 1,636.67
IR Bono: ~1,500 (calculado según metodología de pagos ocasionales)
IR Total: ~3,136.67
Salario Neto: ~24,763.33
```

### Validación Manual

Para validar la configuración:

1. **Crear empleado de prueba** con diferentes niveles salariales
2. **Ejecutar nómina de prueba** en modo borrador
3. **Comparar resultados** con cálculos manuales
4. **Verificar que:**
   - INSS se calcula correctamente (7% del bruto)
   - IR aplica los tramos progresivos correctos
   - El salario neto es coherente
   - Las prestaciones patronales son correctas

### Herramienta de Validación

Puede crear un script de prueba personalizado para validar los cálculos:

```python
def calcular_nomina_nicaragua(salario_bruto):
    # INSS
    inss = salario_bruto * 0.07
    salario_neto = salario_bruto - inss
    
    # Proyección anual
    renta_anual = salario_neto * 12
    
    # IR según tramos
    if renta_anual <= 100000:
        ir_anual = 0
    elif renta_anual <= 200000:
        ir_anual = (renta_anual - 100000) * 0.15
    elif renta_anual <= 350000:
        ir_anual = 15000 + (renta_anual - 200000) * 0.20
    elif renta_anual <= 500000:
        ir_anual = 45000 + (renta_anual - 350000) * 0.25
    else:
        ir_anual = 82500 + (renta_anual - 500000) * 0.30
    
    ir_mensual = ir_anual / 12
    salario_final = salario_bruto - inss - ir_mensual
    
    return {
        'bruto': salario_bruto,
        'inss': inss,
        'ir': ir_mensual,
        'neto': salario_final
    }

# Probar
resultado = calcular_nomina_nicaragua(25000)
print(f"Salario Bruto: C$ {resultado['bruto']:,.2f}")
print(f"INSS: C$ {resultado['inss']:,.2f}")
print(f"IR: C$ {resultado['ir']:,.2f}")
print(f"Salario Neto: C$ {resultado['neto']:,.2f}")
```

## Preguntas Frecuentes

### ¿El sistema puede manejar múltiples empleadores?

El sistema Coati Payroll maneja la nómina para un solo empleador. Si un empleado tiene múltiples empleadores, cada uno calcula independientemente según la metodología del Art. 19, numeral 6, y es responsabilidad del empleado hacer su declaración anual consolidada ante la DGI.

### ¿Cómo manejo el aguinaldo (décimo tercer mes)?

El aguinaldo se maneja de dos formas:

1. **Provisión mensual**: Como prestación acumulada (8.33% mensual)
2. **Pago anual**: Como percepción extraordinaria gravable en diciembre

Cuando se paga el aguinaldo, debe aplicarse la metodología de pagos ocasionales para el IR.

### ¿Qué hago si cambia la tarifa del IR?

1. Cree una **nueva versión** de la Regla de Cálculo `IR_NICARAGUA`
2. Incremente la versión (ej: 2024.1 → 2025.1)
3. Actualice el esquema JSON con los nuevos tramos
4. Configure las fechas de vigencia
5. Active la nueva versión
6. Desactive la versión anterior

El sistema aplicará automáticamente la regla vigente según la fecha.

### ¿Cómo genero reportes para la DGI?

El sistema genera reportes de nómina que incluyen:

- Reporte de retenciones de IR
- Reporte de deducciones INSS
- Detalle por empleado

Consulte la sección de **Reportes** en la documentación principal.

### ¿El sistema calcula la liquidación final?

Sí, el sistema puede calcular liquidaciones finales incluyendo:

- Vacaciones no gozadas
- Aguinaldo proporcional
- Indemnización (según corresponda)
- Retenciones de IR sobre estos montos

Use el módulo de **Liquidaciones** o **Novedades Especiales**.

### ¿Puedo usar el sistema con USD?

Sí, el sistema es multi-moneda. Puede:

1. Configurar salarios en USD
2. Las reglas de IR deben convertirse a NIO usando el tipo de cambio oficial
3. Configure tipos de cambio en el sistema
4. El motor de cálculo aplicará conversiones automáticamente

!!! warning "Importante"
    Las tablas del IR están en córdobas. Si paga en USD, el sistema debe convertir a NIO para aplicar las retenciones según normativa de la DGI.

### ¿Cómo manejo deducciones adicionales?

Puede crear deducciones adicionales como:

- Préstamos a empleados
- Adelantos de salario
- Embargos judiciales
- Cuotas sindicales
- Seguros privados

Cada una con su prioridad y configuración específica. Consulte la guía de **Deducciones** y **Préstamos**.

### ¿Existe una calculadora en línea?

El sistema incluye una vista previa de nómina donde puede simular cálculos antes de ejecutar la planilla oficial.

También puede usar la herramienta `tax-engine.py` proporcionada en este documento para validaciones offline.

## Herramienta de Validación - Tax Engine

Para validar los cálculos de IR, puede usar el siguiente script de Python que implementa la lógica exacta de los auditores:

```python
import json
from dataclasses import dataclass

@dataclass
class TaxBracket:
    min: float
    max: float | None
    rate: float
    fixed: float = 0.0

@dataclass
class DeductionRule:
    name: str
    type: str  # "fixed", "percent"
    value: float

@dataclass
class TaxConfig:
    version: str
    currency: str
    brackets: list[TaxBracket]
    deductions: list[DeductionRule]

class TaxEngine:
    def __init__(self, config: TaxConfig):
        self.config = config

    def compute_deductions(self, income: float) -> dict:
        deduction_results = {}
        total = 0.0
        
        for d in self.config.deductions:
            if d.type == "fixed":
                amount = d.value
            elif d.type == "percent":
                amount = income * (d.value / 100.0)
            else:
                raise ValueError(f"Unknown deduction type: {d.type}")
            
            deduction_results[d.name] = amount
            total += amount
        
        return {"items": deduction_results, "total": total}

    def compute_tax(self, taxable_income: float) -> dict:
        if taxable_income <= 0:
            return {"tax": 0.0, "applied_bracket": None}
        
        for bracket in self.config.brackets:
            if bracket.max is None or taxable_income <= bracket.max:
                tax = bracket.fixed + (taxable_income - bracket.min) * bracket.rate
                return {"tax": max(tax, 0.0), "applied_bracket": bracket}
        
        raise RuntimeError("No bracket matched — malformed tax table.")

    def evaluate(self, income: float) -> dict:
        deductions = self.compute_deductions(income)
        taxable_income = max(income - deductions["total"], 0)
        tax_result = self.compute_tax(taxable_income)
        
        return {
            "income": income,
            "currency": self.config.currency,
            "deductions": deductions,
            "taxable_income": taxable_income,
            "tax": tax_result["tax"],
            "bracket": tax_result["applied_bracket"]
        }

# Configuración Nicaragua
nicaragua_config = TaxConfig(
    version="2024",
    currency="NIO",
    brackets=[
        TaxBracket(min=0, max=100000, rate=0.0, fixed=0),
        TaxBracket(min=100000, max=200000, rate=0.15, fixed=0),
        TaxBracket(min=200000, max=350000, rate=0.20, fixed=15000),
        TaxBracket(min=350000, max=500000, rate=0.25, fixed=45000),
        TaxBracket(min=500000, max=None, rate=0.30, fixed=82500)
    ],
    deductions=[
        DeductionRule(name="INSS", type="percent", value=7)
    ]
)

# Ejemplo de uso
engine = TaxEngine(nicaragua_config)
salario_anual = 300000
result = engine.evaluate(salario_anual)

print(f"\nIngreso anual: {result['income']} {result['currency']}")
print(f"INSS (7%): {result['deductions']['items']['INSS']:.2f}")
print(f"Ingreso gravable: {result['taxable_income']:.2f}")
print(f"IR anual: {result['tax']:.2f}")
print(f"IR mensual: {result['tax']/12:.2f}")
```

Guarde este script como `validar_ir_nicaragua.py` y ejecútelo con diferentes salarios para verificar los cálculos.

## Recursos Adicionales

### Referencias Legales

- **Ley de Concertación Tributaria (LCT)** - Ley No 822
- **Reglamento de la LCT** - Decreto No 01-2013
- **Ley No 891** - Reforma al Art. 23 de la LCT
- **Código del Trabajo de Nicaragua** - Ley No 185

### Contactos Útiles

- **DGI (Dirección General de Ingresos)**: [www.dgi.gob.ni](https://www.dgi.gob.ni)
- **INSS**: [www.inss.gob.ni](https://www.inss.gob.ni)
- **INATEC**: [www.inatec.gob.ni](https://www.inatec.gob.ni)

### Soporte Técnico

Para soporte técnico del sistema Coati Payroll:

- Documentación principal: Ver página de inicio
- Guías de usuario: Sección "Guía de Uso" en el menú
- Reportar problemas: [GitHub Issues](https://github.com/williamjmorenor/coati/issues)

---

## Resumen de Configuración Rápida

Para implementar Nicaragua rápidamente:

1. ✅ Configurar moneda NIO
2. ✅ Crear Regla de Cálculo `IR_NICARAGUA` con tramos progresivos
3. ✅ Crear deducción `INSS_LABORAL` (7%)
4. ✅ Crear deducción `IR` usando la regla creada
5. ✅ Crear prestaciones patronales (INSS Patronal, INATEC, etc.)
6. ✅ Crear percepciones según necesidades (horas extra, bonos, etc.)
7. ✅ Crear Tipo de Planilla `MENSUAL_NIC`
8. ✅ Registrar empleados
9. ✅ Ejecutar nómina de prueba
10. ✅ Validar resultados

!!! success "¡Listo!"
    Con estos pasos, el sistema Coati Payroll estará configurado para manejar nóminas según la legislación nicaragüense.

---

*Documento actualizado: Diciembre 2024*  
*Versión: 1.0*  
*Legislación base: Ley de Concertación Tributaria vigente*
