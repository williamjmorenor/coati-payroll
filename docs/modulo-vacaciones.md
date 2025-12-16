# Módulo de Vacaciones - Documentación Técnica

## Descripción General

El **Módulo de Vacaciones** de Coati Payroll es un subsistema robusto, auditable y agnóstico al país, diseñado para gestionar el control completo de vacaciones de empleados. Este módulo está basado en principios de sistemas enterprise HRIS/Payroll y puede adaptarse a las regulaciones de cualquier país de América (LATAM, USA y Canadá).

## Principios de Diseño

El módulo se basa en los siguientes principios fundamentales:

1. **Vacaciones no son días, son un balance**: Las vacaciones se gestionan como un balance contable que aumenta (acumulación) y disminuye (uso).

2. **El balance se modifica solo por eventos**: Todas las modificaciones al balance se realizan mediante eventos registrados en el libro mayor (ledger).

3. **Las reglas no viven en código, viven en configuración**: Las políticas de vacaciones son configurables y no requieren cambios en el código para adaptarse a diferentes legislaciones.

4. **El sistema no decide legalidad, solo ejecuta políticas**: El sistema ejecuta políticas configuradas; la interpretación legal es responsabilidad del usuario.

5. **El motor debe ser determinista y reproducible**: Dado el mismo conjunto de eventos, el sistema siempre produce el mismo balance.

6. **Toda mutación debe dejar trazabilidad**: Cada cambio en el balance deja un registro inmutable en el ledger.

## Arquitectura del Sistema

```
Employee
  └── VacationAccount (per policy)
         ├── current_balance
         ├── policy_id
         └── VacationLedger[] (immutable audit trail)
                ├── ACCRUAL (earned)
                ├── USAGE (taken)
                ├── ADJUSTMENT (manual)
                ├── EXPIRATION (expired)
                └── PAYOUT (paid out)
```

## Entidades del Modelo

### 1. VacationPolicy (Política de Vacaciones)

Define cómo se acumulan, usan y vencen las vacaciones. Es completamente configurable por planilla (nómina) o empresa.

**IMPORTANTE**: Las políticas se asocian principalmente a **Planillas (nóminas)**, no solo a empresas. Esto permite que una instalación tenga múltiples planillas con distintas reglas de vacaciones, incluso para distintos países en consolidados de empresas.

**Campos Principales:**

#### Identificación
- `codigo`: Código único de la política
- `nombre`: Nombre descriptivo
- `descripcion`: Descripción detallada
- `planilla_id`: Planilla asociada (recomendado, permite políticas específicas por nómina/país)
- `empresa_id`: Empresa asociada (opcional, para políticas globales que aplican a toda la empresa)

#### Configuración de Acumulación
- `accrual_method`: Método de acumulación
  - `periodic`: Cantidad fija por período
  - `proportional`: Basado en días/horas trabajadas
  - `seniority`: Escalonado por antigüedad
- `accrual_rate`: Tasa de acumulación (cantidad por período)
- `accrual_frequency`: Frecuencia de acumulación
  - `monthly`: Mensual
  - `biweekly`: Quincenal
  - `annual`: Anual
- `accrual_basis`: Base para cálculo proporcional
  - `days_worked`: Días trabajados
  - `hours_worked`: Horas trabajadas
- `min_service_days`: Días mínimos de servicio antes de acumular
- `seniority_tiers`: Niveles por antigüedad (JSON)

#### Límites de Balance
- `max_balance`: Balance máximo permitido
- `carryover_limit`: Máximo que puede traspasar al siguiente período
- `allow_negative`: Permitir balance negativo (vacaciones adelantadas)

#### Reglas de Vencimiento
- `expiration_rule`: Cuándo vencen las vacaciones
  - `never`: Nunca vencen
  - `fiscal_year_end`: Al fin del año fiscal
  - `anniversary`: En el aniversario del empleado
  - `custom_date`: Fecha personalizada
- `expiration_months`: Meses después de acumulación antes de vencer
- `expiration_date`: Fecha personalizada de vencimiento

#### Configuración de Uso
- `unit_type`: Tipo de unidad
  - `days`: Días
  - `hours`: Horas
- `count_weekends`: Incluir fines de semana en el cálculo
- `count_holidays`: Incluir feriados en el cálculo
- `partial_units_allowed`: Permitir fracciones de días/horas
- `rounding_rule`: Regla de redondeo (`nearest`, `up`, `down`)
- `accrue_during_leave`: Continuar acumulando durante vacaciones
- `payout_on_termination`: Pagar vacaciones al terminar relación laboral

**Ejemplo de Configuración - Nicaragua:**
```python
policy_nicaragua = VacationPolicy(
    codigo="NIC-STANDARD",
    nombre="Política Nicaragua Estándar",
    accrual_method="periodic",
    accrual_rate=1.25,  # 15 días al año / 12 meses
    accrual_frequency="monthly",
    unit_type="days",
    count_weekends=True,
    count_holidays=True,
    payout_on_termination=True,
    expiration_rule="anniversary",
    expiration_months=12
)
```

**Ejemplo de Configuración - USA:**
```python
policy_usa = VacationPolicy(
    codigo="USA-HOURLY",
    nombre="USA Hourly Accrual",
    accrual_method="proportional",
    accrual_basis="hours_worked",
    accrual_rate=0.025,  # 1 hora por cada 40 horas trabajadas
    accrual_frequency="monthly",
    unit_type="hours",
    count_weekends=False,
    count_holidays=False,
    partial_units_allowed=True,
    allow_negative=False,
    payout_on_termination=True
)
```

**Ejemplo de Configuración - Antigüedad:**
```python
policy_seniority = VacationPolicy(
    codigo="LAT-SENIORITY",
    nombre="Política por Antigüedad LATAM",
    accrual_method="seniority",
    accrual_frequency="annual",
    unit_type="days",
    seniority_tiers=[
        {"years": 0, "rate": 10},   # 0-1 años: 10 días
        {"years": 2, "rate": 15},   # 2-5 años: 15 días
        {"years": 6, "rate": 20}    # 6+ años: 20 días
    ],
    payout_on_termination=True
)
```

### 2. VacationAccount (Cuenta de Vacaciones)

Representa el balance de vacaciones de un empleado bajo una política específica.

**Campos Principales:**
- `empleado_id`: ID del empleado
- `policy_id`: ID de la política aplicable
- `current_balance`: Balance actual (calculado desde el ledger)
- `last_accrual_date`: Fecha de la última acumulación
- `activo`: Estado de la cuenta

**Regla de Oro:** Nunca actualizar `current_balance` directamente sin registrar una entrada en `VacationLedger`.

### 3. VacationLedger (Libro Mayor de Vacaciones)

Registro inmutable de todos los movimientos de vacaciones. Es la fuente de verdad del sistema.

**Campos Principales:**
- `account_id`: ID de la cuenta
- `empleado_id`: ID del empleado (para consultas rápidas)
- `fecha`: Fecha del movimiento
- `entry_type`: Tipo de entrada
  - `accrual`: Vacaciones ganadas
  - `usage`: Vacaciones tomadas
  - `adjustment`: Ajuste manual
  - `expiration`: Vacaciones vencidas
  - `payout`: Vacaciones pagadas (al terminar)
- `quantity`: Cantidad (positiva para adiciones, negativa para deducciones)
- `source`: Origen del movimiento (`system`, `novelty`, `termination`, `manual`)
- `reference_id`: ID de referencia (ej: ID de novedad)
- `reference_type`: Tipo de referencia
- `observaciones`: Notas adicionales
- `balance_after`: Balance después de este movimiento

**Características:**
- **Inmutable**: Una vez creado, nunca se modifica o elimina
- **Auditable**: Rastrea quién, cuándo y por qué se modificó el balance
- **Determinista**: `balance = SUM(ledger.quantity)`

### 4. VacationNovelty (Novedad/Solicitud de Vacaciones)

Representa una solicitud de vacaciones que afecta el balance cuando es aprobada.

**Campos Principales:**
- `empleado_id`: ID del empleado
- `account_id`: ID de la cuenta de vacaciones
- `start_date`: Fecha de inicio
- `end_date`: Fecha de fin
- `units`: Unidades solicitadas (días/horas)
- `estado`: Estado de la solicitud
  - `pendiente`: Pendiente de aprobación
  - `aprobado`: Aprobada
  - `rechazado`: Rechazada
  - `disfrutado`: Disfrutada/completada
- `fecha_aprobacion`: Fecha de aprobación
- `aprobado_por`: Usuario que aprobó
- `ledger_entry_id`: ID de la entrada en el ledger (cuando es aprobada)
- `observaciones`: Notas
- `motivo_rechazo`: Motivo del rechazo (si aplica)

## Flujos de Trabajo

### Flujo 1: Acumulación de Vacaciones

```
1. Job programado ejecuta motor de acumulación
2. Motor evalúa política de cada cuenta activa
3. Calcula cantidad a acumular según método
4. Genera entrada en VacationLedger (type=ACCRUAL)
5. Actualiza current_balance en VacationAccount
6. Actualiza last_accrual_date
```

### Flujo 2: Solicitud y Aprobación de Vacaciones

```
1. Usuario crea VacationNovelty (estado=pendiente)
2. Sistema valida:
   - Empleado tiene cuenta activa
   - Balance suficiente (o policy.allow_negative=true)
3. Administrador revisa solicitud
4. Si aprueba:
   a. Cambia estado a 'aprobado'
   b. Genera VacationLedger (type=USAGE, quantity=-N)
   c. Actualiza current_balance
   d. Vincula ledger_entry_id
5. Si rechaza:
   a. Cambia estado a 'rechazado'
   b. Registra motivo_rechazo
```

### Flujo 3: Ajuste Manual

```
1. Administrador crea ajuste manual
2. Sistema genera VacationLedger (type=ADJUSTMENT)
3. Actualiza current_balance
4. Registra observaciones y usuario
```

### Flujo 4: Vencimiento de Vacaciones

```
1. Job programado evalúa políticas de vencimiento
2. Identifica vacaciones vencidas según expiration_rule
3. Genera VacationLedger (type=EXPIRATION, quantity=-N)
4. Actualiza current_balance
```

### Flujo 5: Pago al Terminar Relación Laboral

```
1. Empleado es dado de baja
2. Si policy.payout_on_termination=true:
   a. Genera VacationLedger (type=PAYOUT, quantity=-balance)
   b. Balance queda en 0
   c. Se integra con nómina para pago
```

## Casos de Uso Cubiertos

### ✅ LATAM (Ejemplo: Nicaragua)
- Acumulación: 15 días calendario al año
- Frecuencia: Mensual (1.25 días/mes)
- Unidad: Días calendario
- Vencimiento: 12 meses después del aniversario
- Pago al terminar: Sí

### ✅ USA
- Acumulación: Por horas trabajadas
- Frecuencia: Mensual (basado en horas del mes)
- Unidad: Horas
- Vencimiento: Fin de año fiscal
- Fracciones: Permitidas

### ✅ Canadá
- Acumulación: Porcentaje del salario
- Frecuencia: Quincenal o mensual
- Unidad: Días u horas
- Pago al terminar: Sí

### ✅ Part-Time / Empleados por Horas
- Acumulación proporcional basada en horas trabajadas
- Configuración específica por tipo de empleado

### ✅ Vacaciones Adelantadas
- Configurar `allow_negative=true` en la política
- El balance puede ser negativo
- Se descuenta en futuras acumulaciones

### ✅ Ajustes Manuales Auditables
- Todos los ajustes quedan registrados en el ledger
- Se registra usuario, fecha y motivo

## Integración con Nómina

El módulo de vacaciones **NO calcula dinero**, solo gestiona **unidades** (días/horas).

La integración con nómina se realiza mediante:

1. **Vacaciones Tomadas**: Se registran como novedades que pueden afectar el cálculo de la nómina
2. **Pago de Vacaciones al Terminar**: El evento `PAYOUT` genera una novedad que se procesa en la nómina final
3. **Provisión de Vacaciones**: Se puede configurar como prestación patronal basada en el balance acumulado

## Reportes y Consultas

### Balance por Empleado
```sql
SELECT current_balance FROM vacation_account WHERE empleado_id = ?
```

### Historial Completo
```sql
SELECT * FROM vacation_ledger 
WHERE empleado_id = ? 
ORDER BY fecha DESC
```

### Cálculo Verificable del Balance
```sql
SELECT SUM(quantity) FROM vacation_ledger WHERE account_id = ?
-- Debe ser igual a vacation_account.current_balance
```

### Vacaciones por Vencer
```sql
SELECT va.*, vp.expiration_months 
FROM vacation_account va
JOIN vacation_policy vp ON va.policy_id = vp.id
WHERE vp.expiration_rule != 'never'
  AND va.last_accrual_date < DATEADD(MONTH, -vp.expiration_months, GETDATE())
```

## Seguridad y Permisos

- **Crear/Editar Políticas**: Solo administradores
- **Ver Cuentas**: Usuarios con permisos de lectura
- **Aprobar Solicitudes**: Administradores y RRHH
- **Crear Solicitudes**: Usuarios con permisos de escritura
- **Ajustes Manuales**: Solo administradores

## Ventajas del Diseño

✅ **100% agnóstico al país**: Se adapta a cualquier legislación mediante configuración  
✅ **Auditable**: Cada cambio queda registrado  
✅ **Reversible**: Ajustes se registran, no se borran  
✅ **Extensible**: Nuevas reglas se agregan sin cambiar código  
✅ **Compatible con plugins**: Sistema de eventos permite extensiones  
✅ **No rompe nómina**: Integración limpia con el módulo de nómina  

## Riesgos Evitados

❌ Hardcodear días legales  
❌ Mezclar vacaciones con nómina  
❌ Actualizar balances directamente  
❌ No tener ledger (libro mayor)  
❌ No modelar eventos  

## Próximas Mejoras

- Motor de acumulación automático (scheduled job)
- Notificaciones de vacaciones por vencer
- Integración con calendario empresarial
- Reportes avanzados y dashboards
- API REST para integraciones externas
- Importación masiva de balances iniciales

## Conclusión

El Módulo de Vacaciones de Coati Payroll implementa un sistema robusto basado en **políticas + eventos + ledger + motor de reglas**, apto para cumplir con legislaciones de cualquier país de América sin necesidad de reescribir código.
