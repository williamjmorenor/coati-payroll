# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Background tasks for payroll processing.

This module defines tasks that can be executed in the background:
- Individual employee payroll calculations
- Bulk payroll processing for multiple employees
- Report generation
- Email notifications

Tasks are automatically registered with the available queue driver
(Dramatiq or Huey) and can be enqueued for background execution.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import joinedload

from coati_payroll.log import log
from coati_payroll.model import (
    db,
    Empleado,
    Planilla,
    Nomina as NominaModel,
    NominaEmpleado as NominaEmpleadoModel,
    NominaDetalle as NominaDetalleModel,
)
from coati_payroll.nomina_engine import NominaEngine
from coati_payroll.queue import get_queue_driver


# Get the queue driver
queue = get_queue_driver()


def calculate_employee_payroll(
    empleado_id: str,
    planilla_id: str,
    periodo_inicio: str,
    periodo_fin: str,
    fecha_calculo: str | None = None,
    usuario: str | None = None,
) -> dict[str, str | Decimal | None]:
    """Calculate payroll for a single employee (background task).

    This task can be enqueued for background processing to avoid
    blocking the main application when calculating large payrolls.

    Args:
        empleado_id: Employee ID (ULID string)
        planilla_id: Planilla ID (ULID string)
        periodo_inicio: Start date (ISO format: YYYY-MM-DD)
        periodo_fin: End date (ISO format: YYYY-MM-DD)
        fecha_calculo: Calculation date (ISO format, optional)
        usuario: Username executing the payroll (optional)

    Returns:
        Dictionary with calculation results:
        {
            "empleado_id": str,
            "salario_bruto": Decimal,
            "salario_neto": Decimal,
            "total_deducciones": Decimal,
            "success": bool,
            "error": str (if failed)
        }
    """
    try:
        log.info(f"Processing payroll for employee {empleado_id}")

        # Convert date strings to date objects
        periodo_inicio_date = date.fromisoformat(periodo_inicio)
        periodo_fin_date = date.fromisoformat(periodo_fin)
        fecha_calculo_date = date.fromisoformat(fecha_calculo) if fecha_calculo else None

        # Load employee and planilla
        empleado = db.session.get(Empleado, empleado_id)
        if not empleado:
            return {
                "empleado_id": empleado_id,
                "success": False,
                "error": "Employee not found",
            }

        planilla = db.session.get(Planilla, planilla_id)
        if not planilla:
            return {
                "empleado_id": empleado_id,
                "success": False,
                "error": "Planilla not found",
            }

        # Initialize engine for single employee
        engine = NominaEngine(
            planilla=planilla,
            periodo_inicio=periodo_inicio_date,
            periodo_fin=periodo_fin_date,
            fecha_calculo=fecha_calculo_date,
            usuario=usuario,
        )

        # Process only this employee
        emp_calculo = engine._procesar_empleado(empleado)

        # Commit to database
        db.session.commit()

        log.info(f"Employee {empleado_id} processed successfully. " f"Net: {emp_calculo.salario_neto}")

        return {
            "empleado_id": empleado_id,
            "salario_bruto": emp_calculo.salario_bruto,
            "salario_neto": emp_calculo.salario_neto,
            "total_deducciones": emp_calculo.total_deducciones,
            "success": True,
        }

    except Exception as e:
        log.error(f"Error processing employee {empleado_id}: {e}")
        db.session.rollback()
        return {
            "empleado_id": empleado_id,
            "success": False,
            "error": str(e),
        }


def process_payroll_parallel(
    planilla_id: str,
    periodo_inicio: str,
    periodo_fin: str,
    fecha_calculo: str | None = None,
    usuario: str | None = None,
) -> dict[str, bool | int | list[str]]:
    """Process payroll for all employees in parallel (background task).

    This task enqueues individual employee calculations to be processed
    concurrently by multiple workers. This is the recommended approach
    for large payrolls (1000+ employees).

    Args:
        planilla_id: Planilla ID (ULID string)
        periodo_inicio: Start date (ISO format: YYYY-MM-DD)
        periodo_fin: End date (ISO format: YYYY-MM-DD)
        fecha_calculo: Calculation date (ISO format, optional)
        usuario: Username executing the payroll (optional)

    Returns:
        Dictionary with enqueue status:
        {
            "success": bool,
            "total_employees": int,
            "enqueued_tasks": list[str],  # Task IDs
            "error": str (if failed)
        }
    """
    try:
        log.info(f"Starting parallel payroll processing for planilla {planilla_id}")

        # Load planilla
        planilla = db.session.get(Planilla, planilla_id)
        if not planilla:
            return {
                "success": False,
                "error": "Planilla not found",
            }

        # Get all active employees
        empleados = [pe.empleado for pe in planilla.planilla_empleados if pe.activo and pe.empleado.activo]

        if not empleados:
            return {
                "success": False,
                "error": "No active employees found",
            }

        # Enqueue individual tasks for each employee
        enqueued_tasks = []
        for empleado in empleados:
            try:
                task_id = queue.enqueue(
                    "calculate_employee_payroll",
                    empleado_id=empleado.id,
                    planilla_id=planilla_id,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    fecha_calculo=fecha_calculo,
                    usuario=usuario,
                )
                enqueued_tasks.append(str(task_id))
            except Exception as e:
                log.error(f"Failed to enqueue task for employee {empleado.id}: {e}")

        log.info(f"Enqueued {len(enqueued_tasks)} tasks for planilla {planilla_id}")

        return {
            "success": True,
            "total_employees": len(empleados),
            "enqueued_tasks": enqueued_tasks,
        }

    except Exception as e:
        log.error(f"Error processing parallel payroll: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def process_large_payroll(
    nomina_id: str,
    planilla_id: str,
    periodo_inicio: str,
    periodo_fin: str,
    fecha_calculo: str | None = None,
    usuario: str | None = None,
) -> dict[str, bool | int | list[str]]:
    """Process large payroll in background with progress tracking.

    This task processes a payroll for all employees sequentially,
    updating progress in the database after each employee.
    Designed for large payrolls (>100 employees) to provide
    real-time feedback to users.

    Args:
        nomina_id: Nomina ID (ULID string)
        planilla_id: Planilla ID (ULID string)
        periodo_inicio: Start date (ISO format: YYYY-MM-DD)
        periodo_fin: End date (ISO format: YYYY-MM-DD)
        fecha_calculo: Calculation date (ISO format, optional)
        usuario: Username executing the payroll (optional)

    Returns:
        Dictionary with processing results:
        {
            "success": bool,
            "total_empleados": int,
            "empleados_procesados": int,
            "empleados_con_error": int,
            "errores": list[str]
        }
    """
    from coati_payroll.enums import NominaEstado

    try:
        log.info(f"Starting background processing for nomina {nomina_id}")

        # Convert date strings to date objects
        periodo_inicio_date = date.fromisoformat(periodo_inicio)
        periodo_fin_date = date.fromisoformat(periodo_fin)
        fecha_calculo_date = date.fromisoformat(fecha_calculo) if fecha_calculo else None

        # Load nomina and planilla
        nomina = db.session.get(NominaModel, nomina_id)
        if not nomina:
            log.error(f"Nomina {nomina_id} not found")
            return {
                "success": False,
                "error": "Nomina not found",
            }

        # Load planilla with eager loading of tipo_planilla and moneda
        planilla = db.session.execute(
            db.select(Planilla)
            .options(joinedload(Planilla.tipo_planilla), joinedload(Planilla.moneda))
            .filter_by(id=planilla_id)
        ).scalar_one_or_none()

        if not planilla:
            log.error(f"Planilla {planilla_id} not found")
            nomina.estado = NominaEstado.ERROR
            nomina.errores_calculo = {"error": "Planilla not found"}
            db.session.commit()
            return {
                "success": False,
                "error": "Planilla not found",
            }

        # Get all active employees
        empleados = [pe.empleado for pe in planilla.planilla_empleados if pe.activo and pe.empleado.activo]

        if not empleados:
            log.warning(f"No active employees found for planilla {planilla_id}")
            nomina.estado = NominaEstado.ERROR
            nomina.errores_calculo = {"error": "No active employees found"}
            db.session.commit()
            return {
                "success": False,
                "error": "No active employees found",
            }

        # Initialize progress tracking
        nomina.total_empleados = len(empleados)
        nomina.empleados_procesados = 0
        nomina.empleados_con_error = 0
        nomina.errores_calculo = {}
        nomina.log_procesamiento = []
        db.session.commit()

        # Process each employee
        errores = {}
        log_entries = []
        for idx, empleado in enumerate(empleados, 1):
            empleado_nombre = f"{empleado.primer_nombre} {empleado.primer_apellido}"

            try:
                # Update current employee being processed
                nomina.empleado_actual = empleado_nombre
                db.session.commit()

                log_entries.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "empleado": empleado_nombre,
                        "status": "processing",
                        "message": f"Calculando empleado {idx}/{len(empleados)}: {empleado_nombre}",
                    }
                )
                nomina.log_procesamiento = log_entries
                db.session.commit()

                # Initialize engine for single employee
                engine = NominaEngine(
                    planilla=planilla,
                    periodo_inicio=periodo_inicio_date,
                    periodo_fin=periodo_fin_date,
                    fecha_calculo=fecha_calculo_date,
                    usuario=usuario,
                )

                # Process this employee
                emp_calculo = engine._procesar_empleado(empleado)

                # Save employee calculation to existing nomina
                nomina_empleado = NominaEmpleadoModel(
                    nomina_id=nomina_id,
                    empleado_id=empleado.id,
                    salario_bruto=emp_calculo.salario_bruto,
                    total_ingresos=emp_calculo.total_percepciones,
                    total_deducciones=emp_calculo.total_deducciones,
                    salario_neto=emp_calculo.salario_neto,
                    moneda_origen_id=emp_calculo.moneda_origen_id,
                    tipo_cambio_aplicado=emp_calculo.tipo_cambio,
                    cargo_snapshot=empleado.cargo,
                    area_snapshot=empleado.area,
                    centro_costos_snapshot=empleado.centro_costos,
                    sueldo_base_historico=emp_calculo.salario_base,
                )
                db.session.add(nomina_empleado)
                db.session.flush()

                # Save details
                for percepcion in emp_calculo.percepciones:
                    detalle = NominaDetalleModel(
                        nomina_empleado_id=nomina_empleado.id,
                        tipo="ingreso",
                        codigo=percepcion.codigo,
                        descripcion=percepcion.nombre,
                        monto=percepcion.monto,
                        orden=percepcion.orden,
                        percepcion_id=percepcion.percepcion_id,
                    )
                    db.session.add(detalle)

                for deduccion in emp_calculo.deducciones:
                    detalle = NominaDetalleModel(
                        nomina_empleado_id=nomina_empleado.id,
                        tipo="deduccion",
                        codigo=deduccion.codigo,
                        descripcion=deduccion.nombre,
                        monto=deduccion.monto,
                        orden=deduccion.prioridad,
                        deduccion_id=deduccion.deduccion_id,
                    )
                    db.session.add(detalle)

                for prestacion in emp_calculo.prestaciones:
                    detalle = NominaDetalleModel(
                        nomina_empleado_id=nomina_empleado.id,
                        tipo="prestacion",
                        codigo=prestacion.codigo,
                        descripcion=prestacion.nombre,
                        monto=prestacion.monto,
                        orden=prestacion.orden,
                        prestacion_id=prestacion.prestacion_id,
                    )
                    db.session.add(detalle)

                # Update progress with success
                nomina.empleados_procesados = idx
                log_entries.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "empleado": empleado_nombre,
                        "status": "success",
                        "message": f"✓ Completado: {empleado_nombre} - Neto: {emp_calculo.salario_neto}",
                    }
                )
                nomina.log_procesamiento = log_entries
                db.session.commit()

                log.info(f"Employee {empleado.id} processed successfully " f"({idx}/{nomina.total_empleados})")

            except Exception as e:
                error_msg = str(e)
                log.error(f"Error processing employee {empleado.id}: {error_msg}")
                errores[empleado.id] = error_msg
                nomina.empleados_con_error += 1
                nomina.empleados_procesados = idx

                # Log error
                log_entries.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "empleado": empleado_nombre,
                        "status": "error",
                        "message": f"✗ Error: {empleado_nombre} - {error_msg}",
                    }
                )
                nomina.log_procesamiento = log_entries
                db.session.commit()

        # Calculate totals
        total_bruto = sum(ne.salario_bruto for ne in nomina.nomina_empleados)
        total_deducciones = sum(ne.total_deducciones for ne in nomina.nomina_empleados)
        total_neto = sum(ne.salario_neto for ne in nomina.nomina_empleados)

        nomina.total_bruto = total_bruto
        nomina.total_deducciones = total_deducciones
        nomina.total_neto = total_neto

        # Update final status
        if errores:
            nomina.errores_calculo = errores
            # If some employees processed successfully, mark as generado with errors
            if nomina.empleados_procesados > nomina.empleados_con_error:
                nomina.estado = NominaEstado.GENERADO
            else:
                nomina.estado = NominaEstado.ERROR
        else:
            nomina.estado = NominaEstado.GENERADO

        db.session.commit()

        log.info(
            f"Background processing completed for nomina {nomina_id}. "
            f"Processed: {nomina.empleados_procesados}/{nomina.total_empleados}, "
            f"Errors: {nomina.empleados_con_error}"
        )

        return {
            "success": True,
            "total_empleados": nomina.total_empleados,
            "empleados_procesados": nomina.empleados_procesados,
            "empleados_con_error": nomina.empleados_con_error,
            "errores": list(errores.values()),
        }

    except Exception as e:
        log.error(f"Critical error in background payroll processing: {e}")
        try:
            nomina = db.session.get(NominaModel, nomina_id)
            if nomina:
                nomina.estado = NominaEstado.ERROR
                nomina.errores_calculo = {"critical_error": str(e)}
                db.session.commit()
        except Exception:
            pass
        return {
            "success": False,
            "error": str(e),
        }


# Register tasks with the queue driver
calculate_employee_payroll_task = queue.register_task(
    calculate_employee_payroll,
    name="calculate_employee_payroll",
    max_retries=3,
    min_backoff=15000,  # 15 seconds
    max_backoff=3600000,  # 1 hour
)

process_payroll_parallel_task = queue.register_task(
    process_payroll_parallel,
    name="process_payroll_parallel",
    max_retries=2,
    min_backoff=30000,  # 30 seconds
    max_backoff=7200000,  # 2 hours
)

process_large_payroll_task = queue.register_task(
    process_large_payroll,
    name="process_large_payroll",
    max_retries=1,
    min_backoff=60000,  # 60 seconds
    max_backoff=3600000,  # 1 hour
)
