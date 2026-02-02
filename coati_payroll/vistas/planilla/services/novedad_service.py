# SPDX-License-Identifier: Apache-2.0 \r\n # Copyright 2025 - 2026 BMO Soluciones, S.A.
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
"""Service for novedad business logic."""

from decimal import Decimal
from coati_payroll.model import db, Planilla, Nomina, NominaNovedad
from coati_payroll.vistas.planilla.helpers.form_helpers import get_concepto_ids_from_form


class NovedadService:
    """Service for novedad operations."""

    @staticmethod
    def listar_novedades(planilla: Planilla, nomina: Nomina) -> list:
        """List all novedades for a nomina.

        Args:
            planilla: The planilla
            nomina: The nomina

        Returns:
            List of NominaNovedad objects
        """
        # Get all employees in this planilla
        empleado_ids = [pe.empleado_id for pe in planilla.planilla_empleados if pe.activo]

        # Query novedades that fall within the nomina period and are for employees in this planilla
        novedades = (
            db.session.execute(
                db.select(NominaNovedad)
                .filter(
                    NominaNovedad.empleado_id.in_(empleado_ids),
                    NominaNovedad.fecha_novedad >= nomina.periodo_inicio,
                    NominaNovedad.fecha_novedad <= nomina.periodo_fin,
                )
                .order_by(NominaNovedad.fecha_novedad.desc(), NominaNovedad.timestamp.desc())
            )
            .scalars()
            .all()
        )

        return novedades

    @staticmethod
    def validar_fecha_novedad(fecha_novedad, nomina: Nomina) -> tuple[bool, str | None]:
        """Validate that fecha_novedad falls within the nomina period.

        Args:
            fecha_novedad: The date to validate
            nomina: The nomina

        Returns:
            Tuple of (is_valid, error_message)
        """
        from coati_payroll.i18n import _

        if fecha_novedad:
            if fecha_novedad < nomina.periodo_inicio or fecha_novedad > nomina.periodo_fin:
                return False, _(
                    "La fecha de la novedad debe estar dentro del período de la nómina " "({} a {})."
                ).format(
                    nomina.periodo_inicio.strftime("%d/%m/%Y"),
                    nomina.periodo_fin.strftime("%d/%m/%Y"),
                )
        return True, None

    @staticmethod
    def crear_novedad(nomina: Nomina, form, usuario: str) -> NominaNovedad:
        """Create a new novedad.

        Args:
            nomina: The nomina
            form: The form with novedad data
            usuario: Username of the user creating

        Returns:
            The created NominaNovedad
        """
        percepcion_id, deduccion_id = get_concepto_ids_from_form(form)

        novedad = NominaNovedad(
            nomina_id=nomina.id,
            empleado_id=form.empleado_id.data,
            codigo_concepto=form.codigo_concepto.data,
            tipo_valor=form.tipo_valor.data,
            valor_cantidad=Decimal(str(form.valor_cantidad.data)),
            fecha_novedad=form.fecha_novedad.data,
            percepcion_id=percepcion_id,
            deduccion_id=deduccion_id,
            creado_por=usuario,
        )
        db.session.add(novedad)
        db.session.commit()
        return novedad

    @staticmethod
    def actualizar_novedad(novedad: NominaNovedad, form, usuario: str):
        """Update an existing novedad.

        Args:
            novedad: The novedad to update
            form: The form with updated data
            usuario: Username of the user updating
        """
        percepcion_id, deduccion_id = get_concepto_ids_from_form(form)

        novedad.empleado_id = form.empleado_id.data
        novedad.codigo_concepto = form.codigo_concepto.data
        novedad.tipo_valor = form.tipo_valor.data
        novedad.valor_cantidad = Decimal(str(form.valor_cantidad.data))
        novedad.fecha_novedad = form.fecha_novedad.data
        novedad.percepcion_id = percepcion_id
        novedad.deduccion_id = deduccion_id
        novedad.modificado_por = usuario
        db.session.commit()
