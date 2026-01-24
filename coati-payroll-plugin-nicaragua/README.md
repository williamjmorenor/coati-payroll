# Coati Payroll Plugin - Nicaragua

Plugin de Coati Payroll para implementaciones en Nicaragua. Proporciona funcionalidades específicas para el cálculo de nómina según la legislación nicaragüense.

## Descripción

Este plugin incluye:

- **Cálculos de INSS**: Deducción del 7% del Instituto Nicaragüense de Seguridad Social
- **Cálculos de IR**: Impuesto sobre la Renta progresivo con método acumulado
- **Utilidades de validación**: Scripts para validar cálculos de IR e INSS
- **Documentación técnica**: Guías de implementación específicas para Nicaragua
- **Tests de integración**: Suite completa de tests para validar los cálculos

## Instalación

### Desde el directorio del plugin

```bash
pip install .
```

### En modo desarrollo

```bash
pip install -e .
```

## Activación del Plugin

Después de instalar el plugin:

1. **Reinicia la aplicación Coati Payroll**

2. **Activa el plugin desde la interfaz web:**
   - Navega a `/plugins/`
   - Activa el plugin "Nicaragua"
   - Reinicia la aplicación nuevamente

3. **O activa desde la línea de comandos:**

```bash
# Listar plugins disponibles
payrollctl plugins

# Ver comandos disponibles para Nicaragua
payrollctl plugins nicaragua --help

# Inicializar el plugin (carga catálogos base)
payrollctl plugins nicaragua init

# Actualizar el plugin
payrollctl plugins nicaragua update
```

## Uso

Una vez activado, el plugin aparecerá en el menú principal de Coati Payroll con el nombre "Nicaragua".

### Acceso a la documentación

El plugin incluye documentación técnica accesible en:

- **Interfaz web**: `/nicaragua/documentacion`
- **Archivos locales**: Directorio `docs/` del plugin

### Utilidades incluidas

#### Función de test para nómina nicaragüense

```python
from coati_payroll_plugin_nicaragua.nicaragua import ejecutar_test_nomina_nicaragua

# Ejecutar test de nómina con datos de prueba
result = ejecutar_test_nomina_nicaragua(
    test_data=my_test_data,
    db_session=db.session,
    app=app
)
```

#### Scripts de validación

```bash
# Validar ejemplos de IR
python scripts/validar_ejemplos_nicaragua.py

# Generar reporte de validación
python scripts/reporte_validacion_nicaragua.py
```

## Estructura del Plugin

```
coati-payroll-plugin-nicaragua/
├── pyproject.toml                              # Configuración del paquete
├── README.md                                   # Este archivo
├── LICENSE                                     # Licencia Apache 2.0
├── coati_payroll_plugin_nicaragua/            # Módulo principal
│   ├── __init__.py                            # Punto de entrada del plugin
│   ├── nicaragua.py                           # Utilidades de cálculo
│   ├── validate_nicaragua_examples.py         # Validación de ejemplos
│   ├── validate_nicaragua_ir.py               # Validación de IR
│   ├── templates/                             # Plantillas HTML
│   │   └── nicaragua/
│   │       ├── index.html
│   │       └── documentacion.html
│   └── static/                                # Archivos estáticos
├── docs/                                      # Documentación técnica
│   ├── nicaragua.md
│   ├── nicaragua-implementacion-tecnica.md
│   └── nicaragua-ir-paso-a-paso.md
├── scripts/                                   # Scripts de utilidad
│   ├── validar_ejemplos_nicaragua.py
│   └── reporte_validacion_nicaragua.py
└── tests/                                     # Tests del plugin
    ├── test_nicaragua_examples.py
    ├── test_nicaragua_ir_calculation.py
    ├── test_nicaragua_json_validation.py
    └── test_nicaragua_flask_client_integration.py
```

## Configuración

### Deducciones incluidas

El comando `init` crea automáticamente:

- **INSS**: Instituto Nicaragüense de Seguridad Social (7%)
- **IR**: Impuesto sobre la Renta (progresivo con método acumulado)

### Tipos de planilla

- **MENSUAL_NI**: Planilla mensual según legislación nicaragüense

### Reglas de cálculo

El plugin proporciona una estructura base para la regla de cálculo del IR. El implementador debe configurar los valores exactos de los tramos fiscales según la legislación vigente a través de la interfaz de Coati Payroll.

## Documentación Técnica

El plugin incluye documentación completa sobre:

1. **nicaragua.md**: Guía general de implementación para Nicaragua
2. **nicaragua-implementacion-tecnica.md**: Detalles técnicos de implementación
3. **nicaragua-ir-paso-a-paso.md**: Guía paso a paso para configurar el IR

## Tests

Para ejecutar los tests del plugin:

```bash
# Instalar dependencias de desarrollo
pip install pytest

# Ejecutar todos los tests
pytest tests/

# Ejecutar un test específico
pytest tests/test_nicaragua_ir_calculation.py
```

## Requisitos

- Python >= 3.11
- Coati Payroll (core engine)
- Flask

## Compatibilidad

Este plugin es compatible con:

- Coati Payroll >= 1.0.0
- Python 3.11, 3.12

## Contrato Social

Este plugin sigue el [Contrato Social de Coati Payroll](https://github.com/williamjmorenor/coati-payroll/blob/main/SOCIAL_CONTRACT.md):

- **No incluye interpretaciones legales vinculantes**
- **No reemplaza conocimiento profesional**
- **No garantiza cumplimiento regulatorio**

El implementador es responsable de:

- Conocer la legislación nicaragüense aplicable
- Configurar correctamente los cálculos según la ley vigente
- Validar manualmente los resultados
- Mantener el sistema actualizado con cambios legales

## Licencia

Apache License 2.0 - Ver archivo [LICENSE](LICENSE) para más detalles.

## Soporte

Para reportar problemas o solicitar características:

- **Issues**: https://github.com/williamjmorenor/coati-payroll/issues
- **Documentación**: https://github.com/williamjmorenor/coati-payroll

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del repositorio
2. Crea una rama para tu característica
3. Envía un Pull Request

## Autor

**BMO Soluciones, S.A.**

---

Hecho con ❤️ para la comunidad nicaragüense
