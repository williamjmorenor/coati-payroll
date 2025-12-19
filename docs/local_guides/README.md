# Guías Locales de Implementación

Este directorio contiene guías detalladas para implementar Coati Payroll según las legislaciones laborales y tributarias de diferentes países.

## Guías Disponibles

### 🇳🇮 Nicaragua

- **[Guía de Implementación para Nicaragua](nicaragua.md)** - Configuración completa del sistema según la legislación nicaragüense
  - Tipos de ingresos (ordinarios y extraordinarios)
  - INSS Laboral (7%)
  - IR (Impuesto sobre la Renta) con tarifa progresiva
  - Prestaciones patronales
  - Casos especiales (bonos, aumentos salariales, vacaciones)
  - Ejemplos de configuración con ReglaCalculo

- **[Cálculo del IR Nicaragua - Paso a Paso](nicaragua-ir-paso-a-paso.md)** - Guía educativa para entender el cálculo del IR
  - Explicación detallada en 5 pasos simples
  - Múltiples ejemplos prácticos con diferentes salarios
  - Tablas de tramos progresivos
  - Casos especiales (bonos, aumentos)
  - Herramientas de validación

## Cómo usar estas guías

1. **Seleccione su país**: Encuentre la guía correspondiente a su jurisdicción
2. **Lea la guía de implementación**: Siga los pasos para configurar el sistema
3. **Consulte la guía educativa**: Si necesita entender los cálculos en detalle
4. **Configure el sistema**: Use los ejemplos de configuración proporcionados
5. **Pruebe y valide**: Ejecute las pruebas recomendadas antes de usar en producción

## Contribuir

Si desea agregar una guía para otro país o mejorar las existentes:

1. Cree un archivo nuevo en este directorio (ej: `costa-rica.md`)
2. Siga la estructura de las guías existentes
3. Incluya:
   - Marco legal del país
   - Tipos de ingresos y deducciones
   - Cálculos detallados con ejemplos
   - Configuración paso a paso
   - Casos especiales
   - Herramientas de validación
4. Actualice este README con la nueva guía
5. Actualice `mkdocs.yml` para incluir la guía en la navegación

## Estructura recomendada

Cada guía debería incluir:

```markdown
# Guía de Implementación para [País]

## Introducción
- Resumen del sistema de nómina del país

## Marco Legal
- Leyes y regulaciones aplicables

## Tipos de Ingresos
- Ingresos ordinarios
- Ingresos extraordinarios
- Tratamiento fiscal

## Deducciones Obligatorias
- Seguridad social
- Impuestos sobre la renta
- Otras deducciones

## Configuración del Sistema
- Paso a paso detallado
- Ejemplos de configuración
- Código de reglas de cálculo

## Casos Especiales
- Bonos y comisiones
- Aumentos salariales
- Períodos incompletos
- Vacaciones y aguinaldo

## Pruebas y Validación
- Casos de prueba
- Herramientas de validación
- Comparación con cálculos oficiales

## Preguntas Frecuentes
- Respuestas a dudas comunes

## Recursos Adicionales
- Enlaces a leyes y regulaciones
- Contactos de entidades oficiales
- Herramientas adicionales
```

## Licencia

Estas guías son parte del proyecto Coati Payroll y están bajo la misma licencia Apache 2.0.

---

*Para más información sobre el sistema, consulte la [documentación principal](../index.md).*
