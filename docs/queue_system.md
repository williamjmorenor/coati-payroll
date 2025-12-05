# Sistema de Colas de Procesos (Background Job Processing)

## Descripción General

El sistema de colas de procesos permite ejecutar tareas en segundo plano de manera concurrente y eficiente, sin bloquear la aplicación principal. Esto es esencial para operaciones de larga duración como:

- Cálculo de nóminas con cientos o miles de empleados
- Generación de reportes complejos
- Envío masivo de correos electrónicos
- Procesamiento de datos en batch

## Arquitectura

El sistema implementa dos backends con selección automática:

### 1. Dramatiq + Redis (Producción/Alta Escala)

**Características:**
- Alta performance y escalabilidad horizontal
- Workers multi-hilo y multi-proceso
- Distribución de carga entre múltiples servidores
- Reintentos automáticos con backoff exponencial

**Requisitos:**
- Redis disponible y accesible
- Variable de entorno `REDIS_URL` configurada

### 2. Huey + Filesystem (Desarrollo/Fallback)

**Características:**
- Sin dependencias externas (no requiere Redis ni base de datos)
- Persistencia en archivos del sistema
- Thread-safe para ejecución concurrente local
- Ideal para entornos pequeños o desarrollo

**Requisitos:**
- Permisos de lectura/escritura en el directorio de cola
- Variable de entorno `COATI_QUEUE_PATH` (opcional)

## Selección Automática de Backend

El sistema selecciona automáticamente el backend apropiado:

1. **Si `REDIS_URL` existe y Redis responde** → Usa Dramatiq
2. **En caso contrario** → Usa Huey con filesystem

```python
from coati_payroll.queue import get_queue_driver

# Obtiene el driver apropiado automáticamente
queue = get_queue_driver()

# O fuerza un backend específico
queue = get_queue_driver(force_backend="huey")
```

## Uso Básico

### Registrar una Tarea

```python
from coati_payroll.queue import get_queue_driver

queue = get_queue_driver()

def calculate_something(employee_id: str, value: int) -> dict:
    # Lógica de cálculo
    result = value * 2
    return {"employee_id": employee_id, "result": result}

# Registrar la tarea
calculate_task = queue.register_task(
    calculate_something,
    name="calculate_employee",
    max_retries=3,
    min_backoff=15000,  # 15 segundos
    max_backoff=3600000,  # 1 hora
)
```

### Encolar una Tarea

```python
# Encolar inmediatamente
task_id = queue.enqueue("calculate_employee", employee_id="123", value=100)

# Encolar con delay (5 minutos)
task_id = queue.enqueue("calculate_employee", employee_id="456", value=200, delay=300)
```

### Obtener Feedback del Proceso

El sistema permite obtener feedback de las tareas encoladas:

```python
# Obtener resultado de una tarea individual
result = queue.get_task_result(task_id)
print(f"Status: {result['status']}")

# Obtener feedback de múltiples tareas (x de y completadas)
task_ids = [task1, task2, task3, task4, task5]
bulk_results = queue.get_bulk_results(task_ids)
print(f"Completadas: {bulk_results['completed']} de {bulk_results['total']}")
print(f"Progreso: {bulk_results['progress_percentage']}%")
```

## Caso de Uso: Procesamiento Paralelo de Nómina

### Opción 1: Procesar todos los empleados en paralelo

```python
from coati_payroll.queue.tasks import process_payroll_parallel_task

# Encolar procesamiento paralelo
result = process_payroll_parallel_task.send(
    planilla_id="planilla_123",
    periodo_inicio="2024-01-01",
    periodo_fin="2024-01-15",
    usuario="admin"
)

# Esto encolará una tarea por cada empleado activo
# Las tareas se procesan concurrentemente por los workers
```

### Opción 2: Procesar empleados individuales

```python
from coati_payroll.queue.tasks import calculate_employee_payroll_task

# Encolar cálculo para un empleado específico
task_id = calculate_employee_payroll_task.send(
    empleado_id="emp_456",
    planilla_id="planilla_123",
    periodo_inicio="2024-01-01",
    periodo_fin="2024-01-15",
    usuario="admin"
)

# Obtener resultado cuando esté listo
result = queue.get_task_result(task_id)
if result['status'] == 'completed':
    print(f"Salario neto: {result['result']['salario_neto']}")
```

## Configuración

### Variables de Entorno

```bash
# Backend principal (Dramatiq)
REDIS_URL=redis://localhost:6379/0

# Configuración de cola
QUEUE_ENABLED=1  # 0 para deshabilitar el sistema de colas
COATI_QUEUE_PATH=/var/lib/coati/queue  # Para Huey filesystem (opcional)
```

### Permisos de Filesystem (Huey)

Cuando se usa Huey con backend filesystem, el sistema verifica automáticamente los permisos de lectura/escritura:

```python
# El sistema intentará estos directorios en orden:
# 1. /var/lib/coati/queue
# 2. ~/.local/share/coati-payroll/queue
# 3. ./.coati_queue (directorio actual)
# 4. /tmp/coati_queue (fallback)

# Para configurar un directorio personalizado:
export COATI_QUEUE_PATH=/ruta/personalizada/queue
```

**Importante:** Asegúrese de que el usuario que ejecuta la aplicación tenga permisos de lectura y escritura en el directorio seleccionado.

## Ejecución de Workers

### Dramatiq Workers

```bash
# Worker básico
dramatiq coati_payroll.queue.tasks

# Worker con configuración personalizada
dramatiq coati_payroll.queue.tasks \
    --threads 8 \
    --processes 2 \
    --queues default,priority \
    --verbose

# Worker en producción (systemd service)
dramatiq coati_payroll.queue.tasks --threads 8 --processes 4
```

### Huey Workers

```bash
# Worker básico
huey_consumer coati_payroll.queue.drivers.huey_driver.huey

# Worker con múltiples workers
huey_consumer coati_payroll.queue.drivers.huey_driver.huey \
    --workers 4 \
    --verbose

# Worker en producción
huey_consumer coati_payroll.queue.drivers.huey_driver.huey \
    --workers 8 \
    --logfile /var/log/coati/huey.log
```

## Monitoreo

### Obtener Estadísticas de la Cola

```python
from coati_payroll.queue import get_queue_driver

queue = get_queue_driver()
stats = queue.get_stats()

print(f"Driver: {stats['driver']}")
print(f"Backend: {stats['backend']}")
print(f"Tareas registradas: {stats['registered_tasks']}")

# Para Huey
if 'pending_tasks' in stats:
    print(f"Tareas pendientes: {stats['pending_tasks']}")

# Para Dramatiq
if 'queues' in stats:
    for queue_name, length in stats['queues'].items():
        print(f"Cola {queue_name}: {length} mensajes")
```

## Seguridad

### Validación de IDs

Las tareas siempre validan los IDs antes de procesarlos:

```python
def calculate_employee_payroll(empleado_id: str, planilla_id: str, ...):
    # Validación automática por el ORM
    empleado = db.session.get(Empleado, empleado_id)
    if not empleado:
        return {"success": False, "error": "Employee not found"}
    
    planilla = db.session.get(Planilla, planilla_id)
    if not planilla:
        return {"success": False, "error": "Planilla not found"}
    
    # Procesar solo si existen y son válidos
```

### Permisos de Archivos

El sistema de Huey verifica automáticamente los permisos antes de inicializar:

- Crea directorios con permisos apropiados
- Valida capacidad de lectura/escritura
- Registra advertencias si usa directorios temporales
- Limpia archivos de prueba automáticamente

### Ubicación de Archivos

Por seguridad, los archivos de cola de Huey se almacenan:

1. **Preferentemente** en `/var/lib/coati/queue` (fuera del directorio público)
2. **Alternativamente** en `~/.local/share/coati-payroll/queue` (usuario actual)
3. **Fallback** en directorio temporal con advertencia

## Escalabilidad

### Dramatiq (Alta Escala)

- **Escalado Horizontal**: Agregar más workers conectados al mismo Redis
- **Múltiples Procesos**: Usar `--processes` para aprovechar múltiples CPUs
- **Múltiples Threads**: Usar `--threads` para I/O concurrente
- **Múltiples Colas**: Separar tareas por prioridad

Ejemplo: 1000 empleados procesados en ~30 segundos con 4 workers de 8 threads

### Huey (Escala Local)

- **Múltiples Workers**: Usar `--workers` para procesamiento concurrente
- **Thread-safe**: Soporta ejecución multi-thread segura
- **Limitación**: Solo escala dentro de un servidor (no distribuido)

Ejemplo: 100 empleados procesados en ~10 segundos con 4 workers

## Troubleshooting

### Redis no disponible

```
WARNING: Failed to connect to Redis for Dramatiq: [Errno 111] Connection refused
INFO: Using Huey driver with filesystem backend
```

**Solución**: El sistema automáticamente cambia a Huey. Para usar Dramatiq, asegúrese de que Redis esté corriendo.

### Permisos insuficientes (Huey)

```
ERROR: Insufficient permissions for queue storage at /var/lib/coati/queue
WARNING: Using temporary directory for queue storage: /tmp/coati_queue
```

**Solución**: Asegúrese de que el usuario tenga permisos en el directorio, o configure `COATI_QUEUE_PATH` a un directorio accesible.

### Tareas no se procesan

1. Verifique que los workers estén corriendo
2. Revise los logs de los workers
3. Verifique las estadísticas de la cola
4. Para Dramatiq, verifique la conexión a Redis
5. Para Huey, verifique permisos del directorio de cola

## Ejemplos Completos

Ver `/tests/test_queue.py` para ejemplos completos de uso y testing.
