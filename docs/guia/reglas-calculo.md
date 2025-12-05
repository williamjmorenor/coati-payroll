# Reglas de Cálculo

Las reglas de cálculo son un componente avanzado que permite configurar cálculos complejos utilizando esquemas estructurados. Son especialmente útiles para implementar cálculos de impuestos progresivos, seguridad social y otros cálculos basados en tablas o tramos.

## ¿Qué son las Reglas de Cálculo?

Las reglas de cálculo son configuraciones que definen cómo realizar cálculos complejos basados en:

- **Tablas de tramos**: Para impuestos progresivos o cálculos escalonados
- **Límites y umbrales**: Para aplicar diferentes fórmulas según rangos
- **Tasas variables**: Para cálculos que cambian según el monto base

## Casos de Uso Comunes

### Impuesto sobre la Renta (IR)

El IR en Nicaragua es un impuesto progresivo con diferentes tramos:

```
Tramo 1: C$ 0 - 100,000 → Exento
Tramo 2: C$ 100,000 - 200,000 → 15%
Tramo 3: C$ 200,000 - 350,000 → 20%
Tramo 4: C$ 350,000+ → 25%
```

### INSS (Seguro Social)

Cálculo de aportes a la seguridad social con topes:

- Tasa laboral: 7%
- Tasa patronal: 22.5%
- Tope máximo: C$ 100,000

### Otros Usos

- Bonos escalonados por antigüedad
- Comisiones progresivas por ventas
- Descuentos por volumen
- Cualquier cálculo basado en tablas o tramos

## Componentes de una Regla de Cálculo

### Información Básica

- **Código**: Identificador único (ej: `IR_NICARAGUA`)
- **Nombre**: Nombre descriptivo (ej: "Impuesto sobre la Renta Nicaragua")
- **Versión**: Versión de la regla (permite mantener historial)
- **Descripción**: Explicación del propósito de la regla
- **Activa**: Indica si la regla está en uso

### Esquema JSON

El esquema define la estructura del cálculo. Ejemplo para IR:

```json
{
  "tipo": "tramos",
  "tramos": [
    {
      "desde": 0,
      "hasta": 100000,
      "tasa": 0,
      "base_fija": 0
    },
    {
      "desde": 100000,
      "hasta": 200000,
      "tasa": 0.15,
      "base_fija": 0
    },
    {
      "desde": 200000,
      "hasta": 350000,
      "tasa": 0.20,
      "base_fija": 15000
    },
    {
      "desde": 350000,
      "hasta": null,
      "tasa": 0.25,
      "base_fija": 45000
    }
  ]
}
```

## Crear una Regla de Cálculo

### Método 1: Formulario Manual

1. Acceda a **Configuración** → **Reglas de Cálculo**
2. Haga clic en **Nueva Regla de Cálculo**
3. Complete los campos:
   - **Código**: Use un código descriptivo único
   - **Nombre**: Nombre que verán los usuarios
   - **Descripción**: Explique el propósito y uso
   - **Esquema JSON**: Pegue o escriba el esquema
   - **Versión**: Inicie en 1
   - **Activa**: Marque para activar la regla
4. Haga clic en **Guardar**

### Método 2: Editor de Esquemas (Recomendado)

1. Acceda a **Configuración** → **Reglas de Cálculo**
2. Haga clic en **Nueva Regla de Cálculo**
3. Use el **Editor de Esquemas** visual:
   - Seleccione el tipo de esquema (tramos, tabla, fórmula)
   - Configure los parámetros usando el formulario visual
   - El sistema genera automáticamente el JSON
4. Guarde la regla

!!! tip "Ventajas del Editor Visual"
    El editor de esquemas valida automáticamente la estructura, previene errores de sintaxis y proporciona una interfaz más intuitiva.

## Tipos de Esquemas

### Esquema de Tramos

Para cálculos progresivos como impuestos:

```json
{
  "tipo": "tramos",
  "tramos": [
    {
      "desde": valor_minimo,
      "hasta": valor_maximo,
      "tasa": porcentaje_decimal,
      "base_fija": monto_fijo_base
    }
  ]
}
```

**Parámetros:**

- `desde`: Límite inferior del tramo (inclusive)
- `hasta`: Límite superior del tramo (exclusive, `null` para ilimitado)
- `tasa`: Tasa a aplicar en el tramo (como decimal: 0.15 = 15%)
- `base_fija`: Monto fijo a sumar al cálculo del tramo

### Esquema de Tabla

Para búsqueda directa de valores:

```json
{
  "tipo": "tabla",
  "filas": [
    {
      "clave": "valor_busqueda",
      "resultado": valor_retornar
    }
  ]
}
```

### Esquema de Fórmula

Para cálculos con fórmula directa:

```json
{
  "tipo": "formula",
  "formula": "monto * 0.07",
  "tope_maximo": 7000,
  "tope_minimo": 0
}
```

## Versionado de Reglas

Las reglas de cálculo soportan versionado para mantener historial:

### ¿Por qué Versionar?

- Los impuestos y contribuciones cambian con el tiempo
- Necesita mantener cálculos históricos correctos
- Permite auditar cambios en las reglas

### Crear una Nueva Versión

1. En la lista de reglas, encuentre la regla a versionar
2. Haga clic en **Copiar** o **Nueva Versión**
3. Incremente el número de versión
4. Realice los cambios necesarios en el esquema
5. Active la nueva versión
6. Desactive la versión anterior (opcional)

!!! note "Versiones Activas"
    Solo una versión de cada regla (mismo código) debe estar activa a la vez. El sistema usa la versión activa más reciente para nuevos cálculos.

## Usar Reglas en Deducciones

Para usar una regla de cálculo en una deducción:

1. Cree o edite una deducción
2. En **Fórmula**, seleccione el tipo **Regla de Cálculo**
3. Seleccione la regla de cálculo de la lista
4. Configure el origen del monto base (ej: salario bruto)
5. Guarde la deducción

El sistema aplicará automáticamente la regla al calcular la nómina.

## Validación de Esquemas

El sistema valida automáticamente los esquemas JSON:

### Errores Comunes

❌ **Sintaxis JSON inválida**
```json
{
  "tipo": "tramos"
  "tramos": []  // Falta coma
}
```

✅ **Sintaxis correcta**
```json
{
  "tipo": "tramos",
  "tramos": []
}
```

❌ **Tramos superpuestos**
```json
{
  "tramos": [
    {"desde": 0, "hasta": 100000},
    {"desde": 50000, "hasta": 150000}  // Se superpone con anterior
  ]
}
```

✅ **Tramos continuos**
```json
{
  "tramos": [
    {"desde": 0, "hasta": 100000},
    {"desde": 100000, "hasta": 150000}
  ]
}
```

## Ejemplos Completos

### Ejemplo 1: IR Nicaragua 2024

```json
{
  "tipo": "tramos",
  "descripcion": "Impuesto sobre la Renta Nicaragua 2024",
  "tramos": [
    {
      "desde": 0,
      "hasta": 100000,
      "tasa": 0,
      "base_fija": 0,
      "descripcion": "Exento"
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
      "hasta": null,
      "tasa": 0.25,
      "base_fija": 45000,
      "descripcion": "C$ 45,000 + 25% sobre exceso de C$ 350,000"
    }
  ]
}
```

### Ejemplo 2: INSS con Tope

```json
{
  "tipo": "formula",
  "descripcion": "INSS Laboral 7% con tope de C$ 100,000",
  "formula": "min(monto, 100000) * 0.07",
  "tope_maximo": 7000,
  "tope_minimo": 0
}
```

### Ejemplo 3: Bono por Antigüedad

```json
{
  "tipo": "tabla",
  "descripcion": "Bono mensual según años de antigüedad",
  "filas": [
    {"años": "0-1", "monto": 0},
    {"años": "1-3", "monto": 500},
    {"años": "3-5", "monto": 1000},
    {"años": "5-10", "monto": 2000},
    {"años": "10+", "monto": 3000}
  ]
}
```

## Mejores Prácticas

### Documentación

- Use descripciones claras y detalladas
- Incluya la fecha de vigencia en la descripción
- Documente la fuente legal o regulatoria

### Códigos

- Use códigos descriptivos: `IR_NIC_2024`, `INSS_LABORAL`
- Incluya el año en códigos de reglas que cambian frecuentemente
- Sea consistente con la nomenclatura

### Testing

- Pruebe la regla con varios montos antes de activarla
- Verifique casos límite (0, valores en fronteras de tramos)
- Compare resultados con cálculos manuales conocidos

### Mantenimiento

- Revise las reglas anualmente o cuando cambien las leyes
- Mantenga versiones históricas inactivas para auditoría
- Documente cambios entre versiones

## Solución de Problemas

### La regla no se aplica

- Verifique que la regla esté marcada como **Activa**
- Confirme que la deducción/percepción usa la regla correcta
- Revise que el monto base sea el correcto

### Resultados incorrectos

- Valide el esquema JSON con el editor visual
- Verifique que los tramos no se superpongan
- Confirme que las tasas estén en formato decimal (0.15, no 15)
- Pruebe con montos conocidos

### Error de validación

- Revise la sintaxis JSON (comas, llaves, corchetes)
- Verifique que todos los campos requeridos estén presentes
- Use el editor visual para generar esquemas válidos

## Seguridad

- Solo usuarios administrativos pueden crear o modificar reglas
- Los cambios en reglas activas pueden afectar cálculos de nómina
- Pruebe cambios en un entorno de desarrollo primero

## Soporte

Para asistencia adicional con reglas de cálculo:

- Revise las [preguntas frecuentes](../referencia/faq.md)
- Consulte el [glosario](../referencia/glosario.md) para términos específicos
- Contacte al equipo de soporte con ejemplos específicos

---

!!! info "Característica Avanzada"
    Las reglas de cálculo son una característica avanzada. Para la mayoría de los casos simples, las fórmulas directas en percepciones y deducciones son suficientes.
