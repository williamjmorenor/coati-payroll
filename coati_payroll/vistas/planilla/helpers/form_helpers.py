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
"""Form helper functions for planilla views."""

from coati_payroll.model import db, TipoPlanilla, Moneda, Empresa, NominaEmpleado, Percepcion, Deduccion
from coati_payroll.forms import PlanillaForm
from coati_payroll.i18n import _
from sqlalchemy.orm import joinedload

# Constants
SELECT_PLACEHOLDER = "-- Seleccionar --"


def populate_form_choices(form: PlanillaForm):
    """Populate form select choices from database."""
    tipos = (
        db.session.execute(db.select(TipoPlanilla).filter_by(activo=True).order_by(TipoPlanilla.codigo)).scalars().all()
    )
    form.tipo_planilla_id.choices = [("", _(SELECT_PLACEHOLDER))] + [
        (t.id, f"{t.codigo} - {t.descripcion or t.codigo}") for t in tipos
    ]

    monedas = db.session.execute(db.select(Moneda).filter_by(activo=True).order_by(Moneda.codigo)).scalars().all()
    form.moneda_id.choices = [("", _(SELECT_PLACEHOLDER))] + [(m.id, f"{m.codigo} - {m.nombre}") for m in monedas]

    empresas = (
        db.session.execute(db.select(Empresa).filter_by(activo=True).order_by(Empresa.razon_social)).scalars().all()
    )
    form.empresa_id.choices = [("", _(SELECT_PLACEHOLDER))] + [
        (e.id, f"{e.codigo} - {e.razon_social}") for e in empresas
    ]


def populate_novedad_form_choices(form, nomina_id: str):
    """Populate form select choices for novedad form."""
    # Get employees associated with this nomina with eager loading
    nomina_empleados = (
        db.session.execute(
            db.select(NominaEmpleado).filter_by(nomina_id=nomina_id).options(joinedload(NominaEmpleado.empleado))
        )
        .scalars()
        .all()
    )
    form.empleado_id.choices = [("", _("-- Seleccionar Empleado --"))] + [
        (
            ne.empleado.id,
            f"{ne.empleado.primer_nombre} {ne.empleado.primer_apellido} ({ne.empleado.codigo_empleado})",
        )
        for ne in nomina_empleados
    ]

    # Get active percepciones
    percepciones = (
        db.session.execute(db.select(Percepcion).filter_by(activo=True).order_by(Percepcion.nombre)).scalars().all()
    )
    form.percepcion_id.choices = [("", _("-- Seleccionar Percepción --"))] + [
        (p.id, f"{p.codigo} - {p.nombre}") for p in percepciones
    ]

    # Get active deducciones
    deducciones = (
        db.session.execute(db.select(Deduccion).filter_by(activo=True).order_by(Deduccion.nombre)).scalars().all()
    )
    form.deduccion_id.choices = [("", _("-- Seleccionar Deducción --"))] + [
        (d.id, f"{d.codigo} - {d.nombre}") for d in deducciones
    ]


def get_concepto_ids_from_form(form) -> tuple[str | None, str | None]:
    """Extract percepcion_id and deduccion_id from form based on tipo_concepto.

    Args:
        form: The NominaNovedadForm with submitted data

    Returns:
        Tuple of (percepcion_id, deduccion_id) - one will be set, other will be None
    """
    percepcion_id = None
    deduccion_id = None

    if form.tipo_concepto.data == "percepcion":
        percepcion_id = form.percepcion_id.data if form.percepcion_id.data else None
    else:
        deduccion_id = form.deduccion_id.data if form.deduccion_id.data else None

    return percepcion_id, deduccion_id
