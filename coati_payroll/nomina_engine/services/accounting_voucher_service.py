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
"""Service for generating accounting vouchers from payroll calculations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from collections import defaultdict
from datetime import date

from coati_payroll.model import (
    db,
    Nomina,
    NominaEmpleado,
    NominaDetalle,
    Planilla,
    Percepcion,
    Deduccion,
    Prestacion,
    Adelanto,
    ComprobanteContable,
    ComprobanteContableLinea,
)


class AccountingVoucherService:
    """Service for generating accounting vouchers from payroll calculations."""

    def __init__(self, session):
        self.session = session

    def validate_accounting_configuration(self, planilla: Planilla) -> tuple[bool, list[str]]:
        """Validate that all accounting configuration is complete.

        Args:
            planilla: The planilla to validate

        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings = []

        # Check base salary accounts
        if not planilla.codigo_cuenta_debe_salario:
            warnings.append("Falta configurar la cuenta de débito para salario básico en la planilla")
        if not planilla.codigo_cuenta_haber_salario:
            warnings.append("Falta configurar la cuenta de crédito para salario básico en la planilla")

        # Check percepciones
        percepciones = (
            self.session.execute(
                db.select(Percepcion)
                .join(Percepcion.planillas)
                .filter(db.text("planilla_ingreso.planilla_id = :planilla_id"))
                .params(planilla_id=planilla.id)
            )
            .scalars()
            .all()
        )

        for percepcion in percepciones:
            if percepcion.contabilizable:
                if not percepcion.codigo_cuenta_debe:
                    warnings.append(
                        f"Percepción '{percepcion.nombre}' ({percepcion.codigo}) no tiene cuenta de débito configurada"
                    )
                if not percepcion.codigo_cuenta_haber:
                    warnings.append(
                        f"Percepción '{percepcion.nombre}' ({percepcion.codigo}) no tiene cuenta de crédito configurada"
                    )

        # Check deducciones
        deducciones = (
            self.session.execute(
                db.select(Deduccion)
                .join(Deduccion.planillas)
                .filter(db.text("planilla_deduccion.planilla_id = :planilla_id"))
                .params(planilla_id=planilla.id)
            )
            .scalars()
            .all()
        )

        for deduccion in deducciones:
            if deduccion.contabilizable:
                if not deduccion.codigo_cuenta_debe:
                    warnings.append(
                        f"Deducción '{deduccion.nombre}' ({deduccion.codigo}) no tiene cuenta de débito configurada"
                    )
                if not deduccion.codigo_cuenta_haber:
                    warnings.append(
                        f"Deducción '{deduccion.nombre}' ({deduccion.codigo}) no tiene cuenta de crédito configurada"
                    )

        # Check prestaciones
        prestaciones = (
            self.session.execute(
                db.select(Prestacion)
                .join(Prestacion.planillas)
                .filter(db.text("planilla_prestacion.planilla_id = :planilla_id"))
                .params(planilla_id=planilla.id)
            )
            .scalars()
            .all()
        )

        for prestacion in prestaciones:
            if prestacion.contabilizable:
                if not prestacion.codigo_cuenta_debe:
                    warnings.append(
                        f"Prestación '{prestacion.nombre}' ({prestacion.codigo}) no tiene cuenta de débito configurada"
                    )
                if not prestacion.codigo_cuenta_haber:
                    warnings.append(
                        f"Prestación '{prestacion.nombre}' ({prestacion.codigo}) no tiene cuenta de crédito configurada"
                    )

        is_valid = len(warnings) == 0
        return is_valid, warnings

    def generate_accounting_voucher(
        self, nomina: Nomina, planilla: Planilla, fecha_calculo: date = None, usuario: str = None
    ) -> ComprobanteContable:
        """Generate accounting voucher for a nomina with individual lines per employee.

        Args:
            nomina: The nomina to generate voucher for
            planilla: The planilla configuration
            fecha_calculo: Calculation date (defaults to nomina periodo_fin)
            usuario: User generating/regenerating the voucher

        Returns:
            ComprobanteContable with generated line entries
        """
        from datetime import datetime, timezone
        
        # Validate configuration
        is_valid, warnings = self.validate_accounting_configuration(planilla)

        # Use nomina's calculation date or periodo_fin
        if fecha_calculo is None:
            fecha_calculo = nomina.fecha_calculo_original or nomina.periodo_fin

        # Generate voucher concept
        concepto = f"Nómina {planilla.nombre} - Período {nomina.periodo_inicio.strftime('%d/%m/%Y')} al {nomina.periodo_fin.strftime('%d/%m/%Y')}"

        # Get or create comprobante
        comprobante = (
            self.session.execute(db.select(ComprobanteContable).filter_by(nomina_id=nomina.id)).scalar_one_or_none()
        )

        if comprobante:
            # Regenerating - update modification audit trail
            self.session.execute(
                db.delete(ComprobanteContableLinea).where(ComprobanteContableLinea.comprobante_id == comprobante.id)
            )
            self.session.flush()
            # Update header information
            comprobante.fecha_calculo = fecha_calculo
            comprobante.concepto = concepto
            comprobante.moneda_id = planilla.moneda_id
            comprobante.advertencias = warnings
            # Update modification tracking
            comprobante.modificado_por = usuario or nomina.generado_por
            comprobante.fecha_modificacion = datetime.now(timezone.utc)
            comprobante.veces_modificado += 1
        else:
            # Creating new - set initial audit trail
            # Check if nomina is already applied to set aplicado_por
            from coati_payroll.enums import NominaEstado
            
            aplicado_por = None
            fecha_aplicacion = None
            if nomina.estado in (NominaEstado.APLICADO, NominaEstado.PAGADO):
                aplicado_por = nomina.aplicado_por or usuario or nomina.generado_por
                fecha_aplicacion = nomina.aplicado_en or datetime.now(timezone.utc)
            
            comprobante = ComprobanteContable(
                nomina_id=nomina.id,
                fecha_calculo=fecha_calculo,
                concepto=concepto,
                moneda_id=planilla.moneda_id,
                total_debitos=Decimal("0.00"),
                total_creditos=Decimal("0.00"),
                balance=Decimal("0.00"),
                advertencias=warnings,
                aplicado_por=aplicado_por,
                fecha_aplicacion=fecha_aplicacion,
                veces_modificado=0,
            )
            self.session.add(comprobante)
            self.session.flush()

        # Get all nomina employees with their details
        nomina_empleados = (
            self.session.execute(db.select(NominaEmpleado).filter_by(nomina_id=nomina.id)).scalars().all()
        )

        # Accumulate totals
        total_debitos = Decimal("0.00")
        total_creditos = Decimal("0.00")
        orden = 0

        # Process each employee
        for ne in nomina_empleados:
            empleado = ne.empleado
            centro_costos = ne.centro_costos_snapshot or empleado.centro_costos
            empleado_nombre_completo = f"{empleado.primer_nombre} {empleado.primer_apellido}"

            # 1. Base Salary Accounting
            if planilla.codigo_cuenta_debe_salario and planilla.codigo_cuenta_haber_salario:
                salario_base = ne.sueldo_base_historico

                # Debit: Salary Expense
                orden += 1
                linea_debe = ComprobanteContableLinea(
                    comprobante_id=comprobante.id,
                    nomina_empleado_id=ne.id,
                    empleado_id=empleado.id,
                    empleado_codigo=empleado.codigo_empleado,
                    empleado_nombre=empleado_nombre_completo,
                    codigo_cuenta=planilla.codigo_cuenta_debe_salario,
                    descripcion_cuenta=planilla.descripcion_cuenta_debe_salario or "Gasto por Salario",
                    centro_costos=centro_costos,
                    tipo_debito_credito="debito",
                    debito=salario_base,
                    credito=Decimal("0.00"),
                    monto_calculado=salario_base,
                    concepto="Salario Base",
                    tipo_concepto="salario_base",
                    concepto_codigo="SALARIO_BASE",
                    orden=orden,
                )
                self.session.add(linea_debe)
                total_debitos += salario_base

                # Credit: Salary Payable
                orden += 1
                linea_haber = ComprobanteContableLinea(
                    comprobante_id=comprobante.id,
                    nomina_empleado_id=ne.id,
                    empleado_id=empleado.id,
                    empleado_codigo=empleado.codigo_empleado,
                    empleado_nombre=empleado_nombre_completo,
                    codigo_cuenta=planilla.codigo_cuenta_haber_salario,
                    descripcion_cuenta=planilla.descripcion_cuenta_haber_salario or "Salario por Pagar",
                    centro_costos=centro_costos,
                    tipo_debito_credito="credito",
                    debito=Decimal("0.00"),
                    credito=salario_base,
                    monto_calculado=salario_base,
                    concepto="Salario Base",
                    tipo_concepto="salario_base",
                    concepto_codigo="SALARIO_BASE",
                    orden=orden,
                )
                self.session.add(linea_haber)
                total_creditos += salario_base

            # 2. Process Loans and Advances (special treatment)
            # Loans/advances debit salary payable and credit loan control account
            detalles = (
                self.session.execute(
                    db.select(NominaDetalle).filter_by(nomina_empleado_id=ne.id).order_by(NominaDetalle.orden)
                )
                .scalars()
                .all()
            )

            for detalle in detalles:
                # Check if this is a loan/advance deduction
                is_loan_advance = False
                cuenta_control_prestamo = None

                if detalle.deduccion_id:
                    deduccion = self.session.get(Deduccion, detalle.deduccion_id)
                    if deduccion:
                        # Check if this deduction is associated with loans/advances
                        adelantos = (
                            self.session.execute(
                                db.select(Adelanto).filter_by(empleado_id=empleado.id, deduccion_id=deduccion.id)
                            )
                            .scalars()
                            .all()
                        )
                        if adelantos:
                            is_loan_advance = True
                            # Get loan control account from first active loan
                            for adelanto in adelantos:
                                if adelanto.estado in ("aprobado", "aplicado"):
                                    cuenta_control_prestamo = adelanto.cuenta_haber
                                    break

                if is_loan_advance and cuenta_control_prestamo:
                    # Loan/advance: Debit salary payable, Credit loan control
                    # Debit: Salary Payable (same as base salary credit account)
                    if planilla.codigo_cuenta_haber_salario:
                        orden += 1
                        linea_debe = ComprobanteContableLinea(
                            comprobante_id=comprobante.id,
                            nomina_empleado_id=ne.id,
                            empleado_id=empleado.id,
                            empleado_codigo=empleado.codigo_empleado,
                            empleado_nombre=empleado_nombre_completo,
                            codigo_cuenta=planilla.codigo_cuenta_haber_salario,
                            descripcion_cuenta=planilla.descripcion_cuenta_haber_salario or "Salario por Pagar",
                            centro_costos=centro_costos,
                            tipo_debito_credito="debito",
                                debito=detalle.monto,
                                credito=Decimal("0.00"),
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or "Préstamo/Adelanto",
                            tipo_concepto="prestamo",
                            concepto_codigo=detalle.codigo,
                            orden=orden,
                        )
                        self.session.add(linea_debe)
                        total_debitos += detalle.monto

                    # Credit: Loan Control Account
                    orden += 1
                    linea_haber = ComprobanteContableLinea(
                        comprobante_id=comprobante.id,
                        nomina_empleado_id=ne.id,
                        empleado_id=empleado.id,
                        empleado_codigo=empleado.codigo_empleado,
                        empleado_nombre=empleado_nombre_completo,
                        codigo_cuenta=cuenta_control_prestamo,
                        descripcion_cuenta="Cuenta de Control Préstamos/Adelantos",
                        centro_costos=centro_costos,
                        tipo_debito_credito="credito",
                                debito=Decimal("0.00"),
                                credito=detalle.monto,
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or "Préstamo/Adelanto",
                        tipo_concepto="prestamo",
                        concepto_codigo=detalle.codigo,
                        orden=orden,
                    )
                    self.session.add(linea_haber)
                    total_creditos += detalle.monto

                else:
                    # Regular concept - use configured accounts
                    if detalle.tipo == "ingreso" and detalle.percepcion_id:
                        percepcion = self.session.get(Percepcion, detalle.percepcion_id)
                        if percepcion and percepcion.contabilizable:
                            if percepcion.codigo_cuenta_debe:
                                orden += 1
                                linea_debe = ComprobanteContableLinea(
                                    comprobante_id=comprobante.id,
                                    nomina_empleado_id=ne.id,
                                    empleado_id=empleado.id,
                                    empleado_codigo=empleado.codigo_empleado,
                                    empleado_nombre=empleado_nombre_completo,
                                    codigo_cuenta=percepcion.codigo_cuenta_debe,
                                    descripcion_cuenta=percepcion.descripcion_cuenta_debe or percepcion.nombre,
                                    centro_costos=centro_costos,
                                    tipo_debito_credito="debito",
                                debito=detalle.monto,
                                credito=Decimal("0.00"),
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or percepcion.nombre,
                                    tipo_concepto="percepcion",
                                    concepto_codigo=percepcion.codigo,
                                    orden=orden,
                                )
                                self.session.add(linea_debe)
                                total_debitos += detalle.monto

                            if percepcion.codigo_cuenta_haber:
                                orden += 1
                                linea_haber = ComprobanteContableLinea(
                                    comprobante_id=comprobante.id,
                                    nomina_empleado_id=ne.id,
                                    empleado_id=empleado.id,
                                    empleado_codigo=empleado.codigo_empleado,
                                    empleado_nombre=empleado_nombre_completo,
                                    codigo_cuenta=percepcion.codigo_cuenta_haber,
                                    descripcion_cuenta=percepcion.descripcion_cuenta_haber or percepcion.nombre,
                                    centro_costos=centro_costos,
                                    tipo_debito_credito="credito",
                                debito=Decimal("0.00"),
                                credito=detalle.monto,
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or percepcion.nombre,
                                    tipo_concepto="percepcion",
                                    concepto_codigo=percepcion.codigo,
                                    orden=orden,
                                )
                                self.session.add(linea_haber)
                                total_creditos += detalle.monto

                    elif detalle.tipo == "deduccion" and detalle.deduccion_id:
                        deduccion = self.session.get(Deduccion, detalle.deduccion_id)
                        if deduccion and deduccion.contabilizable:
                            if deduccion.codigo_cuenta_debe:
                                orden += 1
                                linea_debe = ComprobanteContableLinea(
                                    comprobante_id=comprobante.id,
                                    nomina_empleado_id=ne.id,
                                    empleado_id=empleado.id,
                                    empleado_codigo=empleado.codigo_empleado,
                                    empleado_nombre=empleado_nombre_completo,
                                    codigo_cuenta=deduccion.codigo_cuenta_debe,
                                    descripcion_cuenta=deduccion.descripcion_cuenta_debe or deduccion.nombre,
                                    centro_costos=centro_costos,
                                    tipo_debito_credito="debito",
                                debito=detalle.monto,
                                credito=Decimal("0.00"),
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or deduccion.nombre,
                                    tipo_concepto="deduccion",
                                    concepto_codigo=deduccion.codigo,
                                    orden=orden,
                                )
                                self.session.add(linea_debe)
                                total_debitos += detalle.monto

                            if deduccion.codigo_cuenta_haber:
                                orden += 1
                                linea_haber = ComprobanteContableLinea(
                                    comprobante_id=comprobante.id,
                                    nomina_empleado_id=ne.id,
                                    empleado_id=empleado.id,
                                    empleado_codigo=empleado.codigo_empleado,
                                    empleado_nombre=empleado_nombre_completo,
                                    codigo_cuenta=deduccion.codigo_cuenta_haber,
                                    descripcion_cuenta=deduccion.descripcion_cuenta_haber or deduccion.nombre,
                                    centro_costos=centro_costos,
                                    tipo_debito_credito="credito",
                                debito=Decimal("0.00"),
                                credito=detalle.monto,
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or deduccion.nombre,
                                    tipo_concepto="deduccion",
                                    concepto_codigo=deduccion.codigo,
                                    orden=orden,
                                )
                                self.session.add(linea_haber)
                                total_creditos += detalle.monto

                    elif detalle.tipo == "prestacion" and detalle.prestacion_id:
                        prestacion = self.session.get(Prestacion, detalle.prestacion_id)
                        if prestacion and prestacion.contabilizable:
                            if prestacion.codigo_cuenta_debe:
                                orden += 1
                                linea_debe = ComprobanteContableLinea(
                                    comprobante_id=comprobante.id,
                                    nomina_empleado_id=ne.id,
                                    empleado_id=empleado.id,
                                    empleado_codigo=empleado.codigo_empleado,
                                    empleado_nombre=empleado_nombre_completo,
                                    codigo_cuenta=prestacion.codigo_cuenta_debe,
                                    descripcion_cuenta=prestacion.descripcion_cuenta_debe or prestacion.nombre,
                                    centro_costos=centro_costos,
                                    tipo_debito_credito="debito",
                                debito=detalle.monto,
                                credito=Decimal("0.00"),
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or prestacion.nombre,
                                    tipo_concepto="prestacion",
                                    concepto_codigo=prestacion.codigo,
                                    orden=orden,
                                )
                                self.session.add(linea_debe)
                                total_debitos += detalle.monto

                            if prestacion.codigo_cuenta_haber:
                                orden += 1
                                linea_haber = ComprobanteContableLinea(
                                    comprobante_id=comprobante.id,
                                    nomina_empleado_id=ne.id,
                                    empleado_id=empleado.id,
                                    empleado_codigo=empleado.codigo_empleado,
                                    empleado_nombre=empleado_nombre_completo,
                                    codigo_cuenta=prestacion.codigo_cuenta_haber,
                                    descripcion_cuenta=prestacion.descripcion_cuenta_haber or prestacion.nombre,
                                    centro_costos=centro_costos,
                                    tipo_debito_credito="credito",
                                debito=Decimal("0.00"),
                                credito=detalle.monto,
                                monto_calculado=detalle.monto,
                                concepto=detalle.descripcion or prestacion.nombre,
                                    tipo_concepto="prestacion",
                                    concepto_codigo=prestacion.codigo,
                                    orden=orden,
                                )
                                self.session.add(linea_haber)
                                total_creditos += detalle.monto

        # Calculate balance (should be 0 for balanced voucher)
        balance = total_debitos - total_creditos

        # Validate balance
        if balance != Decimal("0.00"):
            balance_warning = (
                f"ADVERTENCIA: El comprobante no está balanceado. "
                f"Débitos: {total_debitos}, Créditos: {total_creditos}, "
                f"Diferencia: {abs(balance)}"
            )
            if balance_warning not in warnings:
                warnings.append(balance_warning)

        # Update comprobante totals
        comprobante.total_debitos = total_debitos
        comprobante.total_creditos = total_creditos
        comprobante.balance = balance
        comprobante.advertencias = warnings

        return comprobante

    def summarize_voucher(self, comprobante: ComprobanteContable) -> list[dict[str, Any]]:
        """Summarize voucher lines by account and cost center with netting.

        Groups lines by (codigo_cuenta, centro_costos) and nets debits/credits.
        If same account+cost center has both debits and credits, they are netted
        and only one line with the net amount is shown.

        Args:
            comprobante: The comprobante to summarize

        Returns:
            List of summarized entries sorted by account code
        """
        # Dictionary to accumulate by (account, cost_center)
        summary_dict: dict[tuple[str, str | None], dict[str, Any]] = defaultdict(
            lambda: {"debito": Decimal("0.00"), "credito": Decimal("0.00"), "descripcion": ""}
        )

        # Get all lines
        lineas = (
            self.session.execute(
                db.select(ComprobanteContableLinea)
                .filter_by(comprobante_id=comprobante.id)
                .order_by(ComprobanteContableLinea.orden)
            )
            .scalars()
            .all()
        )

        # Accumulate by account + cost center
        for linea in lineas:
            key = (linea.codigo_cuenta, linea.centro_costos)
            summary_dict[key]["debito"] += linea.debito
            summary_dict[key]["credito"] += linea.credito
            # Use first description found for this account
            if not summary_dict[key]["descripcion"]:
                summary_dict[key]["descripcion"] = linea.descripcion_cuenta or ""

        # Create summarized entries with netting
        summarized_entries = []
        for (codigo_cuenta, centro_costos), amounts in summary_dict.items():
            debito = amounts["debito"]
            credito = amounts["credito"]

            # Net debits and credits
            if debito > credito:
                monto_neto = debito - credito
                summarized_entries.append(
                    {
                        "codigo_cuenta": codigo_cuenta,
                        "descripcion": amounts["descripcion"],
                        "centro_costos": centro_costos,
                        "debito": monto_neto,
                        "credito": Decimal("0.00"),
                    }
                )
            elif credito > debito:
                monto_neto = credito - debito
                summarized_entries.append(
                    {
                        "codigo_cuenta": codigo_cuenta,
                        "descripcion": amounts["descripcion"],
                        "centro_costos": centro_costos,
                        "debito": Decimal("0.00"),
                        "credito": monto_neto,
                    }
                )
            # If debito == credito, they cancel out completely, so line is excluded from summary
            # This is intentional: zero-balance entries don't need to appear in the summarized voucher

        # Sort by account code and cost center
        summarized_entries.sort(key=lambda x: (x["codigo_cuenta"], x["centro_costos"] or ""))

        return summarized_entries

    def get_detailed_voucher_by_employee(self, comprobante: ComprobanteContable) -> list[dict[str, Any]]:
        """Get detailed voucher lines grouped by employee for audit purposes.

        Args:
            comprobante: The comprobante to get details for

        Returns:
            List of entries grouped by employee with all their accounting lines
        """
        detailed_entries = []

        # Get all lines grouped by employee using the denormalized employee info
        lineas = (
            self.session.execute(
                db.select(ComprobanteContableLinea)
                .filter_by(comprobante_id=comprobante.id)
                .order_by(ComprobanteContableLinea.empleado_codigo, ComprobanteContableLinea.orden)
            )
            .scalars()
            .all()
        )

        # Group by employee
        current_empleado_codigo = None
        current_entry = None

        for linea in lineas:
            if linea.empleado_codigo != current_empleado_codigo:
                # New employee, save previous and start new
                if current_entry:
                    detailed_entries.append(current_entry)

                current_empleado_codigo = linea.empleado_codigo
                current_entry = {
                    "empleado_codigo": linea.empleado_codigo,
                    "empleado_nombre": linea.empleado_nombre,
                    "centro_costos": linea.centro_costos,
                    "lineas": [],
                }

            # Add line to current employee
            current_entry["lineas"].append(
                {
                    "concepto": linea.concepto,
                    "tipo_concepto": linea.tipo_concepto,
                    "codigo_cuenta": linea.codigo_cuenta,
                    "descripcion_cuenta": linea.descripcion_cuenta,
                    "debito": linea.debito,
                    "credito": linea.credito,
                }
            )

        # Don't forget the last employee
        if current_entry:
            detailed_entries.append(current_entry)

        return detailed_entries
