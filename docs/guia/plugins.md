# Sistema de Plugins

## Objetivo y regla inquebrantable

Coati Payroll debe permanecer como un motor de nómina agnóstico a cualquier jurisdicción. La adaptación a una jurisdicción específica debe residir **exclusivamente** en plugins instalables, sin modificar el código fuente del motor.

## Descubrimiento (no dinámico)

- Los plugins se detectan al iniciar la aplicación enumerando los paquetes instalados en el entorno de Python.
- El implementador debe:
  - instalar el paquete del plugin
  - reiniciar la aplicación

No existe “hot reload” de plugins.

## Nombre del paquete

El paquete instalable debe llamarse:

`coati-payroll-plugin-XXXXXXXX`

Donde `XXXXXXXX` es el identificador del plugin.

## Módulo del plugin (contrato)

Cada plugin debe exponer un módulo importable con el nombre:

`coati_payroll_plugin_XXXXXXXX`

Regla: el `XXXXXXXX` del módulo se deriva del nombre del paquete, reemplazando `-` por `_`.

Ejemplo:

- Paquete: `coati-payroll-plugin-pa`
- Módulo: `coati_payroll_plugin_pa`

## Ejemplo mínimo de estructura

Ejemplo para un plugin `coati-payroll-plugin-gt` (Guatemala):

```text
coati-payroll-plugin-gt/
  pyproject.toml
  README.md
  coati_payroll_plugin_gt.py
```

El sistema descubrirá el paquete al reiniciar la app y lo registrará en `plugin_registry`.

## Blueprint (requerido)

Un plugin debe **al menos registrar un blueprint**.

El módulo del plugin debe definir la función:

- `register_blueprints(app)`

Esta función es llamada por la aplicación principal solo si el plugin está marcado como `active` en la base de datos.

### Ejemplo: `register_blueprints(app)`

```python
from flask import Blueprint, render_template

bp = Blueprint("plugin_gt", __name__, url_prefix="/gt")


@bp.route("/")
def index():
    return render_template("gt/index.html")


def register_blueprints(app):
    app.register_blueprint(bp)
```

## Menú principal

Si un plugin está instalado y marcado como activo, el sistema agrega una entrada al menú principal mediante un simple bucle:

```jinja2
{% for active_plugin in plugin_actives %}
  <!-- add_entry_in_main_menu -->
{% endfor %}
```

El plugin debe proponer el nombre de la entrada y el ícono. Para eso debe exponer uno de:

- `get_menu_entry()` que devuelve un `dict`
- o `MENU_ENTRY` como `dict`

Formato del `dict`:

- `label`: texto a mostrar
- `icon`: clase CSS del icono (por defecto se usa `bi bi-puzzle`)
- `url`: URL absoluta o relativa dentro del sitio (por ejemplo `/mi-plugin/`)

### Ejemplo: entrada de menú

```python
def get_menu_entry():
    return {
        "label": "Guatemala",
        "icon": "bi bi-geo-alt",
        "url": "/gt/",
    }
```

## Estado activo/inactivo (persistido)

El estado del plugin se almacena en base de datos en la tabla `plugin_registry`.

Reglas al inicio:

- Si se detecta un plugin nuevo instalado, se inserta como registro en la BD con `active = false`.
- Si en un redeployment un plugin aparece como `active = true` en BD pero no está instalado, el sistema lo marca inmediatamente como `active = false`.

## Interfaz gráfica

La aplicación expone una pantalla para listar plugins detectados en el entorno, y activar/desactivar su estado.

Ruta:

- `/plugins/`

Nota: al activar/desactivar, se recomienda reiniciar la aplicación para asegurar que los blueprints se registren de forma consistente.

## CLI (crítico): `payrollctl plugins`

La CLI incluye el grupo:

- `payrollctl plugins`

Y por cada plugin instalado expone:

- `payrollctl plugins XXXXXXXX init`
- `payrollctl plugins XXXXXXXX update`

Importante: `init` y `update` no aparecen directamente bajo `payrollctl plugins`, sino bajo el subcomando del plugin.

La jerarquía real es:

- `payrollctl plugins`
- `payrollctl plugins XXXXXXXX`
  - `init`
  - `update`

### Ejemplos de `--help`

Si no hay plugins instalados en el entorno, `payrollctl plugins --help` no mostrará subcomandos de plugins.

```text
$ payrollctl plugins --help
Usage: payrollctl plugins [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  (sin plugins instalados)
```

Cuando sí hay plugins instalados (ejemplo: `coati-payroll-plugin-gt`):

```text
$ payrollctl plugins --help
Usage: payrollctl plugins [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  gt
```

Y el `--help` del plugin muestra `init` y `update`:

```text
$ payrollctl plugins gt --help
Usage: payrollctl plugins gt [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  init
  update
```

### init (función crítica)

El comando `init` es considerado **crítico** porque puede automatizar la preparación completa de una jurisdicción.

Al ejecutar `payrollctl plugins XXXXXXXX init`, el plugin puede:

- crear definiciones de deducciones
- crear definiciones de percepciones
- crear definiciones de prestaciones
- crear definiciones de planillas
- crear tablas adicionales en la base de datos
- crear definiciones de nómina (si el implementador requiere inicialización adicional)

Lo más importante: un plugin puede empaquetar **toda** la lógica de implementación de una jurisdicción, incluyendo la carga de catálogos base (percepciones, deducciones, prestaciones) y la configuración de planillas/tipos.

El módulo del plugin debe implementar:

- `init()`

Después de ejecutar `init()`, la aplicación ejecuta `db.create_all()` para crear las tablas definidas por el plugin (si el plugin definió modelos SQLAlchemy).

### Ejemplo: `init()` cargando percepciones, deducciones, prestaciones y planillas

Ejemplo orientativo (los campos exactos dependen del modelo y tu jurisdicción). La idea es que `init()` sea **idempotente**: si lo ejecutas 2 veces, no debe duplicar registros.

```python
from coati_payroll.model import db, Percepcion, Deduccion, Prestacion, TipoPlanilla, Planilla


def _upsert_by_codigo(Model, codigo: str, **kwargs):
    existing = db.session.execute(db.select(Model).filter_by(codigo=codigo)).scalar_one_or_none()
    if existing is None:
        existing = Model()
        existing.codigo = codigo
        db.session.add(existing)
    for k, v in kwargs.items():
        setattr(existing, k, v)
    return existing


def init():
    # 1) Catálogo de percepciones
    _upsert_by_codigo(
        Percepcion,
        "SAL_BASE",
        nombre="Salario Base",
        descripcion="Sueldo ordinario",
        formula_tipo="monto_fijo",
        activo=True,
    )

    # 2) Catálogo de deducciones
    _upsert_by_codigo(
        Deduccion,
        "IGSS",
        nombre="Seguro Social",
        descripcion="Aporte del trabajador",
        formula_tipo="porcentaje",
        activo=True,
    )

    # 3) Catálogo de prestaciones (aportes patronales)
    _upsert_by_codigo(
        Prestacion,
        "PATRONAL_SS",
        nombre="Aporte patronal SS",
        descripcion="Aporte del patrono",
        formula_tipo="porcentaje",
        activo=True,
    )

    # 4) Tipos de planilla
    _upsert_by_codigo(
        TipoPlanilla,
        "MENSUAL",
        nombre="Mensual",
        descripcion="Planilla mensual",
        activo=True,
    )

    # 5) Planillas base (ejemplo; ajustar a tu esquema: empresa/moneda, etc.)
    # Si tu modelo de Planilla requiere FK (empresa_id, moneda_id),
    # obtén/crea esos registros primero y pásalos aquí.
    _upsert_by_codigo(
        Planilla,
        "PL_MENSUAL",
        nombre="Planilla Mensual",
        descripcion="Planilla principal",
        activo=True,
    )

    db.session.commit()
```

### Ejemplo: crear tablas propias del plugin

Si tu plugin define modelos SQLAlchemy adicionales (tablas nuevas), simplemente impórtalos en el módulo del plugin (para que se registren en el metadata) y deja que el comando ejecute `db.create_all()`.

Ejemplo (conceptual):

```python
from coati_payroll.model import db, BaseTabla


class TablaJurisdiccion(db.Model, BaseTabla):
    __tablename__ = "gt_parametros"
    clave = db.Column(db.String(50), unique=True, nullable=False, index=True)
    valor = db.Column(db.String(200), nullable=False)
```

### update

El módulo del plugin debe implementar:

- `update()`

Se utiliza para aplicar actualizaciones de catálogo o cambios propios de la jurisdicción.

Después de ejecutar `update()`, la aplicación ejecuta `db.create_all()` para asegurar que tablas nuevas queden creadas.

### Ejemplo: `update()`

Usa `update()` para:

- agregar nuevos conceptos al catálogo
- corregir descripciones/códigos
- introducir nuevas planillas/tipos

```python
from coati_payroll.model import db, Percepcion


def update():
    p = db.session.execute(db.select(Percepcion).filter_by(codigo="SAL_BASE")).scalar_one_or_none()
    if p is not None:
        p.descripcion = "Sueldo ordinario (actualizado)"
        db.session.commit()
```

## Responsabilidad del implementador

Dentro del blueprint, el diseñador del plugin puede implementar todo lo que Python / Flask / JavaScript permitan; es responsabilidad del implementador.
