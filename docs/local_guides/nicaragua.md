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

*Fuente: Artículo 23 LCT, reformado por Ley No 891 del 10 de Diciembre de 2014*

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

##### 1. Retención Mensual Regular (Art. 19, numeral 1)

Para períodos fiscales completos con un solo empleador:

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

**Ejemplo:**

Para un salario bruto de C$ 25,000:

```
1. Salario Bruto:        C$ 25,000.00
2. INSS (7%):            C$  1,750.00
3. Salario Neto:         C$ 23,250.00
4. Renta Anual:          C$ 279,000.00  (23,250 × 12)

5. Aplicar tarifa progresiva:
   Tramo: C$ 200,000 - C$ 350,000
   IR Anual = 15,000 + (279,000 - 200,000) × 0.20
   IR Anual = 15,000 + 79,000 × 0.20
   IR Anual = 15,000 + 15,800
   IR Anual = C$ 30,800.00

6. IR Mensual:           C$ 2,566.67  (30,800 / 12)
```

**Resultado Final:**
```
Salario Bruto:           C$ 25,000.00
- INSS (7%):            (C$  1,750.00)
- IR:                   (C$  2,566.67)
= Salario Neto:          C$ 20,683.33
```

##### 2. Pagos Ocasionales (Art. 19, numeral 2)

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

#### Fórmula Simplificada para Cálculo en el Sistema

```python
# 1. Calcular salario neto mensual
salario_neto = salario_bruto - (salario_bruto * 0.07)

# 2. Proyectar a anual
renta_anual = salario_neto * 12

# 3. Aplicar tramos progresivos
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

# 4. Calcular retención mensual
ir_mensual = ir_anual / 12
```

## Configuración del Sistema

### Paso 1: Configurar Moneda

1. Acceda a **Configuración** → **Monedas**
2. Verifique que exista la moneda **NIO (Córdoba)**
3. Si no existe, créela:
   - **Código**: NIO
   - **Nombre**: Córdoba Nicaragüense
   - **Símbolo**: C$

### Paso 2: Configurar INSS Laboral

#### Opción A: Deducción Simple con Fórmula

1. Acceda a **Configuración** → **Deducciones**
2. Cree una nueva deducción:
   - **Código**: `INSS_LABORAL`
   - **Nombre**: `INSS Laboral (7%)`
   - **Descripción**: `Aporte del empleado al Instituto Nicaragüense de Seguridad Social`
   - **Es Obligatoria**: ✓ Sí
   - **Prioridad**: `1` (alta prioridad, se deduce primero)
   - **Tipo de Fórmula**: `Porcentaje del Salario Bruto`
   - **Fórmula**: `0.07` o `7`
   - **Afecta IR**: ✓ Sí (reduce la base imponible del IR)

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

**Esquema JSON:**

```json
{
  "tipo": "tramos",
  "descripcion": "Impuesto sobre la Renta Nicaragua - Tarifa Progresiva 2024",
  "base_calculo": "anual",
  "deducciones_previas": ["INSS_LABORAL"],
  "tramos": [
    {
      "desde": 0,
      "hasta": 100000,
      "tasa": 0.00,
      "base_fija": 0,
      "descripcion": "Exento - Hasta C$ 100,000"
    },
    {
      "desde": 100000,
      "hasta": 200000,
      "tasa": 0.15,
      "base_fija": 0,
      "descripcion": "15% sobre exceso de C$ 100,000"
    },
    {
      "desde": 200000,
      "hasta": 350000,
      "tasa": 0.20,
      "base_fija": 15000,
      "descripcion": "C$ 15,000 + 20% sobre exceso de C$ 200,000"
    },
    {
      "desde": 350000,
      "hasta": 500000,
      "tasa": 0.25,
      "base_fija": 45000,
      "descripcion": "C$ 45,000 + 25% sobre exceso de C$ 350,000"
    },
    {
      "desde": 500000,
      "hasta": null,
      "tasa": 0.30,
      "base_fija": 82500,
      "descripcion": "C$ 82,500 + 30% sobre exceso de C$ 500,000"
    }
  ],
  "periodicidad": "mensual",
  "factor_anual": 12,
  "notas": "Conforme Art. 23 LCT, reformado por Ley No 891"
}
```

!!! tip "Esquema Completo"
    El esquema incluye campos adicionales como `base_calculo`, `deducciones_previas`, y `factor_anual` que ayudan al motor de cálculo a entender cómo aplicar la regla correctamente.

#### 3.2. Crear Deducción de IR

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
   - **Periodicidad**: `Mensual`
   - **Moneda**: `NIO`
   
3. Asocie las percepciones, deducciones y prestaciones configuradas

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
