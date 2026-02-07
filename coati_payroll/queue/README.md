# Background Queue System

Sistema de colas de procesos para ejecutar tareas en segundo plano sin bloquear la aplicación principal.

## Características Principales

- ✅ **Doble Backend**: Dramatiq+Redis (producción) y Huey+Filesystem (desarrollo/fallback)
- ✅ **Selección Automática**: El sistema elige el mejor backend disponible
- ✅ **Feedback en Tiempo Real**: Seguimiento de progreso (x de y completadas)
- ✅ **Validación de Permisos**: Verificación automática de acceso a filesystem
- ✅ **Thread-Safe**: Ejecución segura con múltiples workers
- ✅ **Reintentos Automáticos**: Backoff exponencial en caso de errores
- ✅ **Seguridad**: Validación de IDs y ubicación segura de archivos
- ✅ **Idempotencia**: Bloqueo por nómina y job_id para evitar doble procesamiento

## Inicio Rápido

### 1. Instalación

Las dependencias ya están incluidas en `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Uso Básico

```python
from coati_payroll.queue import get_queue_driver

# Obtener driver (automático)
queue = get_queue_driver()

# Registrar tarea
@queue.register_task(name="mi_tarea")
def procesar_algo(datos):
    return {"resultado": datos * 2}

# Encolar tarea
task_id = queue.enqueue("mi_tarea", datos=100)

# Obtener resultado
resultado = queue.get_task_result(task_id)
```

### 3. Procesamiento Paralelo de Nómina

```python
from coati_payroll.queue.tasks import process_payroll_parallel_task

# Procesar todos los empleados en paralelo
result = process_payroll_parallel_task.send(
    planilla_id="planilla_123",
    periodo_inicio="2024-01-01",
    periodo_fin="2024-01-15",
    usuario="admin"
)

# Obtener progreso
bulk_status = queue.get_bulk_results(task_ids)
print(f"Completadas: {bulk_status['completed']} de {bulk_status['total']}")
print(f"Progreso: {bulk_status['progress_percentage']}%")
```

## Configuración

### Variables de Entorno

```bash
# Redis (para Dramatiq en producción)
export REDIS_URL=redis://localhost:6379/0

# Habilitar/deshabilitar sistema de colas
export QUEUE_ENABLED=1

# Ruta personalizada para Huey (opcional)
export COATI_QUEUE_PATH=/var/lib/coati/queue

# Evitar uso accidental del driver Noop (tests)
export COATI_ALLOW_NOOP_QUEUE=1
```

### Ejecutar Workers

**Dramatiq (producción con Redis):**
```bash
dramatiq coati_payroll.queue.tasks --threads 8 --processes 4
```

**Huey (desarrollo o sin Redis):**
```bash
huey_consumer coati_payroll.queue.drivers.huey_driver.huey --workers 4
```

> ⚠️ En producción se requiere Dramatiq+Redis. El fallback a Huey está deshabilitado.

## Estructura del Módulo

```
coati_payroll/queue/
├── __init__.py           # API pública
├── driver.py             # Interfaz abstracta
├── selector.py           # Selección automática de backend
├── tasks.py              # Tareas de ejemplo para nómina
└── drivers/
    ├── dramatiq_driver.py   # Driver Dramatiq+Redis
    └── huey_driver.py       # Driver Huey+Filesystem
```

## Documentación Completa

Para documentación detallada, ver:
- [`/docs/queue_system.md`](../../docs/queue_system.md) - Guía completa
- [`/docs/queue_example.py`](../../docs/queue_example.py) - Ejemplo ejecutable
- [`/tests/test_queue.py`](../../tests/test_queue.py) - Tests y ejemplos

## Casos de Uso

### ✅ Recomendado Para:

- Cálculo de nóminas grandes (1000+ empleados)
- Generación de reportes complejos
- Envío masivo de correos
- Procesamiento de importaciones de datos
- Cualquier operación que tarde >5 segundos

### ❌ No Recomendado Para:

- Operaciones simples que tardan <1 segundo
- Tareas que requieren respuesta inmediata al usuario
- Operaciones que modifican la sesión del usuario

## Monitoreo

```python
from coati_payroll.queue import get_queue_driver

queue = get_queue_driver()
stats = queue.get_stats()

print(f"Driver: {stats['driver']}")
print(f"Backend: {stats['backend']}")
print(f"Tareas registradas: {stats['registered_tasks']}")
```

## Troubleshooting

### Redis no disponible
En producción se bloquea el fallback a Huey. Para usar Dramatiq:
1. Instalar Redis: `apt-get install redis-server` o `brew install redis`
2. Configurar: `export REDIS_URL=redis://localhost:6379/0`
3. Iniciar: `redis-server`

### Permisos insuficientes (Huey)
Si ve advertencias sobre permisos:
1. Configure una ruta personalizada: `export COATI_QUEUE_PATH=/ruta/segura`
2. O asegure permisos en: `/var/lib/coati/queue`

### Tareas no se procesan
1. Verifique que los workers estén corriendo
2. Revise los logs: `tail -f /var/log/coati/queue.log`
3. Verifique estadísticas: `queue.get_stats()`

## Soporte

Para reportar problemas o solicitar ayuda:
- GitHub Issues: https://github.com/williamjmorenor/coati/issues
- Documentación: `/docs/queue_system.md`

## Idempotencia y Concurrencia

Invariantes del sistema:

- Solo un job activo por nómina (lock por `nomina_id` + `job_id`).
- La ejecución solo continúa si la nómina está en estado `CALCULANDO` y el `job_id` coincide.
- Los reintentos reutilizan el mismo `job_id` para evitar duplicaciones.
- El progreso se registra fuera de la transacción de cálculo para evitar mezclas con rollback.
