# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Service for nomina business logic."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import uuid4
from flask import current_app
from sqlalchemy import func
from coati_payroll.model import db, Planilla, Nomina, AcumuladoAnual, Deduccion, Percepcion
from coati_payroll.enums import NominaEstado
from coati_payroll.nomina_engine import NominaEngine
from coati_payroll.queue import get_queue_driver


class NominaService:
    """Service for nomina operations."""

    @staticmethod
    def _rollback_accumulations_for_nomina(nomina: Nomina, planilla: Planilla) -> None:
        """Rollback accumulated annual values produced by one payroll.

        This is required before recalculation to avoid double-counting
        (e.g., periodos_procesados jumping from 2 -> 3 for the same month).
        """
        from coati_payroll.model import NominaEmpleado, NominaDetalle

        if not planilla.tipo_planilla:
            return

        tipo_planilla = planilla.tipo_planilla
        empresa_id = planilla.empresa_id
        if not empresa_id:
            return

        fecha_base = nomina.fecha_calculo_original or nomina.fecha_generacion.date()
        anio = fecha_base.year
        mes_inicio = int(planilla.mes_inicio_fiscal or tipo_planilla.mes_inicio_fiscal)
        dia_inicio = tipo_planilla.dia_inicio_fiscal
        if fecha_base.month < mes_inicio:
            anio -= 1
        periodo_fiscal_inicio = date(anio, mes_inicio, dia_inicio)

        nomina_empleados = (
            db.session.execute(db.select(NominaEmpleado).where(NominaEmpleado.nomina_id == nomina.id)).scalars().all()
        )
        if not nomina_empleados:
            return

        empleado_ids = [ne.empleado_id for ne in nomina_empleados]
        nomina_empleado_ids = [ne.id for ne in nomina_empleados]

        acumulados = (
            db.session.execute(
                db.select(AcumuladoAnual).where(
                    AcumuladoAnual.empleado_id.in_(empleado_ids),
                    AcumuladoAnual.tipo_planilla_id == tipo_planilla.id,
                    AcumuladoAnual.empresa_id == empresa_id,
                    AcumuladoAnual.periodo_fiscal_inicio == periodo_fiscal_inicio,
                )
            )
            .scalars()
            .all()
        )
        acumulado_by_empleado = {a.empleado_id: a for a in acumulados}

        # Aggregate deduction amounts by payroll employee and deduction type.
        deduction_rows = db.session.execute(
            db.select(
                NominaDetalle.nomina_empleado_id,
                Deduccion.es_impuesto,
                Deduccion.antes_impuesto,
                func.sum(NominaDetalle.monto),
            )
            .join(Deduccion, Deduccion.id == NominaDetalle.deduccion_id)
            .where(
                NominaDetalle.nomina_empleado_id.in_(nomina_empleado_ids),
                NominaDetalle.tipo == "deduction",
                NominaDetalle.deduccion_id.is_not(None),
            )
            .group_by(NominaDetalle.nomina_empleado_id, Deduccion.es_impuesto, Deduccion.antes_impuesto)
        ).all()

        deducciones_by_ne: dict[str, dict[str, Decimal]] = {}
        for ne_id, es_impuesto, antes_impuesto, total in deduction_rows:
            bucket = deducciones_by_ne.setdefault(ne_id, {"impuesto": Decimal("0.00"), "antes": Decimal("0.00")})
            amount = Decimal(str(total or 0))
            if es_impuesto:
                bucket["impuesto"] += amount
            elif antes_impuesto:
                bucket["antes"] += amount

        # Aggregate only gravable perceptions for salario_gravable rollback.
        gravable_rows = db.session.execute(
            db.select(NominaDetalle.nomina_empleado_id, func.sum(NominaDetalle.monto))
            .join(Percepcion, Percepcion.id == NominaDetalle.percepcion_id)
            .where(
                NominaDetalle.nomina_empleado_id.in_(nomina_empleado_ids),
                NominaDetalle.tipo == "income",
                NominaDetalle.percepcion_id.is_not(None),
                Percepcion.gravable.is_(True),
            )
            .group_by(NominaDetalle.nomina_empleado_id)
        ).all()
        gravable_by_ne = {ne_id: Decimal(str(total or 0)) for ne_id, total in gravable_rows}

        for ne in nomina_empleados:
            acumulado = acumulado_by_empleado.get(ne.empleado_id)
            if not acumulado:
                continue

            salario_bruto = Decimal(str(ne.salario_bruto or 0))
            salario_base = Decimal(str(ne.sueldo_base_historico or 0))
            salario_gravable = salario_base + gravable_by_ne.get(ne.id, Decimal("0.00"))
            deducciones = deducciones_by_ne.get(ne.id, {"impuesto": Decimal("0.00"), "antes": Decimal("0.00")})

            acumulado.salario_bruto_acumulado = max(
                Decimal(str(acumulado.salario_bruto_acumulado or 0)) - salario_bruto,
                Decimal("0.00"),
            )
            acumulado.salario_acumulado_mes = max(
                Decimal(str(acumulado.salario_acumulado_mes or 0)) - salario_bruto,
                Decimal("0.00"),
            )
            acumulado.salario_gravable_acumulado = max(
                Decimal(str(acumulado.salario_gravable_acumulado or 0)) - salario_gravable,
                Decimal("0.00"),
            )
            acumulado.deducciones_antes_impuesto_acumulado = max(
                Decimal(str(acumulado.deducciones_antes_impuesto_acumulado or 0)) - deducciones["antes"],
                Decimal("0.00"),
            )
            acumulado.impuesto_retenido_acumulado = max(
                Decimal(str(acumulado.impuesto_retenido_acumulado or 0)) - deducciones["impuesto"],
                Decimal("0.00"),
            )

            acumulado.periodos_procesados = max(int(acumulado.periodos_procesados or 0) - 1, 0)
            if acumulado.periodos_procesados == 0:
                acumulado.ultimo_periodo_procesado = None
                if Decimal(str(acumulado.salario_acumulado_mes or 0)) == Decimal("0.00"):
                    acumulado.mes_actual = None

    @staticmethod
    def calcular_periodo_sugerido(planilla: Planilla) -> tuple[date, date]:
        """Calculate suggested period dates for a new nomina.

        Args:
            planilla: The planilla to calculate period for

        Returns:
            Tuple of (periodo_inicio, periodo_fin)
        """
        # Get last nomina for default dates
        ultima_nomina = db.session.execute(
            db.select(Nomina).filter_by(planilla_id=planilla.id).order_by(Nomina.periodo_fin.desc())
        ).scalar_one_or_none()

        hoy = date.today()

        if ultima_nomina:
            # Start from the day after last period ended
            periodo_inicio_sugerido = ultima_nomina.periodo_fin + timedelta(days=1)
        else:
            # First day of current month
            periodo_inicio_sugerido = hoy.replace(day=1)

        # Calculate end of period based on tipo_planilla
        tipo = planilla.tipo_planilla
        match tipo.periodicidad if tipo else "mensual":
            case "semanal":
                periodo_fin_sugerido = periodo_inicio_sugerido + timedelta(days=6)
            case "quincenal":
                if periodo_inicio_sugerido.day <= 15:
                    periodo_fin_sugerido = periodo_inicio_sugerido.replace(day=15)
                else:
                    # End of month
                    next_month = periodo_inicio_sugerido.replace(day=28) + timedelta(days=4)
                    periodo_fin_sugerido = next_month - timedelta(days=next_month.day)
            case _:  # mensual or other
                # End of month
                next_month = periodo_inicio_sugerido.replace(day=28) + timedelta(days=4)
                periodo_fin_sugerido = next_month - timedelta(days=next_month.day)

        return periodo_inicio_sugerido, periodo_fin_sugerido

    @staticmethod
    def ejecutar_nomina(
        planilla: Planilla,
        periodo_inicio: date,
        periodo_fin: date,
        fecha_calculo: date,
        usuario: str,
    ) -> tuple[Nomina | None, list[str], list[str]]:
        """Execute a nomina calculation.

        Args:
            planilla: The planilla to execute
            periodo_inicio: Start date of the period
            periodo_fin: End date of the period
            fecha_calculo: Calculation date
            usuario: Username of the user executing

        Returns:
            Tuple of (nomina, errors, warnings)
        """
        # Count active employees
        planilla_empleados = cast(list[Any], planilla.planilla_empleados)
        num_empleados = len([pe for pe in planilla_empleados if pe.activo and pe.empleado.activo])

        # Get configurable threshold for background processing
        threshold = current_app.config.get("BACKGROUND_PAYROLL_THRESHOLD", 100)

        # Determine if we should process in background
        if num_empleados > threshold:
            # Create nomina record with "calculating" status
            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                generado_por=usuario,
                estado=NominaEstado.CALCULANDO,
                total_bruto=0,
                total_deducciones=0,
                total_neto=0,
                total_empleados=num_empleados,
                empleados_procesados=0,
                empleados_con_error=0,
                procesamiento_en_background=True,
            )
            db.session.add(nomina)
            db.session.commit()

            # Enqueue background task
            try:
                queue = get_queue_driver()
                queue.enqueue(
                    "process_large_payroll",
                    nomina_id=nomina.id,
                    job_id=uuid4().hex,
                    planilla_id=planilla.id,
                    periodo_inicio=periodo_inicio.isoformat(),
                    periodo_fin=periodo_fin.isoformat(),
                    fecha_calculo=fecha_calculo.isoformat(),
                    usuario=usuario,
                )
                return nomina, [], []
            except Exception as e:
                # If background processing fails, mark nomina as error
                nomina.estado = NominaEstado.ERROR
                nomina.errores_calculo = {"background_task_initialization_error": str(e)}
                db.session.commit()
                return None, [f"Error al iniciar el procesamiento en segundo plano: {str(e)}"], []
        else:
            # For smaller payrolls, process synchronously
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                fecha_calculo=fecha_calculo,
                usuario=usuario,
            )

            nomina_result = engine.ejecutar()
            return nomina_result, engine.errors, engine.warnings

    @staticmethod
    def recalcular_nomina(
        nomina: Nomina, planilla: Planilla, usuario: str
    ) -> tuple[Nomina | None, list[str], list[str]]:
        """Recalculate an existing nomina.

        Args:
            nomina: The nomina to recalculate
            planilla: The planilla
            usuario: Username of the user recalculating

        Returns:
            Tuple of (new_nomina, errors, warnings)
        """
        from coati_payroll.model import (
            NominaEmpleado,
            NominaDetalle,
            NominaNovedad,
            AdelantoAbono,
            ComprobanteContable,
            VacationLedger,
            VacationAccount,
        )

        # Store the original period and calculation date for consistency
        periodo_inicio = nomina.periodo_inicio
        periodo_fin = nomina.periodo_fin
        fecha_calculo_original = nomina.fecha_calculo_original or nomina.fecha_generacion.date()
        nomina_original_id = nomina.id
        novedad_ids = (
            db.session.execute(db.select(NominaNovedad.id).where(NominaNovedad.nomina_id == nomina.id)).scalars().all()
        )

        # Revert original accumulated values first to keep period counts correct on recalculation.
        NominaService._rollback_accumulations_for_nomina(nomina, planilla)

        # Remove vacation ledger entries tied to the old payroll employees to avoid double accruals.
        nomina_empleado_ids = (
            db.session.execute(db.select(NominaEmpleado.id).where(NominaEmpleado.nomina_id == nomina.id))
            .scalars()
            .all()
        )
        if nomina_empleado_ids:
            account_ids = {
                row[0]
                for row in db.session.execute(
                    db.select(VacationLedger.account_id).where(
                        VacationLedger.reference_type == "nomina_empleado",
                        VacationLedger.reference_id.in_(nomina_empleado_ids),
                    )
                ).all()
                if row[0]
            }
            db.session.execute(
                db.delete(VacationLedger).where(
                    VacationLedger.reference_type == "nomina_empleado",
                    VacationLedger.reference_id.in_(nomina_empleado_ids),
                )
            )
            if account_ids:
                accounts = (
                    db.session.execute(db.select(VacationAccount).where(VacationAccount.id.in_(account_ids)))
                    .scalars()
                    .all()
                )
                for account in accounts:
                    balance = db.session.execute(
                        db.select(func.coalesce(func.sum(VacationLedger.quantity), 0)).where(
                            VacationLedger.account_id == account.id
                        )
                    ).scalar_one()
                    account.current_balance = Decimal(str(balance))
                    last_accrual = db.session.execute(
                        db.select(func.max(VacationLedger.fecha)).where(
                            VacationLedger.account_id == account.id,
                            VacationLedger.entry_type == "accrual",
                        )
                    ).scalar_one()
                    account.last_accrual_date = last_accrual

        # Re-execute the payroll with the ORIGINAL calculation date for consistency
        engine = NominaEngine(
            planilla=planilla,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_calculo=fecha_calculo_original,
            usuario=usuario,
            excluded_nomina_id=nomina_original_id,
        )

        new_nomina = engine.ejecutar()

        # Mark as recalculation and link to original
        if new_nomina:
            new_nomina.es_recalculo = True
            new_nomina.nomina_original_id = nomina_original_id

            # Delete related AdelantoAbono records
            db.session.execute(db.delete(AdelantoAbono).where(AdelantoAbono.nomina_id == nomina.id))

            # Delete NominaDetalle records
            db.session.execute(
                db.delete(NominaDetalle).where(
                    NominaDetalle.nomina_empleado_id.in_(
                        db.select(NominaEmpleado.id).where(NominaEmpleado.nomina_id == nomina.id)
                    )
                )
            )

            # Delete all NominaEmpleado records
            db.session.execute(db.delete(NominaEmpleado).where(NominaEmpleado.nomina_id == nomina.id))

            # CRITICAL: NominaNovedad must be preserved during recalculation.
            # They are master payroll events (overtime, absences, bonuses, etc.)
            # and deleting them breaks repeatable payroll calculations.
            # Re-link previous novedades to the new recalculated payroll.
            if novedad_ids:
                db.session.execute(
                    db.update(NominaNovedad).where(NominaNovedad.id.in_(novedad_ids)).values(nomina_id=new_nomina.id)
                )

            # Remove existing accounting voucher tied to the old nomina.
            # The voucher has a non-nullable FK, so it must be deleted before the nomina.
            db.session.execute(db.delete(ComprobanteContable).where(ComprobanteContable.nomina_id == nomina.id))

            # Delete the old nomina record after moving linked novelties
            db.session.delete(nomina)

            # Create audit log for recalculation
            from coati_payroll.audit_helpers import crear_log_auditoria_nomina

            crear_log_auditoria_nomina(
                nomina=new_nomina,
                accion="recalculated",
                usuario=usuario,
                descripcion=f"Nómina recalculada desde nómina original {nomina_original_id}",
                cambios={
                    "nomina_original_id": nomina_original_id,
                    "fecha_calculo_original": fecha_calculo_original.isoformat(),
                    "periodo_inicio": periodo_inicio.isoformat(),
                    "periodo_fin": periodo_fin.isoformat(),
                },
                estado_anterior="deleted",
                estado_nuevo=new_nomina.estado,
            )

            db.session.commit()

        return new_nomina, engine.errors, engine.warnings
