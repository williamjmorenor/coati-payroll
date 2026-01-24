# Guías Locales de Implementación

**IMPORTANTE**: Las guías de implementación específicas de cada país han sido movidas a sus respectivos plugins para mantener el motor de nómina agnóstico a cualquier jurisdicción.

## Sistema de Plugins

Coati Payroll sigue un principio fundamental: **el motor de nómina debe ser agnóstico a cualquier jurisdicción**. Todo código, documentación y herramientas específicas de un país deben residir en plugins instalables separados.

## Plugins Disponibles

### 🇳🇮 Nicaragua

La implementación específica para Nicaragua (cálculos de INSS e IR, documentación técnica, scripts de validación) está disponible en el plugin:

**[coati-payroll-plugin-nicaragua](../../coati-payroll-plugin-nicaragua/)**

El plugin incluye:
- Cálculos de INSS (7%) e IR (progresivo con método acumulado)
- Documentación técnica completa:
  - `nicaragua.md` - Guía de implementación completa
  - `nicaragua-ir-paso-a-paso.md` - Guía educativa del cálculo de IR
  - `nicaragua-implementacion-tecnica.md` - Detalles técnicos
- Scripts de validación y pruebas
- Tests de integración

Para más información, ver:
- [README del plugin Nicaragua](../../coati-payroll-plugin-nicaragua/README.md)
- Documentación en `coati-payroll-plugin-nicaragua/docs/`

## Instalación de Plugins

Para instalar y usar un plugin:

```bash
# Instalar el plugin
pip install ./coati-payroll-plugin-nicaragua

# Reiniciar la aplicación
# El plugin aparecerá en /plugins/

# Inicializar el plugin (carga catálogos)
payrollctl plugins nicaragua init

# Activar desde CLI o interfaz web
# El elemento del menú aparecerá después de la activación
```

## Crear tu Propio Plugin

Si necesitas implementar Coati Payroll para otra jurisdicción, **crea un plugin** en lugar de modificar el motor principal.

Consulta la guía completa de desarrollo de plugins:
- **[Guía de Desarrollo de Plugins](../guia/plugins.md)**

Esta guía explica:
1. Estructura del plugin
2. Funciones requeridas (`register_blueprints`, `init`, `update`)
3. Cómo empaquetar para pip
4. Cómo registrar el plugin en el sistema
5. Ejemplos completos paso a paso

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
