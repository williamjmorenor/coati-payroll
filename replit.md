# Coati Payroll

Sistema de nómina ligero pero completo para el cálculo de planillas laborales con control de percepciones y deducciones.

## Overview

Sistema de gestión de nómina desarrollado en Flask con SQLAlchemy. Permite:
- Gestión de empleados y sus datos laborales
- Configuración de planillas por tipo (mensual, quincenal, semanal)
- Control de percepciones (ingresos) y deducciones
- Generación de nóminas con historial
- Soporte multimoneda con tipos de cambio

## Recent Changes

### 2025-11-27
- Agregadas tablas de Prestaciones (aportes del empleador):
  - `Prestacion`: Catálogo de prestaciones patronales (INSS patronal, vacaciones, etc.)
  - `PlanillaPrestacion`: Asociación de prestaciones a planillas
- Relación `planilla_prestaciones` agregada a `Planilla`
- Campo `prestacion_id` y relación `prestacion` agregados a `NominaDetalle`
- `NominaDetalle.tipo` ahora soporta: 'ingreso', 'deduccion', 'prestacion'

### 2025-11-25
- Agregadas nuevas tablas al modelo de datos:
  - `HistorialSalario`: Control de cambios salariales con fecha efectiva
  - `ConfiguracionVacaciones`: Fórmula configurable de devengo (ej: 2.5 días/mes en Nicaragua)
  - `VacacionEmpleado`: Saldo de vacaciones por empleado y año
  - `VacacionDescansada`: Registro de vacaciones tomadas
  - `TablaImpuesto`: Tramos fiscales vinculados a deducciones tipo "impuesto"
  - `Adelanto`: Control de adelantos de salario
  - `AdelantoAbono`: Registro de pagos/deducciones a adelantos
- Campo `tipo` agregado a `Deduccion` para identificar: "general", "impuesto", "adelanto"
- Puerto configurado a 5000 para Replit

## Project Architecture

```
coati_payroll/
├── __init__.py          # App factory y configuración Flask
├── app.py               # Blueprint principal con rutas
├── auth.py              # Autenticación y login
├── config.py            # Configuración del sistema
├── model.py             # Modelos SQLAlchemy (esquema de BD)
├── forms.py             # Formularios WTForms
├── i18n.py              # Internacionalización
├── log.py               # Configuración de logging
├── templates/           # Plantillas Jinja2
└── static/              # Archivos CSS/JS
```

## Database Schema

### Tablas Principales

| Tabla | Propósito |
|-------|-----------|
| `Usuario` | Usuarios del sistema con autenticación |
| `Moneda` | Catálogo de monedas |
| `TipoCambio` | Tipos de cambio históricos |
| `Empleado` | Registro maestro de empleados |
| `TipoPlanilla` | Tipos de planilla (mensual, quincenal, etc.) |
| `Planilla` | Definición de planillas |
| `Percepcion` | Catálogo de percepciones/ingresos |
| `Deduccion` | Catálogo de deducciones (tipo: general, impuesto, adelanto) |
| `Prestacion` | Catálogo de prestaciones patronales (aportes del empleador) |

### Tablas de Configuración de Planilla

| Tabla | Propósito |
|-------|-----------|
| `PlanillaIngreso` | Percepciones asociadas a una planilla |
| `PlanillaDeduccion` | Deducciones asociadas a una planilla |
| `PlanillaPrestacion` | Prestaciones asociadas a una planilla |
| `PlanillaEmpleado` | Empleados asignados a planillas |

### Tablas de Ejecución (Nóminas)

| Tabla | Propósito |
|-------|-----------|
| `Nomina` | Cabecera de nómina generada |
| `NominaEmpleado` | Detalle por empleado en una nómina |
| `NominaDetalle` | Líneas de percepciones/deducciones/prestaciones |
| `NominaNovedad` | Novedades aplicadas (horas extra, ausencias) |

### Tablas de Control Adicional

| Tabla | Propósito |
|-------|-----------|
| `HistorialSalario` | Historial de cambios salariales |
| `ConfiguracionVacaciones` | Fórmula de devengo de vacaciones |
| `VacacionEmpleado` | Saldo de vacaciones por año |
| `VacacionDescansada` | Registro de vacaciones tomadas |
| `TablaImpuesto` | Tramos de impuestos (ISR) |
| `Adelanto` | Adelantos de salario pendientes |
| `AdelantoAbono` | Pagos realizados a adelantos |

## Cálculo de Nómina

La fórmula básica es:

```
Salario Neto = Salario Base + Percepciones - Deducciones
Costo Total Empleador = Salario Neto + Prestaciones
```

Donde:
- **Percepciones**: Ingresos adicionales (bonos, horas extra, comisiones)
- **Deducciones**: Pueden ser tipo:
  - `general`: Deducciones normales
  - `impuesto`: Aplica tabla de tramos fiscales
  - `adelanto`: Abono automático a adelantos pendientes
- **Prestaciones**: Aportes del empleador (no afectan salario neto):
  - INSS patronal
  - Provisión de vacaciones
  - Aguinaldo proporcional
  - Otros beneficios legales

## Vacaciones (Nicaragua)

Configuración por defecto:
- `dias_por_mes`: 2.5 días por mes laborado
- `meses_minimos_para_devengar`: 1 mes

## Running the Application

```bash
python app.py
```

Credenciales por defecto:
- Usuario: `coati-admin`
- Contraseña: `coati-admin`

## Environment Variables

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | URI de conexión a BD | SQLite local |
| `SECRET_KEY` | Clave secreta Flask | "dev" |
| `ADMIN_USER` | Usuario administrador inicial | "coati-admin" |
| `ADMIN_PASSWORD` | Contraseña administrador | "coati-admin" |

## User Preferences

- Idioma: Español
- Zona horaria: UTC
