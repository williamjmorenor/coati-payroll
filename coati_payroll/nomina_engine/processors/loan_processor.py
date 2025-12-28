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
"""Loan processor for automatic loan and advance deductions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from coati_payroll.model import db, Adelanto, AdelantoAbono, Nomina, Liquidacion
from coati_payroll.enums import AdelantoEstado
from coati_payroll.i18n import _
from ..domain.calculation_items import DeduccionItem


class LoanProcessor:
    """Processor for automatic loan and advance deductions."""

    def __init__(
        self,
        nomina: Nomina | None,
        fecha_calculo: date,
        periodo_inicio: date,
        periodo_fin: date,
        liquidacion: Liquidacion | None = None,
        calcular_interes: bool = True,
    ):
        self.nomina = nomina
        self.liquidacion = liquidacion
        self.fecha_calculo = fecha_calculo
        self.periodo_inicio = periodo_inicio
        self.periodo_fin = periodo_fin
        self.calcular_interes = calcular_interes

    def process_loans(
        self, empleado_id: str, saldo_disponible: Decimal, aplicar_prestamos: bool, prioridad_prestamos: int
    ) -> list[DeduccionItem]:
        """Process loans for an employee."""
        deductions = []

        if not aplicar_prestamos:
            return deductions

        # Get active loans
        from sqlalchemy import select

        prestamos = list(
            db.session.execute(
                select(Adelanto).filter(
                    Adelanto.empleado_id == empleado_id,
                    Adelanto.estado == AdelantoEstado.APROBADO,
                    Adelanto.saldo_pendiente > 0,
                    Adelanto.deduccion_id.isnot(None),  # Only loans, not advances
                )
            )
            .scalars()
            .all()
        )

        for prestamo in prestamos:
            if saldo_disponible <= 0:
                break

            # Calculate and apply interest if applicable
            if self.calcular_interes:
                self._calculate_interest(prestamo)

            monto_cuota = Decimal(str(prestamo.monto_por_cuota or 0))
            if monto_cuota <= 0:
                continue

            monto_aplicar = min(monto_cuota, saldo_disponible)

            item = DeduccionItem(
                codigo=f"PRESTAMO_{prestamo.id[:8]}",
                nombre=f"Cuota préstamo - {prestamo.motivo or 'N/A'}",
                monto=monto_aplicar,
                prioridad=prioridad_prestamos,
                es_obligatoria=False,
                tipo="prestamo",
            )
            deductions.append(item)
            saldo_disponible -= monto_aplicar

            # Record the payment
            self._record_payment(prestamo, monto_aplicar)

        return deductions

    def process_advances(
        self, empleado_id: str, saldo_disponible: Decimal, aplicar_adelantos: bool, prioridad_adelantos: int
    ) -> list[DeduccionItem]:
        """Process salary advances for an employee."""
        deductions = []

        if not aplicar_adelantos:
            return deductions

        from sqlalchemy import select

        adelantos = list(
            db.session.execute(
                select(Adelanto).filter(
                    Adelanto.empleado_id == empleado_id,
                    Adelanto.estado == AdelantoEstado.APROBADO,
                    Adelanto.saldo_pendiente > 0,
                    Adelanto.deduccion_id.is_(None),  # Only advances, not loans
                )
            )
            .scalars()
            .all()
        )

        for adelanto in adelantos:
            if saldo_disponible <= 0:
                break

            monto_cuota = Decimal(str(adelanto.monto_por_cuota or adelanto.saldo_pendiente))
            monto_aplicar = min(monto_cuota, saldo_disponible)

            item = DeduccionItem(
                codigo=f"ADELANTO_{adelanto.id[:8]}",
                nombre=f"Adelanto salarial - {adelanto.motivo or 'N/A'}",
                monto=monto_aplicar,
                prioridad=prioridad_adelantos,
                es_obligatoria=False,
                tipo="adelanto",
            )
            deductions.append(item)
            saldo_disponible -= monto_aplicar

            # Record the payment
            self._record_payment(adelanto, monto_aplicar)

        return deductions

    def _calculate_interest(self, prestamo: Adelanto) -> None:
        """Calculate and apply interest for a loan."""
        from coati_payroll.interes_engine import calcular_interes_periodo
        from coati_payroll.model import InteresAdelanto

        tasa_interes = prestamo.tasa_interes or Decimal("0.0000")
        if tasa_interes <= 0:
            return

        if prestamo.saldo_pendiente <= 0:
            return

        fecha_desde = prestamo.fecha_ultimo_calculo_interes
        if not fecha_desde:
            fecha_desde = prestamo.fecha_desembolso or prestamo.fecha_aprobacion

        if not fecha_desde:
            return

        fecha_hasta = self.fecha_calculo

        if fecha_desde >= fecha_hasta:
            return

        tipo_interes = prestamo.tipo_interes or "simple"
        interes_calculado, dias = calcular_interes_periodo(
            saldo=prestamo.saldo_pendiente,
            tasa_anual=tasa_interes,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tipo_interes=tipo_interes,
        )

        if interes_calculado <= 0:
            return

        # Record interest in journal
        interes_entrada = InteresAdelanto(
            adelanto_id=prestamo.id,
            nomina_id=self.nomina.id if self.nomina else None,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            dias_transcurridos=dias,
            saldo_base=prestamo.saldo_pendiente,
            tasa_aplicada=tasa_interes,
            interes_calculado=interes_calculado,
            saldo_anterior=prestamo.saldo_pendiente,
            saldo_posterior=prestamo.saldo_pendiente + interes_calculado,
            observaciones=_("Interés calculado por nómina del {inicio} al {fin}").format(
                inicio=self.periodo_inicio, fin=self.periodo_fin
            ),
        )
        db.session.add(interes_entrada)

        # Update loan with interest
        prestamo.saldo_pendiente += interes_calculado
        prestamo.interes_acumulado = (prestamo.interes_acumulado or Decimal("0.00")) + interes_calculado
        prestamo.fecha_ultimo_calculo_interes = fecha_hasta

    def _record_payment(self, adelanto: Adelanto, monto: Decimal) -> None:
        """Record a payment towards a loan/advance."""
        saldo_anterior = Decimal(str(adelanto.saldo_pendiente))
        saldo_posterior = saldo_anterior - monto

        abono = AdelantoAbono(
            adelanto_id=adelanto.id,
            nomina_id=self.nomina.id if self.nomina else None,
            liquidacion_id=self.liquidacion.id if self.liquidacion else None,
            fecha_abono=self.fecha_calculo,
            monto_abonado=monto,
            saldo_anterior=saldo_anterior,
            saldo_posterior=max(saldo_posterior, Decimal("0.00")),
            tipo_abono="liquidacion" if self.liquidacion else "nomina",
        )
        db.session.add(abono)

        # Update adelanto balance
        adelanto.saldo_pendiente = max(saldo_posterior, Decimal("0.00"))
        if adelanto.saldo_pendiente <= 0:
            adelanto.estado = AdelantoEstado.PAGADO
