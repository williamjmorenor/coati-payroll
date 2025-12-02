# Coati Payroll

Bienvenido a la documentación oficial de **Coati Payroll**, un sistema de administración de nóminas y planillas desarrollado por BMO Soluciones, S.A.

## ¿Qué es Coati Payroll?

Coati Payroll es una aplicación web diseñada para facilitar la gestión completa del proceso de nómina de una empresa. El sistema permite:

- **Gestión de Empleados**: Registro y administración completa de la información del personal.
- **Configuración de Conceptos de Nómina**: Percepciones (ingresos), deducciones y prestaciones patronales.
- **Planillas Flexibles**: Configuración de diferentes tipos de planilla (mensual, quincenal, semanal).
- **Cálculo Automático**: Motor de cálculo que procesa automáticamente salarios, deducciones e impuestos.
- **Préstamos y Adelantos**: Control de préstamos a empleados con deducción automática de cuotas.
- **Multi-moneda**: Soporte para múltiples monedas con tipos de cambio configurables.

## Características Principales

### 📋 Gestión de Planillas

Las planillas son el elemento central del sistema. Una planilla conecta:

- Empleados asignados
- Percepciones (ingresos adicionales al salario)
- Deducciones (descuentos del salario)
- Prestaciones (aportes patronales)
- Reglas de cálculo (impuestos, seguridad social)

### 💰 Cálculo de Nómina

El motor de nómina procesa automáticamente:

1. **Percepciones**: Se suman al salario base (bonos, comisiones, horas extras)
2. **Deducciones**: Se restan del salario bruto en orden de prioridad
3. **Prestaciones**: Costos patronales que no afectan el salario neto del empleado

### 🔄 Deducción Automática de Préstamos

El sistema deduce automáticamente:

- Cuotas de préstamos aprobados
- Adelantos salariales pendientes

La prioridad de estas deducciones es configurable por planilla.

## Comenzando

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } __Instalación__

    ---

    Aprende a instalar y configurar Coati Payroll en tu servidor.

    [:octicons-arrow-right-24: Guía de Instalación](instalacion/instalacion.md)

-   :material-rocket-launch:{ .lg .middle } __Primeros Pasos__

    ---

    Configura tu primera planilla y ejecuta tu primera nómina.

    [:octicons-arrow-right-24: Primeros Pasos](guia/primeros-pasos.md)

-   :material-school:{ .lg .middle } __Tutorial Completo__

    ---

    Sigue el tutorial paso a paso para configurar una nómina completa.

    [:octicons-arrow-right-24: Tutorial](tutorial/nomina-completa.md)

-   :material-help-circle:{ .lg .middle } __Preguntas Frecuentes__

    ---

    Encuentra respuestas a las preguntas más comunes.

    [:octicons-arrow-right-24: FAQ](referencia/faq.md)

</div>

## Estructura del Sistema

El siguiente diagrama muestra cómo se relacionan los componentes principales del sistema:

```mermaid
graph TD
    A[Empleados] --> B[Planilla]
    C[Percepciones] --> B
    D[Deducciones] --> B
    E[Prestaciones] --> B
    F[Reglas de Cálculo] --> B
    B --> G[Nómina]
    H[Préstamos/Adelantos] --> G
    G --> I[Detalle por Empleado]
    J[Novedades] --> G
```

### Flujo de Trabajo de Nómina

```mermaid
graph LR
    A[Ejecutar Nómina] --> B[Agregar Novedades]
    B --> C[Recalcular si es necesario]
    C --> D[Revisar y Aprobar]
    D --> E[Aplicar/Pagar]
```

## Licencia

Coati Payroll está licenciado bajo la [Licencia Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Soporte

Para reportar problemas o solicitar nuevas funcionalidades, por favor visite el [repositorio en GitHub](https://github.com/williamjmorenor/coati).
