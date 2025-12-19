# Guía Técnica de Implementación: Nicaragua

**Audiencia**: Implementadores de sistemas con experiencia en nóminas y cálculos de impuestos

**Objetivo**: Proporcionar una guía técnica detallada paso a paso para implementar correctamente los cálculos de nómina de Nicaragua en Coati Payroll.

## Tabla de Contenidos

- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Modelo de Datos Relevante](#modelo-de-datos-relevante)
- [Método de Cálculo del IR](#metodo-de-calculo-del-ir)
- [Implementación Paso a Paso](#implementacion-paso-a-paso)
- [Configuración de ReglaCalculo](#configuracion-de-reglacalculo)
- [Validación y Pruebas](#validacion-y-pruebas)
- [Troubleshooting](#troubleshooting)
- [Casos de Uso Avanzados](#casos-de-uso-avanzados)

---

## Arquitectura del Sistema

### Flujo de Ejecución de Nómina

```
Usuario → Planilla → NominaEngine → FormulaEngine → Base de Datos
                          ↓
                    [Percepciones]
                          ↓
                    [Deducciones] (en orden de prioridad)
                          ↓
                    [Prestaciones]
                          ↓
                    [AcumuladoAnual] ← Base para IR próximo período
```

### Componentes Clave

1. **NominaEngine** (`coati_payroll/nomina_engine.py`)
   - Motor principal de ejecución de nómina
   - Procesa empleados de una planilla
   - Ejecuta fórmulas en orden de prioridad
   - Actualiza valores acumulados

2. **FormulaEngine** (`coati_payroll/formula_engine.py`)
   - Motor de evaluación de fórmulas
   - Soporta operaciones aritméticas, condicionales, funciones
   - Implementa `_calculate_bracket_tax()` para impuestos progresivos
   - Provee contexto con variables disponibles

3. **ReglaCalculo** (modelo de base de datos)
   - Almacena definiciones de cálculo en formato JSON
   - Soporta múltiples tipos: `formula`, `tramos`, `tabla`
   - Versionable y con vigencia temporal

4. **AcumuladoAnual** (modelo de base de datos)
   - Almacena valores acumulados por empleado por año fiscal
   - Campos clave para Nicaragua:
     - `salario_bruto_acumulado`
     - `deducciones_antes_impuesto_acumulado`
     - `impuesto_retenido_acumulado`
     - `periodos_procesados`

---

## Modelo de Datos Relevante

### Tabla: `acumulado_anual`

```sql
CREATE TABLE acumulado_anual (
    id INTEGER PRIMARY KEY,
    empleado_id INTEGER NOT NULL,
    anio_fiscal INTEGER NOT NULL,
    salario_bruto_acumulado NUMERIC(18, 2),
    salario_gravable_acumulado NUMERIC(18, 2),
    deducciones_antes_impuesto_acumulado NUMERIC(18, 2),
    impuesto_retenido_acumulado NUMERIC(18, 2),
    prestaciones_acumuladas NUMERIC(18, 2),
    periodos_procesados INTEGER,
    -- ... más campos
    UNIQUE(empleado_id, anio_fiscal)
);
```

**Campos críticos para Nicaragua IR:**

| Campo | Descripción | Uso en IR |
|-------|-------------|-----------|
| `salario_bruto_acumulado` | Suma de salarios brutos de meses anteriores | Base para calcular promedio |
| `deducciones_antes_impuesto_acumulado` | INSS y otras deducciones pre-IR acumuladas | Restar de bruto para obtener neto |
| `impuesto_retenido_acumulado` | IR ya retenido en meses anteriores | Restar de IR calculado para mes actual |
| `periodos_procesados` | Número de meses ya procesados | Divisor para promedio mensual |

### Tabla: `regla_calculo`

```sql
CREATE TABLE regla_calculo (
    id INTEGER PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    version VARCHAR(50),
    jurisdiccion VARCHAR(100),
    tipo_regla VARCHAR(50),
    schema JSON NOT NULL,  -- Configuración en JSON
    vigente_desde DATE,
    vigente_hasta DATE,
    -- ... más campos
);
```

---

## Método de Cálculo del IR

### Fundamento Legal

**Artículo 19, numeral 6 de la Ley de Concertación Tributaria (LCT)**

El método acumulado con promedio mensual es obligatorio para empleados que laboran para un solo empleador durante múltiples meses en el año fiscal.

### Algoritmo Detallado

```python
# Pseudocódigo del método acumulado (Art. 19 numeral 6)

def calcular_ir_mes_actual(empleado, mes_actual, acumulado_anual):
    """
    Calcula el IR a retener en el mes actual usando método acumulado.
    
    Args:
        empleado: Empleado con salario_bruto_mes
        mes_actual: Mes que se está procesando (1-12)
        acumulado_anual: Registro de AcumuladoAnual con valores previos
    
    Returns:
        Decimal: IR a retener este mes
    """
    
    # Paso 1: Calcular INSS del mes actual (7%)
    inss_mes_actual = empleado.salario_bruto_mes * 0.07
    
    # Paso 2: Calcular salario neto del mes actual
    salario_neto_mes = empleado.salario_bruto_mes - inss_mes_actual
    
    # Paso 3: Acumular salario bruto y deducciones
    salario_bruto_total = acumulado_anual.salario_bruto_acumulado + empleado.salario_bruto_mes
    deducciones_total = acumulado_anual.deducciones_antes_impuesto_acumulado + inss_mes_actual
    
    # Paso 4: Calcular salario neto acumulado
    salario_neto_acumulado = salario_bruto_total - deducciones_total
    
    # Paso 5: Contar meses trabajados (incluyendo el actual)
    meses_totales = acumulado_anual.periodos_procesados + 1
    
    # Paso 6: Calcular promedio mensual
    promedio_mensual = salario_neto_acumulado / meses_totales
    
    # Paso 7: Proyectar expectativa anual
    expectativa_anual = promedio_mensual * 12
    
    # Paso 8: Aplicar tabla progresiva
    ir_anual = aplicar_tabla_progresiva(expectativa_anual)
    
    # Paso 9: Calcular IR proporcional a meses trabajados
    ir_proporcional = (ir_anual / 12) * meses_totales
    
    # Paso 10: Restar retenciones previas
    ir_mes_actual = max(ir_proporcional - acumulado_anual.impuesto_retenido_acumulado, 0)
    
    return ir_mes_actual


def aplicar_tabla_progresiva(renta_anual):
    """
    Aplica la tabla progresiva del IR de Nicaragua.
    
    Tabla vigente (Ley 891):
    - C$ 0 - 100,000: 0%
    - C$ 100,000 - 200,000: 15% sobre exceso de 100,000
    - C$ 200,000 - 350,000: C$ 15,000 + 20% sobre exceso de 200,000
    - C$ 350,000 - 500,000: C$ 45,000 + 25% sobre exceso de 350,000
    - C$ 500,000+: C$ 82,500 + 30% sobre exceso de 500,000
    """
    if renta_anual <= 100000:
        return 0
    elif renta_anual <= 200000:
        return (renta_anual - 100000) * 0.15
    elif renta_anual <= 350000:
        return 15000 + (renta_anual - 200000) * 0.20
    elif renta_anual <= 500000:
        return 45000 + (renta_anual - 350000) * 0.25
    else:
        return 82500 + (renta_anual - 500000) * 0.30
```

### Diferencias Clave con Otros Métodos

| Aspecto | Método Simple (❌ Incorrecto) | Método Acumulado (✅ Correcto) |
|---------|----------------------------|--------------------------------|
| Proyección | Multiplica mes actual × 12 | Promedia meses trabajados × 12 |
| Ajuste | No se ajusta a variaciones | Se ajusta automáticamente |
| Base legal | No cumple Art. 19 numeral 6 | Cumple con LCT |
| Salarios variables | Retiene incorrectamente | Retiene correctamente |

---

## Implementación Paso a Paso

### Fase 1: Preparación de Base de Datos

#### 1.1 Verificar Tablas

```bash
# Conectarse a la base de datos y verificar existencia de tablas
psql -d coati_payroll -c "\dt acumulado_anual"
psql -d coati_payroll -c "\dt regla_calculo"
psql -d coati_payroll -c "\dt deduccion"
```

#### 1.2 Verificar Migraciónes

```bash
# Verificar que las migraciones estén aplicadas
flask db current

# Si es necesario, aplicar migraciones pendientes
flask db upgrade
```

### Fase 2: Configuración de Moneda

```sql
-- Verificar o insertar moneda NIO (Córdoba nicaragüense)
INSERT INTO moneda (codigo, nombre, simbolo, activo)
VALUES ('NIO', 'Córdoba Nicaragüense', 'C$', true)
ON CONFLICT (codigo) DO NOTHING;
```

O desde la aplicación:

```python
from coati_payroll.model import Moneda, db

# Verificar si existe
nio = Moneda.query.filter_by(codigo='NIO').first()

if not nio:
    nio = Moneda(
        codigo='NIO',
        nombre='Córdoba Nicaragüense',
        simbolo='C$',
        activo=True
    )
    db.session.add(nio)
    db.session.commit()
```

### Fase 3: Configuración de INSS (7%)

#### 3.1 Crear Deducción INSS

```python
from coati_payroll.model import Deduccion, db
from coati_payroll.enums import FormulaType

inss = Deduccion(
    codigo='INSS_LABORAL',
    nombre='INSS Laboral (7%)',
    descripcion='Aporte del empleado al Instituto Nicaragüense de Seguridad Social',
    formula_type=FormulaType.PERCENTAGE,
    formula='7',  # 7%
    es_obligatoria=True,
    prioridad=1,  # Alta prioridad - se deduce primero
    afecta_ir=True,  # Reduce la base imponible del IR
    activo=True
)

db.session.add(inss)
db.session.commit()
```

#### 3.2 Validar Fórmula INSS

```python
# Prueba rápida
from decimal import Decimal
from coati_payroll.formula_engine import FormulaEngine

engine = FormulaEngine()
context = {'salario_bruto': Decimal('25000.00')}

resultado = engine.evaluate('salario_bruto * 0.07', context)
print(f"INSS esperado: C$ 1,750.00")
print(f"INSS calculado: C$ {resultado}")

assert resultado == Decimal('1750.00'), "Error en cálculo de INSS"
```

### Fase 4: Configuración de IR (Tabla Progresiva)

#### 4.1 Crear ReglaCalculo para IR

Este es el paso más crítico. El JSON debe configurarse correctamente.

```python
from coati_payroll.model import ReglaCalculo, db
from datetime import date
import json

# Esquema JSON completo
ir_schema = {
    "meta": {
        "name": "IR Nicaragua - Método Acumulado",
        "description": "Cálculo de IR según Art. 19 numeral 6 LCT",
        "jurisdiction": "Nicaragua",
        "reference_currency": "NIO",
        "version": "2025.1",
        "legal_reference": "Ley 891 - Art. 23 LCT"
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
            "name": "deducciones_antes_impuesto_acumulado",
            "type": "decimal",
            "source": "acumulado.deducciones_antes_impuesto_acumulado",
            "description": "INSS acumulado"
        },
        {
            "name": "ir_retenido_acumulado",
            "type": "decimal",
            "source": "acumulado.impuesto_retenido_acumulado",
            "description": "IR retenido previamente"
        },
        {
            "name": "meses_trabajados",
            "type": "integer",
            "source": "acumulado.periodos_procesados",
            "description": "Meses trabajados en el año fiscal"
        }
    ],
    "steps": [
        {
            "name": "paso_1_inss_mes_actual",
            "type": "calculation",
            "description": "Calcular INSS del mes actual (7%)",
            "formula": "salario_bruto * 0.07",
            "output": "inss_mes_actual"
        },
        {
            "name": "paso_2_salario_neto_mes",
            "type": "calculation",
            "description": "Calcular salario neto del mes actual",
            "formula": "salario_bruto - inss_mes_actual",
            "output": "salario_neto_mes"
        },
        {
            "name": "paso_3_salario_neto_acumulado_total",
            "type": "calculation",
            "description": "Sumar salario neto a acumulados",
            "formula": "(salario_bruto_acumulado + salario_bruto) - (deducciones_antes_impuesto_acumulado + inss_mes_actual)",
            "output": "salario_neto_acumulado_total"
        },
        {
            "name": "paso_4_meses_totales",
            "type": "calculation",
            "description": "Total de meses incluyendo el actual",
            "formula": "meses_trabajados + 1",
            "output": "meses_totales"
        },
        {
            "name": "paso_5_promedio_mensual",
            "type": "calculation",
            "description": "Calcular promedio mensual de salario neto",
            "formula": "salario_neto_acumulado_total / meses_totales",
            "output": "promedio_mensual"
        },
        {
            "name": "paso_6_expectativa_anual",
            "type": "calculation",
            "description": "Proyectar expectativa anual basada en promedio",
            "formula": "promedio_mensual * 12",
            "output": "expectativa_anual"
        },
        {
            "name": "paso_7_ir_anual",
            "type": "tax_lookup",
            "description": "Aplicar tabla progresiva de IR",
            "table": "tabla_ir_nicaragua",
            "input": "expectativa_anual",
            "output": "ir_anual"
        },
        {
            "name": "paso_8_ir_proporcional",
            "type": "calculation",
            "description": "Calcular IR proporcional a meses trabajados",
            "formula": "(ir_anual / 12) * meses_totales",
            "output": "ir_proporcional"
        },
        {
            "name": "paso_9_ir_mes_actual",
            "type": "calculation",
            "description": "Restar retenciones previas para obtener IR del mes",
            "formula": "max(ir_proporcional - ir_retenido_acumulado, 0)",
            "output": "ir_mes_actual"
        }
    ],
    "tabla_ir_nicaragua": {
        "type": "progressive",
        "brackets": [
            {
                "min": 0,
                "max": 100000,
                "rate": 0.0,
                "fixed": 0,
                "description": "Exento"
            },
            {
                "min": 100000,
                "max": 200000,
                "rate": 0.15,
                "fixed": 0,
                "over": 100000,
                "description": "15% sobre exceso de C$ 100,000"
            },
            {
                "min": 200000,
                "max": 350000,
                "rate": 0.20,
                "fixed": 15000,
                "over": 200000,
                "description": "C$ 15,000 + 20% sobre exceso de C$ 200,000"
            },
            {
                "min": 350000,
                "max": 500000,
                "rate": 0.25,
                "fixed": 45000,
                "over": 350000,
                "description": "C$ 45,000 + 25% sobre exceso de C$ 350,000"
            },
            {
                "min": 500000,
                "max": null,
                "rate": 0.30,
                "fixed": 82500,
                "over": 500000,
                "description": "C$ 82,500 + 30% sobre exceso de C$ 500,000"
            }
        ]
    }
}

# Crear la regla
regla_ir = ReglaCalculo(
    codigo='IR_NICARAGUA_2025',
    nombre='Impuesto sobre la Renta Nicaragua',
    version='2025.1',
    descripcion='Tarifa progresiva del IR según Ley No 891, método acumulado',
    jurisdiccion='Nicaragua',
    tipo_regla='impuesto',
    schema=json.dumps(ir_schema),
    vigente_desde=date(2025, 1, 1),
    vigente_hasta=None,
    activo=True
)

db.session.add(regla_ir)
db.session.commit()

print(f"ReglaCalculo creada: ID={regla_ir.id}")
```

#### 4.2 Crear Deducción IR

```python
from coati_payroll.model import Deduccion, ReglaCalculo, db
from coati_payroll.enums import FormulaType

# Obtener la regla recién creada
regla_ir = ReglaCalculo.query.filter_by(codigo='IR_NICARAGUA_2025').first()

if not regla_ir:
    raise ValueError("ReglaCalculo IR_NICARAGUA_2025 no encontrada")

# Crear deducción
deduccion_ir = Deduccion(
    codigo='IR_NICARAGUA',
    nombre='Impuesto sobre la Renta',
    descripcion='Retención de IR según tabla progresiva de Nicaragua',
    formula_type=FormulaType.REGLA_CALCULO,
    regla_calculo_id=regla_ir.id,
    es_obligatoria=True,
    prioridad=10,  # Se aplica DESPUÉS del INSS
    afecta_ir=False,  # El IR no se auto-afecta
    activo=True
)

db.session.add(deduccion_ir)
db.session.commit()

print(f"Deducción IR creada: ID={deduccion_ir.id}")
```

### Fase 5: Configuración de Planilla

#### 5.1 Crear TipoPlanilla

```python
from coati_payroll.model import TipoPlanilla, db

tipo_planilla_mensual = TipoPlanilla(
    codigo='MENSUAL_NIC',
    nombre='Planilla Mensual Nicaragua',
    descripcion='Planilla mensual para empleados en Nicaragua',
    periodo='mensual',
    mes_inicio_fiscal=1,  # Enero
    activo=True
)

db.session.add(tipo_planilla_mensual)
db.session.commit()
```

#### 5.2 Crear Planilla

```python
from coati_payroll.model import Planilla, Empresa, TipoPlanilla, Moneda, db
from datetime import date

# Obtener referencias
empresa = Empresa.query.first()  # O la empresa específica
tipo_planilla = TipoPlanilla.query.filter_by(codigo='MENSUAL_NIC').first()
moneda_nio = Moneda.query.filter_by(codigo='NIO').first()

planilla = Planilla(
    codigo='PLANILLA_NIC_2025',
    nombre='Planilla Nicaragua 2025',
    empresa_id=empresa.id,
    tipo_planilla_id=tipo_planilla.id,
    moneda_id=moneda_nio.id,
    fecha_inicio=date(2025, 1, 1),
    fecha_fin=date(2025, 12, 31),
    activo=True
)

db.session.add(planilla)
db.session.commit()
```

#### 5.3 Asociar Deducciones a Planilla

```python
from coati_payroll.model import PlanillaDeduccion, Planilla, Deduccion, db

planilla = Planilla.query.filter_by(codigo='PLANILLA_NIC_2025').first()
inss = Deduccion.query.filter_by(codigo='INSS_LABORAL').first()
ir = Deduccion.query.filter_by(codigo='IR_NICARAGUA').first()

# Asociar INSS
planilla_inss = PlanillaDeduccion(
    planilla_id=planilla.id,
    deduccion_id=inss.id,
    es_obligatoria=True,
    activo=True
)

# Asociar IR
planilla_ir = PlanillaDeduccion(
    planilla_id=planilla.id,
    deduccion_id=ir.id,
    es_obligatoria=True,
    activo=True
)

db.session.add_all([planilla_inss, planilla_ir])
db.session.commit()

print("Deducciones asociadas a planilla exitosamente")
```

### Fase 6: Configuración de Empleados

#### 6.1 Crear Empleado de Prueba

```python
from coati_payroll.model import Empleado, Empresa, db
from decimal import Decimal
from datetime import date

empresa = Empresa.query.first()

empleado = Empleado(
    codigo='EMP-001',
    nombre='Juan',
    segundo_nombre='Carlos',
    apellido='Pérez',
    segundo_apellido='García',
    numero_identificacion='001-010180-0001X',
    email='juan.perez@example.com',
    empresa_id=empresa.id,
    salario_base=Decimal('25000.00'),  # C$ 25,000 mensuales
    tipo_salario='mensual',
    fecha_ingreso=date(2025, 1, 1),
    activo=True
)

db.session.add(empleado)
db.session.commit()

print(f"Empleado creado: ID={empleado.id}, Salario=C$ {empleado.salario_base}")
```

#### 6.2 Asociar Empleado a Planilla

```python
from coati_payroll.model import PlanillaEmpleado, Planilla, Empleado, db

planilla = Planilla.query.filter_by(codigo='PLANILLA_NIC_2025').first()
empleado = Empleado.query.filter_by(codigo='EMP-001').first()

planilla_empleado = PlanillaEmpleado(
    planilla_id=planilla.id,
    empleado_id=empleado.id,
    activo=True
)

db.session.add(planilla_empleado)
db.session.commit()

print("Empleado asociado a planilla")
```

### Fase 7: Ejecución de Nómina

#### 7.1 Ejecutar Primera Nómina (Mes 1)

```python
from coati_payroll.model import Planilla, Usuario, db
from coati_payroll.nomina_engine import NominaEngine
from datetime import date

# Obtener planilla y usuario
planilla = Planilla.query.filter_by(codigo='PLANILLA_NIC_2025').first()
usuario = Usuario.query.first()  # O el usuario actual

# Crear instancia del motor de nómina
engine = NominaEngine()

# Ejecutar nómina para enero 2025
nomina = engine.ejecutar(
    planilla=planilla,
    periodo_inicio=date(2025, 1, 1),
    periodo_fin=date(2025, 1, 31),
    fecha_pago=date(2025, 2, 5),
    usuario=usuario,
    descripcion='Nómina Enero 2025'
)

db.session.commit()

print(f"Nómina ejecutada: ID={nomina.id}")
print(f"Empleados procesados: {nomina.empleados_procesados}")
print(f"Total neto: C$ {nomina.total_neto}")
```

#### 7.2 Verificar Resultados

```python
from coati_payroll.model import NominaEmpleado, NominaDetalle, AcumuladoAnual

# Obtener el registro de nómina del empleado
nomina_empleado = NominaEmpleado.query.filter_by(
    nomina_id=nomina.id,
    empleado_id=empleado.id
).first()

print(f"\n=== Resultados Mes 1 ===")
print(f"Salario Bruto: C$ {nomina_empleado.salario_bruto}")
print(f"Total Deducciones: C$ {nomina_empleado.total_deducciones}")
print(f"Salario Neto: C$ {nomina_empleado.salario_neto}")

# Ver detalle de deducciones
detalles = NominaDetalle.query.filter_by(
    nomina_empleado_id=nomina_empleado.id
).all()

for detalle in detalles:
    if detalle.deduccion:
        print(f"  - {detalle.deduccion.nombre}: C$ {detalle.monto}")

# Verificar acumulado anual
acumulado = AcumuladoAnual.query.filter_by(
    empleado_id=empleado.id,
    anio_fiscal=2025
).first()

print(f"\n=== Valores Acumulados ===")
print(f"Salario Bruto Acumulado: C$ {acumulado.salario_bruto_acumulado}")
print(f"Deducciones Pre-IR Acumuladas: C$ {acumulado.deducciones_antes_impuesto_acumulado}")
print(f"IR Retenido Acumulado: C$ {acumulado.impuesto_retenido_acumulado}")
print(f"Períodos Procesados: {acumulado.periodos_procesados}")
```

#### 7.3 Ejecutar Segunda Nómina (Mes 2)

```python
# Ejecutar nómina para febrero 2025
nomina_mes2 = engine.ejecutar(
    planilla=planilla,
    periodo_inicio=date(2025, 2, 1),
    periodo_fin=date(2025, 2, 28),
    fecha_pago=date(2025, 3, 5),
    usuario=usuario,
    descripcion='Nómina Febrero 2025'
)

db.session.commit()

# Verificar que el IR se ajustó correctamente
nomina_empleado_mes2 = NominaEmpleado.query.filter_by(
    nomina_id=nomina_mes2.id,
    empleado_id=empleado.id
).first()

acumulado_mes2 = AcumuladoAnual.query.filter_by(
    empleado_id=empleado.id,
    anio_fiscal=2025
).first()

print(f"\n=== Resultados Mes 2 ===")
print(f"Salario Neto: C$ {nomina_empleado_mes2.salario_neto}")
print(f"Períodos Procesados: {acumulado_mes2.periodos_procesados}")
print(f"IR Acumulado: C$ {acumulado_mes2.impuesto_retenido_acumulado}")
```

---

## Configuración de ReglaCalculo

### Estructura del Schema JSON

El schema JSON de `ReglaCalculo` tiene tres secciones principales:

#### 1. Metadatos (`meta`)

```json
{
  "meta": {
    "name": "Nombre descriptivo",
    "description": "Descripción técnica",
    "jurisdiction": "Nicaragua",
    "reference_currency": "NIO",
    "version": "2025.1",
    "legal_reference": "Ley 891 - Art. 23"
  }
}
```

#### 2. Entradas (`inputs`)

Define las variables que se inyectarán desde la base de datos:

```json
{
  "inputs": [
    {
      "name": "nombre_variable",
      "type": "decimal|integer|string|boolean",
      "source": "ruta.campo.base_datos",
      "description": "Descripción"
    }
  ]
}
```

**Fuentes disponibles (`source`):**

| Source | Descripción | Ejemplo |
|--------|-------------|---------|
| `empleado.salario_base` | Salario base del empleado | `25000.00` |
| `empleado.salario_hora` | Salario por hora | `104.17` |
| `acumulado.salario_bruto_acumulado` | Salario bruto acumulado | `50000.00` |
| `acumulado.deducciones_antes_impuesto_acumulado` | Deducciones pre-IR acumuladas | `3500.00` |
| `acumulado.impuesto_retenido_acumulado` | IR acumulado | `5133.34` |
| `acumulado.periodos_procesados` | Meses procesados | `2` |
| `nomina.periodo_dias` | Días del período | `30` |
| `novedad.monto` | Monto de novedad | `5000.00` |

#### 3. Pasos (`steps`)

Define los cálculos a realizar en secuencia:

```json
{
  "steps": [
    {
      "name": "identificador_unico",
      "type": "calculation|tax_lookup|conditional",
      "description": "Descripción del paso",
      "formula": "expresion_matematica",
      "output": "nombre_variable_resultado"
    }
  ]
}
```

**Tipos de pasos:**

- `calculation`: Evalúa una fórmula matemática
- `tax_lookup`: Busca en tabla de impuestos progresivos
- `conditional`: Evalúa condición if/else

### Variables Disponibles en Fórmulas

Dentro de las fórmulas de `steps`, puedes usar:

1. **Variables de `inputs`**: Por su `name`
2. **Outputs de pasos previos**: Por su `output`
3. **Funciones matemáticas**: `max()`, `min()`, `abs()`, `round()`
4. **Operadores**: `+`, `-`, `*`, `/`, `%`, `**`
5. **Comparaciones**: `>`, `<`, `>=`, `<=`, `==`, `!=`
6. **Lógicos**: `and`, `or`, `not`

### Tabla de Impuestos Progresivos

```json
{
  "tabla_nombre": {
    "type": "progressive",
    "brackets": [
      {
        "min": 0,
        "max": 100000,
        "rate": 0.0,
        "fixed": 0,
        "over": null
      },
      {
        "min": 100000,
        "max": 200000,
        "rate": 0.15,
        "fixed": 0,
        "over": 100000
      }
    ]
  }
}
```

**Fórmula del bracket:**
```
impuesto = fixed + (monto - over) * rate
```

---

## Validación y Pruebas

### Prueba Unitaria con Utilidad Reusable

El sistema incluye una utilidad de prueba en `coati_payroll/utils/locales/nicaragua.py`:

```python
from coati_payroll.utils.locales.nicaragua import ejecutar_test_nomina_nicaragua

# Definir datos de prueba
test_data = {
    "employee": {
        "codigo": "EMP-TEST-001",
        "nombre": "María",
        "apellido": "López",
        "salario_base": 30000.00
    },
    "fiscal_year_start": "2025-01-01",
    "months": [
        {
            "month": 1,
            "salario_ordinario": 30000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 2100.00,  # 30000 * 0.07
            "expected_ir": 3400.00     # Según tabla progresiva
        },
        {
            "month": 2,
            "salario_ordinario": 30000.00,
            "salario_ocasional": 5000.00,  # Bono
            "expected_inss": 2450.00,  # 35000 * 0.07
            "expected_ir": 4500.00     # Ajustado por bono
        }
    ]
}

# Ejecutar prueba
results = ejecutar_test_nomina_nicaragua(
    test_data=test_data,
    db_session=db.session,
    app=app,
    verbose=True
)

# Verificar resultados
if results["success"]:
    print("✅ Todas las pruebas pasaron")
    print(f"Meses procesados: {results['months_processed']}")
    print(f"Acumulados finales:")
    print(f"  - Bruto: C$ {results['final_accumulated']['salario_bruto_acumulado']}")
    print(f"  - INSS: C$ {results['final_accumulated']['deducciones_antes_impuesto_acumulado']}")
    print(f"  - IR: C$ {results['final_accumulated']['impuesto_retenido_acumulado']}")
else:
    print("❌ Pruebas fallidas")
    for error in results["errors"]:
        print(f"  - {error}")
```

### Casos de Prueba Recomendados

#### Caso 1: Salario Bajo (Exento de IR)

```python
test_exento = {
    "employee": {"codigo": "EMP-LOW", "nombre": "Pedro", "apellido": "Sánchez", "salario_base": 8000.00},
    "fiscal_year_start": "2025-01-01",
    "months": [
        {"month": 1, "salario_ordinario": 8000.00, "salario_ocasional": 0.00,
         "expected_inss": 560.00, "expected_ir": 0.00},  # Exento (< C$ 100k anual)
        {"month": 2, "salario_ordinario": 8000.00, "salario_ocasional": 0.00,
         "expected_inss": 560.00, "expected_ir": 0.00}
    ]
}
```

#### Caso 2: Salario Variable

```python
test_variable = {
    "employee": {"codigo": "EMP-VAR", "nombre": "Ana", "apellido": "Martínez", "salario_base": 25000.00},
    "fiscal_year_start": "2025-01-01",
    "months": [
        {"month": 1, "salario_ordinario": 25000.00, "salario_ocasional": 0.00,
         "expected_inss": 1750.00, "expected_ir": 2566.67},
        {"month": 2, "salario_ordinario": 30000.00, "salario_ocasional": 0.00,
         "expected_inss": 2100.00, "expected_ir": 3496.66},  # Ajusta por promedio
        {"month": 3, "salario_ordinario": 28000.00, "salario_ocasional": 0.00,
         "expected_inss": 1960.00, "expected_ir": 3124.67}   # Ajusta nuevamente
    ]
}
```

#### Caso 3: Salario Alto (Tramo Máximo)

```python
test_alto = {
    "employee": {"codigo": "EMP-HIGH", "nombre": "Carlos", "apellido": "Rodríguez", "salario_base": 50000.00},
    "fiscal_year_start": "2025-01-01",
    "months": [
        {"month": 1, "salario_ordinario": 50000.00, "salario_ocasional": 0.00,
         "expected_inss": 3500.00, "expected_ir": 8325.00}  # Tramo 30%
    ]
}
```

### Validación Manual

#### Verificar INSS

```python
from decimal import Decimal

salario_bruto = Decimal('25000.00')
inss_esperado = salario_bruto * Decimal('0.07')

print(f"INSS esperado: C$ {inss_esperado}")
# Debe ser: C$ 1,750.00
```

#### Verificar IR Mes 1

```python
# Mes 1: Salario C$ 25,000
salario_bruto = Decimal('25000.00')
inss = salario_bruto * Decimal('0.07')  # C$ 1,750
salario_neto = salario_bruto - inss      # C$ 23,250
expectativa_anual = salario_neto * 12    # C$ 279,000

# Aplicar tabla progresiva:
# C$ 279,000 cae en tramo 3: C$ 200,000 - 350,000
# Impuesto base: C$ 15,000
# Tasa marginal: 20% sobre exceso de C$ 200,000
ir_anual = Decimal('15000') + (expectativa_anual - Decimal('200000')) * Decimal('0.20')
# ir_anual = 15,000 + (79,000 * 0.20) = 15,000 + 15,800 = C$ 30,800

ir_mensual = ir_anual / 12  # C$ 2,566.67

print(f"IR Mes 1 esperado: C$ {ir_mensual:.2f}")
# Debe ser: C$ 2,566.67
```

---

## Troubleshooting

### Problema 1: IR no se calcula correctamente

**Síntomas:**
- IR es cero cuando debería haber retención
- IR es muy alto o muy bajo

**Diagnóstico:**

```python
from coati_payroll.model import AcumuladoAnual, Empleado

empleado = Empleado.query.filter_by(codigo='EMP-001').first()
acumulado = AcumuladoAnual.query.filter_by(
    empleado_id=empleado.id,
    anio_fiscal=2025
).first()

print(f"=== Diagnóstico AcumuladoAnual ===")
print(f"Salario Bruto Acumulado: C$ {acumulado.salario_bruto_acumulado}")
print(f"Deducciones Pre-IR Acumulado: C$ {acumulado.deducciones_antes_impuesto_acumulado}")
print(f"IR Retenido Acumulado: C$ {acumulado.impuesto_retenido_acumulado}")
print(f"Períodos Procesados: {acumulado.periodos_procesados}")

# Calcular manualmente
salario_neto_acum = acumulado.salario_bruto_acumulado - acumulado.deducciones_antes_impuesto_acumulado
promedio_mensual = salario_neto_acum / acumulado.periodos_procesados
expectativa_anual = promedio_mensual * 12

print(f"\nCálculo Manual:")
print(f"Salario Neto Acumulado: C$ {salario_neto_acum}")
print(f"Promedio Mensual: C$ {promedio_mensual}")
print(f"Expectativa Anual: C$ {expectativa_anual}")
```

**Soluciones:**

1. **Verificar que INSS se está deduciendo primero**
   ```python
   inss = Deduccion.query.filter_by(codigo='INSS_LABORAL').first()
   print(f"INSS prioridad: {inss.prioridad}")  # Debe ser 1
   print(f"INSS afecta IR: {inss.afecta_ir}")  # Debe ser True
   ```

2. **Verificar que ReglaCalculo está activa**
   ```python
   regla = ReglaCalculo.query.filter_by(codigo='IR_NICARAGUA_2025').first()
   print(f"Regla activa: {regla.activo}")
   print(f"Vigente desde: {regla.vigente_desde}")
   print(f"Vigente hasta: {regla.vigente_hasta}")
   ```

3. **Verificar que los inputs están mapeados correctamente**
   ```python
   import json
   schema = json.loads(regla.schema)
   for input_def in schema['inputs']:
       print(f"{input_def['name']}: {input_def['source']}")
   ```

### Problema 2: Variables acumuladas no están disponibles

**Síntomas:**
- Error: "Variable 'salario_bruto_acumulado' not found in context"

**Solución:**

Verificar que `nomina_engine.py` está inyectando las variables:

```python
# En nomina_engine.py, línea ~500-600
# Debe existir:
if acumulado_anual:
    context['salario_bruto_acumulado'] = acumulado_anual.salario_bruto_acumulado
    context['deducciones_antes_impuesto_acumulado'] = acumulado_anual.deducciones_antes_impuesto_acumulado
    context['periodos_procesados'] = acumulado_anual.periodos_procesados
    # ...
```

Si no existe, actualizar el archivo (ver Fase 4.1).

### Problema 3: AcumuladoAnual no se está actualizando

**Síntomas:**
- `periodos_procesados` permanece en 0 o no se incrementa
- Valores acumulados no cambian

**Diagnóstico:**

```python
from coati_payroll.model import Nomina, db

# Verificar que las nóminas se están confirmando
nominas = Nomina.query.filter_by(planilla_id=planilla.id).all()
for nomina in nominas:
    print(f"Nómina {nomina.id}: Estado={nomina.estado}")
    # Debe ser 'confirmada' o 'pagada'
```

**Solución:**

Asegurarse de llamar a `db.session.commit()` después de ejecutar la nómina.

### Problema 4: Tabla progresiva no se aplica correctamente

**Síntomas:**
- IR calculado no coincide con tabla progresiva manual

**Verificación:**

```python
from coati_payroll.formula_engine import FormulaEngine
from decimal import Decimal

engine = FormulaEngine()

# Probar lookup de tabla
renta_anual = Decimal('279000.00')  # Ejemplo

# El engine debe tener acceso a la tabla
# Esto se hace normalmente dentro del contexto de ReglaCalculo
# Pero podemos probar la lógica:

if renta_anual <= 100000:
    ir = Decimal('0')
elif renta_anual <= 200000:
    ir = (renta_anual - Decimal('100000')) * Decimal('0.15')
elif renta_anual <= 350000:
    ir = Decimal('15000') + (renta_anual - Decimal('200000')) * Decimal('0.20')
elif renta_anual <= 500000:
    ir = Decimal('45000') + (renta_anual - Decimal('350000')) * Decimal('0.25')
else:
    ir = Decimal('82500') + (renta_anual - Decimal('500000')) * Decimal('0.30')

print(f"IR Anual para C$ {renta_anual}: C$ {ir}")
# Para C$ 279,000: C$ 30,800
```

---

## Casos de Uso Avanzados

### Caso 1: Ingreso Ocasional (Bono)

Según Artículo 19, numeral 2 de la LCT:

```python
# Mes 3: Empleado recibe bono de C$ 10,000

from coati_payroll.model import Novedad, db
from decimal import Decimal

# Crear novedad de bono
novedad_bono = Novedad(
    empleado_id=empleado.id,
    tipo='percepcion',
    concepto='BONO_PRODUCTIVIDAD',
    descripcion='Bono por cumplimiento de metas',
    monto=Decimal('10000.00'),
    fecha=date(2025, 3, 15),
    periodo_inicio=date(2025, 3, 1),
    periodo_fin=date(2025, 3, 31),
    activo=True
)

db.session.add(novedad_bono)
db.session.commit()

# Al ejecutar la nómina, el bono se sumará al salario ordinario
# El IR se calculará sobre la suma total según el método acumulado
```

**Efecto esperado:**
- INSS: `(salario_base + bono) * 0.07`
- IR: Se recalcula con el ingreso adicional, puede subir significativamente

### Caso 2: Incremento Salarial

Según Artículo 19, numeral 3 de la LCT:

```python
# Mes 6: Empleado recibe aumento de C$ 25,000 a C$ 30,000

empleado = Empleado.query.filter_by(codigo='EMP-001').first()
empleado.salario_base = Decimal('30000.00')
db.session.commit()

# Al ejecutar la nómina del mes 6, el método acumulado ajustará automáticamente:
# - Promedio mensual aumenta
# - Expectativa anual aumenta
# - IR se recalcula para compensar meses anteriores si es necesario
```

### Caso 3: Múltiples Empleadores

⚠️ **Importante**: El método acumulado simple (Art. 19 numeral 6) NO aplica para trabajadores con múltiples empleadores.

Para este caso, se debe usar el método del Art. 19 numeral 1 (proyección simple) y el trabajador debe presentar declaración anual.

### Caso 4: Período Incompleto

Según Artículo 19, numeral 4 de la LCT:

```python
# Empleado ingresa en Marzo (no desde Enero)

empleado_nuevo = Empleado(
    codigo='EMP-002',
    nombre='Laura',
    apellido='Gómez',
    salario_base=Decimal('20000.00'),
    fecha_ingreso=date(2025, 3, 15),  # Ingresa a mitad de año
    activo=True
)

db.session.add(empleado_nuevo)
db.session.commit()

# El método acumulado funciona igual:
# - Primer mes: promedio = salario_neto_mes / 1
# - Segundo mes: promedio = (mes1 + mes2) / 2
# - etc.
```

### Caso 5: Validación con Archivo Excel

```python
import pandas as pd
from decimal import Decimal

# Cargar archivo de validación
df = pd.read_excel('validacion_nomina_nicaragua.xlsx')

for _, row in df.iterrows():
    test_data = {
        "employee": {
            "codigo": f"EMP-{row['empleado_id']}",
            "nombre": row['nombre'],
            "apellido": row['apellido'],
            "salario_base": float(row['salario_base'])
        },
        "fiscal_year_start": "2025-01-01",
        "months": []
    }
    
    # Construir meses desde las columnas del Excel
    for mes in range(1, 13):
        if pd.notna(row[f'mes_{mes}_salario']):
            test_data["months"].append({
                "month": mes,
                "salario_ordinario": float(row[f'mes_{mes}_salario']),
                "salario_ocasional": float(row[f'mes_{mes}_bono']) if pd.notna(row[f'mes_{mes}_bono']) else 0.00,
                "expected_inss": float(row[f'mes_{mes}_inss_esperado']),
                "expected_ir": float(row[f'mes_{mes}_ir_esperado'])
            })
    
    # Ejecutar prueba
    results = ejecutar_test_nomina_nicaragua(test_data, db.session, app, verbose=False)
    
    if not results["success"]:
        print(f"❌ Falló validación para {row['nombre']} {row['apellido']}")
        for error in results["errors"]:
            print(f"   {error}")
    else:
        print(f"✅ Validación exitosa para {row['nombre']} {row['apellido']}")
```

---

## Checklist de Implementación

Usar esta checklist para verificar que la implementación está completa:

### Fase de Configuración

- [ ] Base de datos inicializada con migraciones aplicadas
- [ ] Moneda NIO (Córdoba) creada y activa
- [ ] Deducción INSS creada con:
  - [ ] Código: `INSS_LABORAL`
  - [ ] Fórmula: `7%` o `0.07`
  - [ ] Prioridad: `1`
  - [ ] `afecta_ir`: `True`
- [ ] ReglaCalculo IR creada con:
  - [ ] Código: `IR_NICARAGUA_2025`
  - [ ] Schema JSON completo con 9 pasos
  - [ ] Tabla progresiva con 5 tramos
  - [ ] Inputs mapeados a `acumulado.*`
- [ ] Deducción IR creada con:
  - [ ] Código: `IR_NICARAGUA`
  - [ ] `formula_type`: `REGLA_CALCULO`
  - [ ] `regla_calculo_id` apuntando a ReglaCalculo IR
  - [ ] Prioridad: `10` (después de INSS)

### Fase de Empleados y Planilla

- [ ] TipoPlanilla mensual creado
- [ ] Planilla creada para año fiscal
- [ ] Deducciones INSS e IR asociadas a planilla
- [ ] Empleados creados con salario_base
- [ ] Empleados asociados a planilla

### Fase de Ejecución

- [ ] Primera nómina ejecutada exitosamente
- [ ] AcumuladoAnual creado con valores iniciales
- [ ] Segunda nómina ejecutada exitosamente
- [ ] AcumuladoAnual actualizado correctamente
- [ ] IR ajustado según método acumulado

### Fase de Validación

- [ ] Pruebas con salario bajo (exento) pasan
- [ ] Pruebas con salario medio pasan
- [ ] Pruebas con salario alto pasan
- [ ] Pruebas con salario variable pasan
- [ ] Pruebas con ingreso ocasional (bono) pasan
- [ ] Validación contra archivo Excel/auditor pasa

---

## Recursos Adicionales

### Scripts de Utilidad

#### Script de Importación Masiva

```python
# import_employees_nicaragua.py
import csv
from decimal import Decimal
from coati_payroll.model import Empleado, Planilla, PlanillaEmpleado, db

def importar_empleados_csv(archivo_csv, planilla_codigo):
    """
    Importa empleados desde archivo CSV.
    
    Formato CSV:
    codigo,nombre,apellido,identificacion,email,salario_base
    EMP-001,Juan,Pérez,001-010180-0001X,juan@example.com,25000.00
    """
    planilla = Planilla.query.filter_by(codigo=planilla_codigo).first()
    
    if not planilla:
        raise ValueError(f"Planilla {planilla_codigo} no encontrada")
    
    with open(archivo_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Verificar si empleado ya existe
            empleado = Empleado.query.filter_by(codigo=row['codigo']).first()
            
            if not empleado:
                empleado = Empleado(
                    codigo=row['codigo'],
                    nombre=row['nombre'],
                    apellido=row['apellido'],
                    numero_identificacion=row['identificacion'],
                    email=row['email'],
                    empresa_id=planilla.empresa_id,
                    salario_base=Decimal(row['salario_base']),
                    tipo_salario='mensual',
                    activo=True
                )
                db.session.add(empleado)
                db.session.flush()
                
                print(f"✓ Empleado creado: {empleado.codigo} - {empleado.nombre} {empleado.apellido}")
            
            # Asociar a planilla
            planilla_empleado = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True
            )
            db.session.add(planilla_empleado)
    
    db.session.commit()
    print(f"\nImportación completa")

# Uso:
# importar_empleados_csv('empleados_nicaragua.csv', 'PLANILLA_NIC_2025')
```

#### Script de Reporte de Validación

```python
# reporte_validacion_ir.py
from coati_payroll.model import Empleado, AcumuladoAnual, NominaEmpleado, Nomina
from decimal import Decimal
import pandas as pd

def generar_reporte_ir(anio_fiscal, output_excel='reporte_ir.xlsx'):
    """
    Genera reporte de validación de IR para todos los empleados.
    """
    empleados = Empleado.query.filter_by(activo=True).all()
    
    datos = []
    
    for empleado in empleados:
        acumulado = AcumuladoAnual.query.filter_by(
            empleado_id=empleado.id,
            anio_fiscal=anio_fiscal
        ).first()
        
        if not acumulado:
            continue
        
        # Calcular valores
        salario_neto_acum = (acumulado.salario_bruto_acumulado - 
                            acumulado.deducciones_antes_impuesto_acumulado)
        promedio_mensual = salario_neto_acum / acumulado.periodos_procesados
        expectativa_anual = promedio_mensual * 12
        
        # Obtener IR acumulado
        ir_acumulado = acumulado.impuesto_retenido_acumulado
        
        datos.append({
            'Código': empleado.codigo,
            'Nombre Completo': f"{empleado.nombre} {empleado.apellido}",
            'Meses Trabajados': acumulado.periodos_procesados,
            'Salario Bruto Acumulado': float(acumulado.salario_bruto_acumulado),
            'INSS Acumulado': float(acumulado.deducciones_antes_impuesto_acumulado),
            'Salario Neto Acumulado': float(salario_neto_acum),
            'Promedio Mensual': float(promedio_mensual),
            'Expectativa Anual': float(expectativa_anual),
            'IR Retenido Acumulado': float(ir_acumulado),
            'IR Promedio Mensual': float(ir_acumulado / acumulado.periodos_procesados)
        })
    
    # Crear DataFrame y exportar
    df = pd.DataFrame(datos)
    df.to_excel(output_excel, index=False)
    
    print(f"✓ Reporte generado: {output_excel}")
    print(f"Total empleados: {len(datos)}")
    print(f"IR total retenido: C$ {df['IR Retenido Acumulado'].sum():,.2f}")

# Uso:
# generar_reporte_ir(2025, 'reporte_ir_2025.xlsx')
```

### Enlaces Útiles

- [Ley de Concertación Tributaria (Ley 822)](https://www.dgi.gob.ni)
- [Código del Trabajo de Nicaragua](https://www.mitrab.gob.ni)
- [Documentación de Coati Payroll](../index.md)
- [Guía paso a paso para usuarios](nicaragua-ir-paso-a-paso.md)

---

## Soporte y Contacto

Para preguntas técnicas sobre esta implementación:

1. Revisar la [documentación principal](../index.md)
2. Revisar el código fuente en:
   - `coati_payroll/nomina_engine.py`
   - `coati_payroll/formula_engine.py`
   - `coati_payroll/utils/locales/nicaragua.py`
3. Ejecutar pruebas de validación con datos conocidos
4. Consultar con experto local en legislación tributaria nicaragüense

---

**Última actualización**: Diciembre 2024  
**Versión**: 1.0  
**Autor**: Equipo Coati Payroll
