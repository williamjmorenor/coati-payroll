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
        self, nomina: Nomina, planilla: Planilla, fecha_calculo: date = None
    ) -> ComprobanteContable:
        """Generate accounting voucher for a nomina with individual lines per employee.

        Args:
            nomina: The nomina to generate voucher for
            planilla: The planilla configuration
            fecha_calculo: Calculation date (defaults to nomina periodo_fin)

        Returns:
            ComprobanteContable with generated line entries
        """
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
            # Delete existing lines to regenerate
            self.session.execute(
                db.delete(ComprobanteContableLinea).where(ComprobanteContableLinea.comprobante_id == comprobante.id)
            )
            self.session.flush()
            # Update header information
            comprobante.fecha_calculo = fecha_calculo
            comprobante.concepto = concepto
            comprobante.moneda_id = planilla.moneda_id
            comprobante.advertencias = warnings
        else:
            # Create new comprobante
            comprobante = ComprobanteContable(
                nomina_id=nomina.id,
                fecha_calculo=fecha_calculo,
                concepto=concepto,
                moneda_id=planilla.moneda_id,
                total_debitos=Decimal("0.00"),
                total_creditos=Decimal("0.00"),
                balance=Decimal("0.00"),
                advertencias=warnings,
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

            # 1. Base Salary Accounting
            if planilla.codigo_cuenta_debe_salario and planilla.codigo_cuenta_haber_salario:
                salario_base = ne.sueldo_base_historico

                # Debit: Salary Expense
                orden += 1
                linea_debe = ComprobanteContableLinea(
                    comprobante_id=comprobante.id,
                    nomina_empleado_id=ne.id,
                    codigo_cuenta=planilla.codigo_cuenta_debe_salario,
                    descripcion_cuenta=planilla.descripcion_cuenta_debe_salario or "Gasto por Salario",
                    centro_costos=centro_costos,
                    debito=salario_base,
                    credito=Decimal("0.00"),
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
                    codigo_cuenta=planilla.codigo_cuenta_haber_salario,
                    descripcion_cuenta=planilla.descripcion_cuenta_haber_salario or "Salario por Pagar",
                    centro_costos=centro_costos,
                    debito=Decimal("0.00"),
                    credito=salario_base,
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
                self.session.execute(db.select(NominaDetalle).filter_by(nomina_empleado_id=ne.id).order_by(NominaDetalle.orden))
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
                        key_debe = (
                            planilla.codigo_cuenta_haber_salario,
                            planilla.descripcion_cuenta_haber_salario or "Salario por Pagar",
                            centro_costos,
                        )
                        entries_dict[key_debe]["debito"] += detalle.monto

                    # Credit: Loan Control Account
                    key_haber = (cuenta_control_prestamo, "Cuenta de Control Préstamos/Adelantos", centro_costos)
                    entries_dict[key_haber]["credito"] += detalle.monto

                else:
                    # Regular concept - use configured accounts
                    if detalle.tipo == "ingreso" and detalle.percepcion_id:
                        percepcion = self.session.get(Percepcion, detalle.percepcion_id)
                        if percepcion and percepcion.contabilizable:
                            if percepcion.codigo_cuenta_debe:
                                key_debe = (
                                    percepcion.codigo_cuenta_debe,
                                    percepcion.descripcion_cuenta_debe or percepcion.nombre,
                                    centro_costos,
                                )
                                entries_dict[key_debe]["debito"] += detalle.monto

                            if percepcion.codigo_cuenta_haber:
                                key_haber = (
                                    percepcion.codigo_cuenta_haber,
                                    percepcion.descripcion_cuenta_haber or percepcion.nombre,
                                    centro_costos,
                                )
                                entries_dict[key_haber]["credito"] += detalle.monto

                    elif detalle.tipo == "deduccion" and detalle.deduccion_id:
                        deduccion = self.session.get(Deduccion, detalle.deduccion_id)
                        if deduccion and deduccion.contabilizable:
                            if deduccion.codigo_cuenta_debe:
                                key_debe = (
                                    deduccion.codigo_cuenta_debe,
                                    deduccion.descripcion_cuenta_debe or deduccion.nombre,
                                    centro_costos,
                                )
                                entries_dict[key_debe]["debito"] += detalle.monto

                            if deduccion.codigo_cuenta_haber:
                                key_haber = (
                                    deduccion.codigo_cuenta_haber,
                                    deduccion.descripcion_cuenta_haber or deduccion.nombre,
                                    centro_costos,
                                )
                                entries_dict[key_haber]["credito"] += detalle.monto

                    elif detalle.tipo == "prestacion" and detalle.prestacion_id:
                        prestacion = self.session.get(Prestacion, detalle.prestacion_id)
                        if prestacion and prestacion.contabilizable:
                            if prestacion.codigo_cuenta_debe:
                                key_debe = (
                                    prestacion.codigo_cuenta_debe,
                                    prestacion.descripcion_cuenta_debe or prestacion.nombre,
                                    centro_costos,
                                )
                                entries_dict[key_debe]["debito"] += detalle.monto

                            if prestacion.codigo_cuenta_haber:
                                key_haber = (
                                    prestacion.codigo_cuenta_haber,
                                    prestacion.descripcion_cuenta_haber or prestacion.nombre,
                                    centro_costos,
                                )
                                entries_dict[key_haber]["credito"] += detalle.monto

        # Net debits and credits for same account + cost center combination
        asientos_contables = []
        total_debitos = Decimal("0.00")
        total_creditos = Decimal("0.00")

        for (codigo_cuenta, descripcion, centro_costos), amounts in entries_dict.items():
            debito = amounts["debito"]
            credito = amounts["credito"]

            # Net debits and credits
            if debito > credito:
                monto_neto = debito - credito
                asientos_contables.append(
                    {
                        "codigo_cuenta": codigo_cuenta,
                        "descripcion": descripcion,
                        "centro_costos": centro_costos,
                        "debito": float(monto_neto),
                        "credito": 0.0,
                    }
                )
                total_debitos += monto_neto
            elif credito > debito:
                monto_neto = credito - debito
                asientos_contables.append(
                    {
                        "codigo_cuenta": codigo_cuenta,
                        "descripcion": descripcion,
                        "centro_costos": centro_costos,
                        "debito": 0.0,
                        "credito": float(monto_neto),
                    }
                )
                total_creditos += monto_neto
            # If debito == credito, they cancel out, no entry needed

        # Sort by account code
        asientos_contables.sort(key=lambda x: (x["codigo_cuenta"], x["centro_costos"] or ""))

        # Calculate balance (should be 0 for balanced voucher)
        balance = total_debitos - total_creditos

        # Create or update comprobante
        comprobante = (
            self.session.execute(db.select(ComprobanteContable).filter_by(nomina_id=nomina.id)).scalar_one_or_none()
        )

        if comprobante:
            # Update existing
            comprobante.asientos_contables = asientos_contables
            comprobante.total_debitos = total_debitos
            comprobante.total_creditos = total_creditos
            comprobante.balance = balance
            comprobante.advertencias = warnings
        else:
            # Create new
            comprobante = ComprobanteContable(
                nomina_id=nomina.id,
                asientos_contables=asientos_contables,
                total_debitos=total_debitos,
                total_creditos=total_creditos,
                balance=balance,
                advertencias=warnings,
            )
            self.session.add(comprobante)

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
            # If debito == credito, they cancel out, no entry needed

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

        # Get all nomina employees
        nomina_empleados = (
            self.session.execute(
                db.select(NominaEmpleado)
                .join(ComprobanteContable, ComprobanteContable.nomina_id == NominaEmpleado.nomina_id)
                .filter(ComprobanteContable.id == comprobante.id)
            )
            .scalars()
            .all()
        )

        for ne in nomina_empleados:
            empleado = ne.empleado
            
            # Get all lines for this employee
            lineas = (
                self.session.execute(
                    db.select(ComprobanteContableLinea)
                    .filter_by(comprobante_id=comprobante.id, nomina_empleado_id=ne.id)
                    .order_by(ComprobanteContableLinea.orden)
                )
                .scalars()
                .all()
            )

            if lineas:  # Only include employees with accounting lines
                employee_entry = {
                    "empleado_codigo": empleado.codigo_empleado,
                    "empleado_nombre": f"{empleado.primer_nombre} {empleado.primer_apellido}",
                    "centro_costos": ne.centro_costos_snapshot or empleado.centro_costos,
                    "lineas": [
                        {
                            "concepto": linea.concepto,
                            "tipo_concepto": linea.tipo_concepto,
                            "codigo_cuenta": linea.codigo_cuenta,
                            "descripcion_cuenta": linea.descripcion_cuenta,
                            "debito": linea.debito,
                            "credito": linea.credito,
                        }
                        for linea in lineas
                    ],
                }
                detailed_entries.append(employee_entry)

        return detailed_entries

