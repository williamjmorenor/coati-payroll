# Cálculo del IR en Nicaragua - Guía Paso a Paso

Esta guía explica de manera sencilla y detallada cómo calcular el Impuesto sobre la Renta (IR) en Nicaragua, incluso si nunca has hecho este cálculo antes.

## ¿Qué es el IR?

El **Impuesto sobre la Renta (IR)** es un impuesto que se cobra sobre los ingresos que recibe una persona trabajadora. En Nicaragua, este impuesto es **progresivo**, lo que significa que quien gana más, paga un porcentaje mayor.

!!! info "Analogía Simple"
    Imagina que el gobierno divide los ingresos en "escalones" o "tramos". En cada escalón, pagas un porcentaje diferente. Los primeros C$ 100,000 al año están exentos (no pagas nada), pero conforme subes de escalón, el porcentaje aumenta.

## Los 5 Pasos del Cálculo

El cálculo del IR en Nicaragua sigue **5 pasos simples**:

1. **Calcular el Salario Bruto Anual**
2. **Restar el INSS (7%)**
3. **Aplicar la Tabla de Tramos Progresivos**
4. **Calcular el IR Anual**
5. **Dividir entre 12 para obtener el IR Mensual**

Vamos a ver cada paso con ejemplos prácticos.

---

## Paso 1: Calcular el Salario Bruto Anual

El primer paso es simple: **multiplicar el salario mensual bruto por 12**.

**¿Qué es el salario bruto?**  
Es el salario que aparece en tu contrato, **antes** de cualquier descuento (INSS, IR, préstamos, etc.).

### Ejemplo 1: Salario de C$ 15,000 mensuales

```
Salario Mensual Bruto = C$ 15,000
Salario Anual Bruto = C$ 15,000 × 12 = C$ 180,000
```

### Ejemplo 2: Salario de C$ 25,000 mensuales

```
Salario Mensual Bruto = C$ 25,000
Salario Anual Bruto = C$ 25,000 × 12 = C$ 300,000
```

!!! tip "¿Por qué anual?"
    El IR se calcula con base anual porque la ley establece los tramos de impuestos en montos anuales. Aunque el descuento se hace mensualmente, el cálculo requiere proyectar a todo el año.

---

## Paso 2: Restar el INSS (7%)

El **INSS (Instituto Nicaragüense de Seguridad Social)** es una deducción obligatoria del **7%** sobre el salario bruto. Esta deducción es **deducible del IR**, es decir, reduce la cantidad sobre la cual se calcula el impuesto.

### ¿Cómo se calcula?

```
INSS Anual = Salario Bruto Anual × 0.07
```

**O también puedes pensarlo como:**
```
INSS Anual = Salario Bruto Anual × 7 / 100
```

### Ejemplo 1: Con salario de C$ 180,000 anuales

```
INSS Anual = C$ 180,000 × 0.07 = C$ 12,600
```

### Ejemplo 2: Con salario de C$ 300,000 anuales

```
INSS Anual = C$ 300,000 × 0.07 = C$ 21,000
```

### Calcular la Renta Neta

Ahora restamos el INSS del salario bruto para obtener la **Renta Neta Anual** (también llamada "salario neto antes de IR"):

```
Renta Neta Anual = Salario Bruto Anual - INSS Anual
```

### Ejemplo 1:

```
Renta Neta Anual = C$ 180,000 - C$ 12,600 = C$ 167,400
```

### Ejemplo 2:

```
Renta Neta Anual = C$ 300,000 - C$ 21,000 = C$ 279,000
```

!!! important "Punto Clave"
    La **Renta Neta Anual** es el monto que usaremos para buscar en la tabla de tramos progresivos. Este es el número más importante para el siguiente paso.

---

## Paso 3: Conocer la Tabla de Tramos Progresivos

Nicaragua tiene una tabla de 5 tramos para calcular el IR. Esta tabla está definida por ley:

| Tramo | Renta Neta Anual (Desde) | Renta Neta Anual (Hasta) | Impuesto Base | Tasa Marginal | Sobre Exceso de |
|-------|--------------------------|--------------------------|---------------|---------------|-----------------|
| 1     | C$ 0.01                  | C$ 100,000               | C$ 0          | 0%            | —               |
| 2     | C$ 100,000.01            | C$ 200,000               | C$ 0          | 15%           | C$ 100,000      |
| 3     | C$ 200,000.01            | C$ 350,000               | C$ 15,000     | 20%           | C$ 200,000      |
| 4     | C$ 350,000.01            | C$ 500,000               | C$ 45,000     | 25%           | C$ 350,000      |
| 5     | C$ 500,000.01            | En adelante              | C$ 82,500     | 30%           | C$ 500,000      |

### ¿Cómo leer esta tabla?

Vamos a explicar cada columna:

1. **Tramo**: El número del escalón
2. **Desde/Hasta**: El rango de renta neta anual que cae en este tramo
3. **Impuesto Base**: La cantidad fija que ya pagas solo por estar en este tramo
4. **Tasa Marginal**: El porcentaje que pagas sobre la cantidad que excede el límite inferior
5. **Sobre Exceso de**: A partir de qué monto se calcula el porcentaje adicional

### Ejemplo Visual: Tramo 3

Si tu renta neta anual es **C$ 279,000**, caes en el **Tramo 3** porque:
- Es mayor a C$ 200,000.01 ✓
- Es menor o igual a C$ 350,000 ✓

Para este tramo:
- Ya pagas un **impuesto base** de C$ 15,000 (es fijo)
- Sobre lo que excede de C$ 200,000, pagas un **20% adicional**

---

## Paso 4: Calcular el IR Anual

Ahora viene la parte donde aplicamos la fórmula. Dependiendo del tramo en que caigas, el cálculo es ligeramente diferente.

### Fórmula General

```
IR Anual = Impuesto Base + (Renta Neta Anual - Exceso de) × Tasa Marginal
```

Suena complicado, pero veamos ejemplos concretos:

---

### Ejemplo A: Salario de C$ 10,000 mensuales (C$ 120,000 anuales)

#### Paso 2: Calcular INSS y Renta Neta
```
Salario Bruto Anual = C$ 120,000
INSS (7%) = C$ 120,000 × 0.07 = C$ 8,400
Renta Neta Anual = C$ 120,000 - C$ 8,400 = C$ 111,600
```

#### Paso 3: Buscar el Tramo
Con C$ 111,600, estamos en el **Tramo 2**:
- Desde: C$ 100,000.01
- Hasta: C$ 200,000
- Impuesto Base: C$ 0
- Tasa Marginal: 15%
- Sobre Exceso de: C$ 100,000

#### Paso 4: Aplicar la Fórmula
```
Exceso = C$ 111,600 - C$ 100,000 = C$ 11,600
Impuesto sobre el exceso = C$ 11,600 × 0.15 = C$ 1,740
IR Anual = C$ 0 + C$ 1,740 = C$ 1,740
```

#### Paso 5: IR Mensual
```
IR Mensual = C$ 1,740 ÷ 12 = C$ 145.00
```

#### Resumen Mensual
```
Salario Bruto:     C$ 10,000.00
- INSS (7%):      (C$    700.00)
- IR:             (C$    145.00)
= Salario Neto:    C$  9,155.00
```

!!! success "Interpretación"
    De cada C$ 10,000 que ganas, te quedan C$ 9,155 después de INSS e IR.

---

### Ejemplo B: Salario de C$ 15,000 mensuales (C$ 180,000 anuales)

#### Paso 2: Calcular INSS y Renta Neta
```
Salario Bruto Anual = C$ 180,000
INSS (7%) = C$ 180,000 × 0.07 = C$ 12,600
Renta Neta Anual = C$ 180,000 - C$ 12,600 = C$ 167,400
```

#### Paso 3: Buscar el Tramo
Con C$ 167,400, estamos en el **Tramo 2** (igual que el anterior):
- Impuesto Base: C$ 0
- Tasa Marginal: 15%
- Sobre Exceso de: C$ 100,000

#### Paso 4: Aplicar la Fórmula
```
Exceso = C$ 167,400 - C$ 100,000 = C$ 67,400
Impuesto sobre el exceso = C$ 67,400 × 0.15 = C$ 10,110
IR Anual = C$ 0 + C$ 10,110 = C$ 10,110
```

#### Paso 5: IR Mensual
```
IR Mensual = C$ 10,110 ÷ 12 = C$ 842.50
```

#### Resumen Mensual
```
Salario Bruto:     C$ 15,000.00
- INSS (7%):      (C$  1,050.00)
- IR:             (C$    842.50)
= Salario Neto:    C$ 13,107.50
```

---

### Ejemplo C: Salario de C$ 25,000 mensuales (C$ 300,000 anuales)

#### Paso 2: Calcular INSS y Renta Neta
```
Salario Bruto Anual = C$ 300,000
INSS (7%) = C$ 300,000 × 0.07 = C$ 21,000
Renta Neta Anual = C$ 300,000 - C$ 21,000 = C$ 279,000
```

#### Paso 3: Buscar el Tramo
Con C$ 279,000, estamos en el **Tramo 3**:
- Desde: C$ 200,000.01
- Hasta: C$ 350,000
- Impuesto Base: C$ 15,000
- Tasa Marginal: 20%
- Sobre Exceso de: C$ 200,000

#### Paso 4: Aplicar la Fórmula
```
Exceso = C$ 279,000 - C$ 200,000 = C$ 79,000
Impuesto sobre el exceso = C$ 79,000 × 0.20 = C$ 15,800
IR Anual = C$ 15,000 + C$ 15,800 = C$ 30,800
```

!!! note "Desglose del IR"
    **C$ 15,000** es lo que ya pagas fijo por estar en el Tramo 3  
    **+ C$ 15,800** es el 20% sobre los C$ 79,000 que exceden el límite de C$ 200,000  
    **= C$ 30,800** total de IR anual

#### Paso 5: IR Mensual
```
IR Mensual = C$ 30,800 ÷ 12 = C$ 2,566.67
```

#### Resumen Mensual
```
Salario Bruto:     C$ 25,000.00
- INSS (7%):      (C$  1,750.00)
- IR:             (C$  2,566.67)
= Salario Neto:    C$ 20,683.33
```

---

### Ejemplo D: Salario de C$ 50,000 mensuales (C$ 600,000 anuales)

#### Paso 2: Calcular INSS y Renta Neta
```
Salario Bruto Anual = C$ 600,000
INSS (7%) = C$ 600,000 × 0.07 = C$ 42,000
Renta Neta Anual = C$ 600,000 - C$ 42,000 = C$ 558,000
```

#### Paso 3: Buscar el Tramo
Con C$ 558,000, estamos en el **Tramo 5** (el más alto):
- Desde: C$ 500,000.01
- Hasta: En adelante (sin límite)
- Impuesto Base: C$ 82,500
- Tasa Marginal: 30%
- Sobre Exceso de: C$ 500,000

#### Paso 4: Aplicar la Fórmula
```
Exceso = C$ 558,000 - C$ 500,000 = C$ 58,000
Impuesto sobre el exceso = C$ 58,000 × 0.30 = C$ 17,400
IR Anual = C$ 82,500 + C$ 17,400 = C$ 99,900
```

!!! note "Desglose del IR"
    **C$ 82,500** es lo que ya pagas fijo por estar en el Tramo 5  
    **+ C$ 17,400** es el 30% sobre los C$ 58,000 que exceden los C$ 500,000  
    **= C$ 99,900** total de IR anual

#### Paso 5: IR Mensual
```
IR Mensual = C$ 99,900 ÷ 12 = C$ 8,325.00
```

#### Resumen Mensual
```
Salario Bruto:     C$ 50,000.00
- INSS (7%):      (C$  3,500.00)
- IR:             (C$  8,325.00)
= Salario Neto:    C$ 38,175.00
```

---

## Paso 5: Dividir entre 12 (IR Mensual)

Como vimos en todos los ejemplos, el último paso es simple:

```
IR Mensual = IR Anual ÷ 12
```

Este es el monto que se descuenta cada mes de tu salario.

---

## Tabla Resumen de Ejemplos

Para facilitar la comprensión, aquí está una tabla con todos los ejemplos:

| Salario Mensual | Salario Anual | INSS (7%) | Renta Neta | Tramo | IR Anual | IR Mensual | Salario Neto |
|-----------------|---------------|-----------|------------|-------|----------|------------|--------------|
| C$ 8,333        | C$ 100,000    | C$ 7,000  | C$ 93,000  | 1     | C$ 0     | C$ 0       | C$ 7,750     |
| C$ 10,000       | C$ 120,000    | C$ 8,400  | C$ 111,600 | 2     | C$ 1,740 | C$ 145     | C$ 9,155     |
| C$ 15,000       | C$ 180,000    | C$ 12,600 | C$ 167,400 | 2     | C$ 10,110| C$ 843     | C$ 13,108    |
| C$ 20,000       | C$ 240,000    | C$ 16,800 | C$ 223,200 | 3     | C$ 19,640| C$ 1,637   | C$ 16,963    |
| C$ 25,000       | C$ 300,000    | C$ 21,000 | C$ 279,000 | 3     | C$ 30,800| C$ 2,567   | C$ 20,683    |
| C$ 35,000       | C$ 420,000    | C$ 29,400 | C$ 390,600 | 4     | C$ 55,150| C$ 4,596   | C$ 27,954    |
| C$ 50,000       | C$ 600,000    | C$ 42,000 | C$ 558,000 | 5     | C$ 99,900| C$ 8,325   | C$ 38,175    |

---

## Casos Especiales

### ¿Qué pasa si recibo un bono?

Cuando recibes un **bono, comisión, o pago extraordinario**, se aplica una metodología especial:

1. Se calcula el IR como si no existiera el bono (IR base)
2. Se suma el bono a tu renta anual y se recalcula el IR (IR nuevo)
3. La diferencia entre IR nuevo e IR base es el impuesto sobre el bono
4. Ese mes pagas: IR regular + IR del bono

**Ejemplo:**

Salario regular: C$ 20,000 mensuales  
Bono en diciembre: C$ 10,000

```
Sin bono:
- Renta Anual: C$ 223,200
- IR Anual: C$ 19,640

Con bono:
- Bono Neto: C$ 10,000 - C$ 700 (INSS) = C$ 9,300
- Nueva Renta Anual: C$ 223,200 + C$ 9,300 = C$ 232,500
- Nuevo IR Anual: C$ 21,140

IR del Bono:
- Diferencia: C$ 21,140 - C$ 19,640 = C$ 1,500

En diciembre pagarás:
- IR Regular: C$ 1,637
- IR Bono: C$ 1,500
- Total IR: C$ 3,137
```

### ¿Qué pasa si tengo un aumento de salario?

Si tu salario aumenta a mitad de año, se debe **recalcular el IR** tomando en cuenta:
- Los meses con el salario anterior
- Los meses restantes con el nuevo salario
- Restar las retenciones ya efectuadas
- Distribuir el IR pendiente en los meses restantes

Este es un caso complejo que generalmente el sistema maneja automáticamente.

---

## Herramienta de Cálculo

Puedes usar esta fórmula en Excel o en una calculadora:

### Para calcular tu IR mensual:

1. **Paso 1**: `Anual = Mensual * 12`
2. **Paso 2**: `INSS = Anual * 0.07`
3. **Paso 3**: `RentaNeta = Anual - INSS`
4. **Paso 4**: Buscar el tramo y aplicar:
   ```
   SI(RentaNeta <= 100000, 0,
   SI(RentaNeta <= 200000, (RentaNeta - 100000) * 0.15,
   SI(RentaNeta <= 350000, 15000 + (RentaNeta - 200000) * 0.20,
   SI(RentaNeta <= 500000, 45000 + (RentaNeta - 350000) * 0.25,
   82500 + (RentaNeta - 500000) * 0.30))))
   ```
5. **Paso 5**: `IRMensual = IRAñual / 12`

### Calculadora Python

Si tienes Python instalado, puedes usar este script:

```python
def calcular_ir_nicaragua(salario_mensual):
    """Calcula el IR mensual para un salario en Nicaragua"""
    
    # Paso 1: Calcular salario anual
    salario_anual = salario_mensual * 12
    
    # Paso 2: Calcular INSS (7%)
    inss_anual = salario_anual * 0.07
    
    # Paso 3: Calcular renta neta
    renta_neta = salario_anual - inss_anual
    
    # Paso 4: Aplicar tabla progresiva
    if renta_neta <= 100000:
        ir_anual = 0
    elif renta_neta <= 200000:
        ir_anual = (renta_neta - 100000) * 0.15
    elif renta_neta <= 350000:
        ir_anual = 15000 + (renta_neta - 200000) * 0.20
    elif renta_neta <= 500000:
        ir_anual = 45000 + (renta_neta - 350000) * 0.25
    else:
        ir_anual = 82500 + (renta_neta - 500000) * 0.30
    
    # Paso 5: Calcular IR mensual
    ir_mensual = ir_anual / 12
    inss_mensual = inss_anual / 12
    salario_neto = salario_mensual - inss_mensual - ir_mensual
    
    # Mostrar resultados
    print(f"Salario Bruto Mensual: C$ {salario_mensual:,.2f}")
    print(f"Salario Bruto Anual:   C$ {salario_anual:,.2f}")
    print(f"INSS (7%):            (C$ {inss_mensual:,.2f})")
    print(f"IR:                   (C$ {ir_mensual:,.2f})")
    print(f"Salario Neto Mensual:  C$ {salario_neto:,.2f}")
    
    return {
        'bruto': salario_mensual,
        'inss': inss_mensual,
        'ir': ir_mensual,
        'neto': salario_neto
    }

# Ejemplo de uso
calcular_ir_nicaragua(25000)
```

---

## Preguntas Frecuentes

### ¿Por qué se calcula anualmente si el descuento es mensual?

Porque la ley establece los tramos en montos anuales. El descuento mensual es una **retención anticipada** del impuesto anual. Al final del año, si trabajaste todo el período, las retenciones mensuales deben sumar exactamente el IR anual calculado.

### ¿Qué pasa si trabajo solo parte del año?

Si trabajas solo parte del año (por ejemplo, entraste en agosto), el cálculo se ajusta proporcionalmente. El sistema proyecta solo los meses que trabajarás.

### ¿El INSS siempre es 7%?

Sí, el INSS laboral (que paga el empleado) es siempre 7% del salario bruto. El empleador paga un porcentaje adicional (22.5%) pero eso no se descuenta de tu salario.

### ¿Puedo pedir devolución si me retuvieron de más?

Sí, si al final del año las retenciones fueron mayores al IR que te correspondía (por ejemplo, si tuviste períodos sin trabajar), puedes solicitar devolución ante la DGI presentando tu declaración anual.

### ¿Los bonos y horas extra pagan IR?

Sí, **todos los ingresos** (salario base, horas extra, bonos, comisiones, etc.) están sujetos a INSS e IR.

### ¿Hay algún monto exento?

Sí, si tu renta neta anual es menor o igual a C$ 100,000 (aproximadamente C$ 8,333 mensuales brutos), no pagas IR. Solo pagas INSS.

---

## Resumen en 5 Pasos

1. 📊 **Multiplica** tu salario mensual × 12 = Salario Anual
2. 💰 **Resta** el INSS (7%) = Renta Neta Anual
3. 📋 **Busca** en qué tramo caes según la tabla
4. 🧮 **Aplica** la fórmula: Impuesto Base + (Exceso × Tasa) = IR Anual
5. 📅 **Divide** entre 12 = IR Mensual

!!! success "¡Ya sabes calcular el IR!"
    Con estos 5 pasos puedes calcular el IR de cualquier salario en Nicaragua. Practica con diferentes montos para familiarizarte con el proceso.

---

## Validación de Cálculos

Para validar que tus cálculos son correctos, consulta la [Guía de Implementación para Nicaragua](nicaragua.md#herramienta-de-validacion-tax-engine) donde encontrarás un script completo de validación que implementa exactamente la misma lógica explicada en esta guía.

El script es consistente con las tablas de Excel que usan los auditores para validar los cálculos de IR en Nicaragua.

---

## Recursos Adicionales

- [Guía de Implementación Completa para Nicaragua](nicaragua.md) - Configuración detallada del sistema
- [Ley de Concertación Tributaria](https://www.dgi.gob.ni) - Marco legal completo
- [Calculadora de IR en línea](https://www.dgi.gob.ni/calculadora) - Herramienta oficial de la DGI

---

*Documento creado con fines educativos*  
*Última actualización: Diciembre 2024*  
*Basado en la legislación tributaria vigente de Nicaragua*
