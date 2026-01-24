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

import os
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
    PrestacionAcumulada,
    AdelantoAbono,
    InteresAdelanto,
)
from coati_payroll.nomina_engine import NominaEngine
from coati_payroll.queue import get_queue_driver


# Get the queue driver
queue = get_queue_driver()


def _get_payroll_retry_config() -> dict[str, int]:
    """Get payroll retry configuration from environment variables.

    Returns:
        Dictionary with retry configuration:
        {
            "max_retries": int,
            "min_backoff_ms": int,
            "max_backoff_ms": int
        }
    """
    return {
        "max_retries": int(os.getenv("PAYROLL_MAX_RETRIES", "3")),
        "min_backoff_ms": int(os.getenv("PAYROLL_MIN_BACKOFF_MS", "60000")),  # 60 seconds
        "max_backoff_ms": int(os.getenv("PAYROLL_MAX_BACKOFF_MS", "3600000")),  # 1 hour
    }


def _is_recoverable_error(error: Exception) -> bool:
    """Determine if an error is recoverable (can be retried).

    Recoverable errors are typically transient issues like:
    - Database connection problems
    - Network timeouts
    - Temporary resource unavailability

    Non-recoverable errors are typically:
    - Validation errors
    - Data integrity issues
    - Configuration problems

    Args:
        error: The exception that occurred

    Returns:
        True if error is recoverable, False otherwise
    """
    error_msg = str(error).lower()

    # Recoverable error patterns
    recoverable_patterns = [
        "connection",
        "timeout",
        "temporary",
        "unavailable",
        "deadlock",
        "lock",
        "network",
        "socket",
        "broken pipe",
    ]

    # Non-recoverable error patterns
    non_recoverable_patterns = [
        "validation",
        "integrity",
        "not found",
        "invalid",
        "missing",
        "required",
    ]

    # Check for non-recoverable patterns first
    for pattern in non_recoverable_patterns:
        if pattern in error_msg:
            return False

    # Check for recoverable patterns
    for pattern in recoverable_patterns:
        if pattern in error_msg:
            return True

    # Default: assume recoverable for unknown errors (safer to retry)
    return True


def retry_failed_nomina(nomina_id: str, usuario: str | None = None) -> dict[str, bool | str]:
    """Retry processing a failed nomina.

    This function allows manual retry of a nomina that failed during processing.
    It will reset the nomina state and attempt to process it again.

    Args:
        nomina_id: ID of the failed nomina to retry
        usuario: Username attempting the retry (optional)

    Returns:
        Dictionary with retry status:
        {
            "success": bool,
            "message": str,
            "error": str (if failed)
        }
    """
    from coati_payroll.enums import NominaEstado

    try:
        log.info(f"Retrying failed nomina {nomina_id}")

        # Load the nomina
        nomina = db.session.get(NominaModel, nomina_id)
        if not nomina:
            return {
                "success": False,
                "error": "Nomina not found",
            }

        # Verify nomina is in ERROR state
        if nomina.estado != NominaEstado.ERROR:
            return {
                "success": False,
                "error": f"Nomina not in ERROR state (current: {nomina.estado}). Only failed nominas can be retried.",
            }

        # Get planilla information
        planilla = db.session.get(Planilla, nomina.planilla_id)
        if not planilla:
            return {
                "success": False,
                "error": "Planilla not found",
            }

        # Reset nomina state for retry
        nomina.estado = NominaEstado.CALCULANDO
        nomina.empleados_procesados = 0
        nomina.empleados_con_error = 0
        nomina.errores_calculo = {}
        nomina.log_procesamiento = []
        nomina.empleado_actual = None

        # Clear any partial data from previous attempt
        _rollback_nomina_data(nomina_id)

        db.session.commit()

        # Enqueue the processing task again
        fecha_calculo_str = nomina.fecha_generacion.date().isoformat() if nomina.fecha_generacion else None
        periodo_inicio_str = nomina.periodo_inicio.isoformat()
        periodo_fin_str = nomina.periodo_fin.isoformat()

        task_id = queue.enqueue(
            "process_large_payroll",
            nomina_id=nomina_id,
            planilla_id=nomina.planilla_id,
            periodo_inicio=periodo_inicio_str,
            periodo_fin=periodo_fin_str,
            fecha_calculo=fecha_calculo_str,
            usuario=usuario or nomina.generado_por,
        )

        log.info(f"Retry task enqueued for nomina {nomina_id}, task_id: {task_id}")

        return {
            "success": True,
            "message": f"Retry task enqueued successfully. Task ID: {task_id}",
        }

    except Exception as e:
        log.error(f"Error retrying nomina {nomina_id}: {e}")
        db.session.rollback()
        return {
            "success": False,
            "error": str(e),
        }


def _rollback_nomina_data(nomina_id: str) -> None:
    """Rollback all data created for a nomina during payroll processing.

    This function removes all records created during payroll calculation:
    - NominaEmpleado records
    - NominaDetalle records
    - PrestacionAcumulada transactions
    - AdelantoAbono records
    - InteresAdelanto records
    - Reverts AcumuladoAnual changes

    Args:
        nomina_id: ID of the nomina to rollback
    """
    try:
        log.info(f"Rolling back all data for nomina {nomina_id}")

        # Get all NominaEmpleado records for this nomina
        nomina_empleados = (
            db.session.execute(db.select(NominaEmpleadoModel).filter(NominaEmpleadoModel.nomina_id == nomina_id))
            .scalars()
            .all()
        )

        # Collect all IDs for cascading deletes
        nomina_empleado_ids = [ne.id for ne in nomina_empleados]

        if nomina_empleado_ids:
            # Delete NominaDetalle records (cascade from NominaEmpleado)
            db.session.execute(
                db.delete(NominaDetalleModel).filter(NominaDetalleModel.nomina_empleado_id.in_(nomina_empleado_ids))
            )

            # Delete NominaEmpleado records
            db.session.execute(db.delete(NominaEmpleadoModel).filter(NominaEmpleadoModel.nomina_id == nomina_id))

        # Delete PrestacionAcumulada transactions created for this nomina
        db.session.execute(db.delete(PrestacionAcumulada).filter(PrestacionAcumulada.nomina_id == nomina_id))

        # Delete AdelantoAbono records created for this nomina
        db.session.execute(db.delete(AdelantoAbono).filter(AdelantoAbono.nomina_id == nomina_id))

        # Delete InteresAdelanto records created for this nomina
        db.session.execute(db.delete(InteresAdelanto).filter(InteresAdelanto.nomina_id == nomina_id))

        # Note: AcumuladoAnual changes are reverted via transaction rollback
        # VacationLedger entries are also reverted via transaction rollback

        log.info(f"Successfully rolled back data for nomina {nomina_id}")

    except Exception as e:
        log.error(f"Error during rollback for nomina {nomina_id}: {e}")
        raise


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

    NOTE: This function now uses the same defensive mechanism as process_large_payroll
    to ensure atomicity. If any employee processing fails, all changes are rolled back.

    For true parallel processing with multiple workers, use process_large_payroll which
    processes employees sequentially but provides better error handling and rollback.

    Args:
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

        # Create nomina record first
        nomina = NominaModel(
            planilla_id=planilla_id,
            periodo_inicio=date.fromisoformat(periodo_inicio),
            periodo_fin=date.fromisoformat(periodo_fin),
            generado_por=usuario,
            estado=NominaEstado.CALCULANDO,
            total_bruto=Decimal("0.00"),
            total_deducciones=Decimal("0.00"),
            total_neto=Decimal("0.00"),
            total_empleados=len(empleados),
            empleados_procesados=0,
            empleados_con_error=0,
            procesamiento_en_background=True,
        )
        db.session.add(nomina)
        db.session.commit()

        # Use process_large_payroll which has the defensive rollback mechanism
        # This ensures atomicity: if any employee fails, all changes are rolled back
        result = process_large_payroll(
            nomina_id=nomina.id,
            planilla_id=planilla_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_calculo=fecha_calculo,
            usuario=usuario,
        )

        return result

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

        # CRITICAL: Use savepoints for safer transaction management
        # Process employees with periodic commits to reduce risk of losing all work
        # If ANY employee fails, rollback ALL changes to maintain consistency
        log_entries = []
        BATCH_SIZE = 10  # Commit progress every N employees to reduce risk

        try:
            # Create initial savepoint for the entire operation
            savepoint = db.session.begin_nested()

            # Process each employee
            for idx, empleado in enumerate(empleados, 1):
                empleado_nombre = f"{empleado.primer_nombre} {empleado.primer_apellido}"

                try:
                    # Create savepoint for this employee
                    emp_savepoint = db.session.begin_nested()

                    # Update current employee being processed (for progress tracking)
                    nomina.empleado_actual = empleado_nombre
                    log_entries.append(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "empleado": empleado_nombre,
                            "status": "processing",
                            "message": f"Calculando empleado {idx}/{len(empleados)}: {empleado_nombre}",
                        }
                    )
                    nomina.log_procesamiento = log_entries
                    # Commit progress updates separately (outside savepoint) so user can see progress
                    db.session.commit()

                    # Initialize engine for single employee
                    engine = NominaEngine(
                        planilla=planilla,
                        periodo_inicio=periodo_inicio_date,
                        periodo_fin=periodo_fin_date,
                        fecha_calculo=fecha_calculo_date,
                        usuario=usuario,
                    )
                    # Set nomina in engine so it can create related records
                    engine.nomina = nomina

                    # Process this employee (creates NominaEmpleado, NominaDetalle, etc.)
                    emp_calculo = engine._procesar_empleado(empleado)

                    # Commit this employee's savepoint (employee processed successfully)
                    emp_savepoint.commit()

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

                    # Commit progress updates periodically to reduce risk
                    # This commits only the progress tracking, not the employee data
                    if idx % BATCH_SIZE == 0 or idx == len(empleados):
                        db.session.commit()
                        log.info(f"Progress committed: {idx}/{len(empleados)} employees processed")

                    log.info(f"Employee {empleado.id} processed successfully " f"({idx}/{nomina.total_empleados})")

                except Exception as e:
                    # Rollback this employee's savepoint (undoes only this employee)
                    emp_savepoint.rollback()

                    # Re-raise to trigger outer rollback of entire operation
                    error_msg = str(e)
                    log.error(f"Error processing employee {empleado.id}: {error_msg}")
                    raise

            # All employees processed successfully - commit the main savepoint
            savepoint.commit()

            # Calculate totals
            total_bruto = sum(ne.salario_bruto for ne in nomina.nomina_empleados)
            total_deducciones = sum(ne.total_deducciones for ne in nomina.nomina_empleados)
            total_neto = sum(ne.salario_neto for ne in nomina.nomina_empleados)

            nomina.total_bruto = total_bruto
            nomina.total_deducciones = total_deducciones
            nomina.total_neto = total_neto
            nomina.estado = NominaEstado.GENERADO
            nomina.errores_calculo = {}
            nomina.empleado_actual = None  # Clear current employee

            # Final commit (this is smaller now since we've been committing progress)
            db.session.commit()

            log.info(f"All employees processed successfully for nomina {nomina_id}")

        except Exception as e:
            # CRITICAL: Rollback all changes if any employee fails
            error_msg = str(e)
            error_type = type(e).__name__

            # Determine if error is recoverable (can be retried)
            # Recoverable: database connection issues, temporary network problems, etc.
            # Non-recoverable: validation errors, data integrity issues, etc.
            is_recoverable = _is_recoverable_error(e)

            log.error(
                f"Critical error during payroll processing: {error_msg} "
                f"(Type: {error_type}, Recoverable: {is_recoverable})"
            )

            # Rollback the main savepoint (undoes all employee processing)
            try:
                savepoint.rollback()
            except Exception:
                # If savepoint doesn't exist or already rolled back, do full rollback
                db.session.rollback()

            # Rollback any remaining data that might have been created
            _rollback_nomina_data(nomina_id)

            # Mark nomina as ERROR with detailed error information
            nomina.estado = NominaEstado.ERROR
            nomina.errores_calculo = {
                "critical_error": error_msg,
                "error_type": error_type,
                "is_recoverable": is_recoverable,
                "empleados_procesados_antes_fallo": nomina.empleados_procesados,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            nomina.log_procesamiento = log_entries + [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "empleado": "SISTEMA",
                    "status": "error",
                    "message": (
                        f"✗ ERROR CRÍTICO: La nómina falló. Todos los cambios fueron revertidos. "
                        f"Error: {error_msg} "
                        f"(Puede reintentarse: {'Sí' if is_recoverable else 'No'})"
                    ),
                }
            ]
            nomina.empleado_actual = None
            db.session.commit()

            # Re-raise to signal failure (queue system will handle retries if configured)
            raise

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
            "errores": nomina.errores_calculo or {},
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


# Get retry configuration from environment
_retry_config = _get_payroll_retry_config()

# Register tasks with the queue driver
calculate_employee_payroll_task = queue.register_task(
    calculate_employee_payroll,
    name="calculate_employee_payroll",
    max_retries=int(os.getenv("PAYROLL_EMPLOYEE_MAX_RETRIES", "3")),
    min_backoff=int(os.getenv("PAYROLL_EMPLOYEE_MIN_BACKOFF_MS", "15000")),  # 15 seconds
    max_backoff=int(os.getenv("PAYROLL_EMPLOYEE_MAX_BACKOFF_MS", "3600000")),  # 1 hour
)

process_payroll_parallel_task = queue.register_task(
    process_payroll_parallel,
    name="process_payroll_parallel",
    max_retries=int(os.getenv("PAYROLL_PARALLEL_MAX_RETRIES", "2")),
    min_backoff=int(os.getenv("PAYROLL_PARALLEL_MIN_BACKOFF_MS", "30000")),  # 30 seconds
    max_backoff=int(os.getenv("PAYROLL_PARALLEL_MAX_BACKOFF_MS", "7200000")),  # 2 hours
)

process_large_payroll_task = queue.register_task(
    process_large_payroll,
    name="process_large_payroll",
    max_retries=_retry_config["max_retries"],
    min_backoff=_retry_config["min_backoff_ms"],
    max_backoff=_retry_config["max_backoff_ms"],
)

retry_failed_nomina_task = queue.register_task(
    retry_failed_nomina,
    name="retry_failed_nomina",
    max_retries=1,  # Manual retry, no automatic retries needed
    min_backoff=0,
    max_backoff=0,
)
