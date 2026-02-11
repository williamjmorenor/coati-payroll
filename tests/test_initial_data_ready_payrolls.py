# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

from coati_payroll.initial_data import load_plugin_ready_payrolls
from coati_payroll.model import (
    Deduccion,
    Moneda,
    Percepcion,
    Planilla,
    PlanillaDeduccion,
    PlanillaIngreso,
    PlanillaPrestacion,
    Prestacion,
    TipoPlanilla,
    db,
)


PERCEPCIONES = {
    "bmonic_HORAS_EXTRAv_lct2019": "Horas Extras",
    "bmonic_SUBSIDIO_MEDICO_100v_lct2019": "Subsidio Médico 100%",
    "bmonic_SUBSIDIO_MEDICO_40v_lct2019": "Subsidio Médico 40%",
    "bmonic_VACACIONES_DESCANSADASv_lct2019": "Vacaciones Descansadas",
}

DEDUCCIONES = {
    "bmonic_INSSv_lct2019": "INSS Laboral",
    "bmonic_LLEGADAS_TARDEv_lct2019": "Deducción por Llegadas Tarde",
}

PRESTACIONES_DEFAULT = {
    "bmonic_AGUINALDOv_lct2019": "Provisión de Aguinaldo",
    "bmonic_INATECv_lct2019": "INATEC",
    "bmonic_INDEMNIZACION_LABORALv_lct2019": "Provisión Indemnización Laboral",
    "bmonic_INSS_PATRONAL_50PLUSv_lct2019": "INSS Patronal 50+ empleados",
}

PRESTACION_QUE_NO_SE_VINCULA = ("bmonic_INSS_PATRONAL_MINUS50v_lct2019", "INSS Patronal menos de 50 empleados")


EXPECTED_PLANILLAS = [
    "Planilla Mensual (LCT2019)",
    "Planilla Aguinaldo (LCT2019)",
]


def _seed_plugin_entities():
    db.session.add(Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True))

    db.session.add(
        TipoPlanilla(
            codigo="bmonic_PLANILLA_MENSUALv_lct2019",
            descripcion="Mensual",
            periodicidad="Monthly",
            dias=30,
            periodos_por_anio=12,
            activo=True,
        )
    )
    db.session.add(
        TipoPlanilla(
            codigo="bmonic_PLANILLA_AGUINALDOv_lct2019",
            descripcion="Aguinaldo",
            periodicidad="Monthly",
            dias=30,
            periodos_por_anio=1,
            activo=True,
        )
    )

    for codigo, nombre in PERCEPCIONES.items():
        db.session.add(Percepcion(codigo=codigo, nombre=nombre, formula_tipo="formula", activo=True))

    db.session.add(Deduccion(codigo="bmonic_INSSv_lct2019", nombre="INSS Laboral", formula_tipo="formula", activo=True))
    db.session.add(
        Deduccion(
            codigo="bmonic_LLEGADAS_TARDEv_lct2019",
            nombre="Deducción por Llegadas Tarde",
            formula_tipo="formula",
            activo=False,
        )
    )

    for codigo, nombre in PRESTACIONES_DEFAULT.items():
        db.session.add(Prestacion(codigo=codigo, nombre=nombre, formula_tipo="formula", activo=True))

    db.session.add(
        Prestacion(
            codigo=PRESTACION_QUE_NO_SE_VINCULA[0],
            nombre=PRESTACION_QUE_NO_SE_VINCULA[1],
            formula_tipo="formula",
            activo=True,
        )
    )

    db.session.commit()


def _linked_codes(planilla_id: str, association_model, relation_attr: str) -> set[str]:
    rows = db.session.execute(db.select(association_model).filter_by(planilla_id=planilla_id)).scalars().all()
    return {getattr(row, relation_attr).codigo for row in rows}


def test_load_plugin_ready_payrolls_creates_explicit_template_links(app, db_session):
    with app.app_context():
        _seed_plugin_entities()

        load_plugin_ready_payrolls()

        planillas = db.session.execute(db.select(Planilla).filter(Planilla.nombre.in_(EXPECTED_PLANILLAS))).scalars().all()

        assert len(planillas) == 2

        for planilla in planillas:
            percepciones = _linked_codes(planilla.id, PlanillaIngreso, "percepcion")
            deducciones = _linked_codes(planilla.id, PlanillaDeduccion, "deduccion")
            prestaciones = _linked_codes(planilla.id, PlanillaPrestacion, "prestacion")

            assert percepciones == set(PERCEPCIONES)
            assert deducciones == set(DEDUCCIONES)
            assert prestaciones == set(PRESTACIONES_DEFAULT)
            assert PRESTACION_QUE_NO_SE_VINCULA[0] not in prestaciones

            llegadas_tarde = db.session.execute(
                db.select(PlanillaDeduccion)
                .join(Deduccion, PlanillaDeduccion.deduccion_id == Deduccion.id)
                .filter(PlanillaDeduccion.planilla_id == planilla.id, Deduccion.codigo == "bmonic_LLEGADAS_TARDEv_lct2019")
            ).scalar_one_or_none()
            assert llegadas_tarde is not None
            assert llegadas_tarde.activo is False


def test_load_plugin_ready_payrolls_is_idempotent(app, db_session):
    with app.app_context():
        _seed_plugin_entities()

        load_plugin_ready_payrolls()
        load_plugin_ready_payrolls()

        assert len(db.session.execute(db.select(Planilla)).scalars().all()) == 2

        expected_per_planilla = len(PERCEPCIONES) + len(DEDUCCIONES) + len(PRESTACIONES_DEFAULT)
        expected_total_links = expected_per_planilla * 2

        total_links = (
            len(db.session.execute(db.select(PlanillaIngreso)).scalars().all())
            + len(db.session.execute(db.select(PlanillaDeduccion)).scalars().all())
            + len(db.session.execute(db.select(PlanillaPrestacion)).scalars().all())
        )
        assert total_links == expected_total_links
