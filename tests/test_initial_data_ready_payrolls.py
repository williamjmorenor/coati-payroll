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


LCT_MARKER = "v_lct2019"


def _create_lct_seed_data():
    db.session.add(Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True))

    db.session.add(
        TipoPlanilla(
            codigo=f"bmonic_PLANILLA_MENSUAL{LCT_MARKER}",
            descripcion="Mensual",
            periodicidad="Monthly",
            dias=30,
            periodos_por_anio=12,
            activo=True,
        )
    )
    db.session.add(
        TipoPlanilla(
            codigo=f"bmonic_PLANILLA_AGUINALDO{LCT_MARKER}",
            descripcion="Aguinaldo",
            periodicidad="Monthly",
            dias=30,
            periodos_por_anio=1,
            activo=True,
        )
    )

    db.session.add(Percepcion(codigo=f"bmonic_HORAS_EXTRALCT_{LCT_MARKER}", nombre="HE", formula_tipo="formula"))
    db.session.add(Deduccion(codigo=f"bmonic_INSSLCT_{LCT_MARKER}", nombre="INSS", formula_tipo="formula"))
    db.session.add(Prestacion(codigo=f"bmonic_INATECLCT_{LCT_MARKER}", nombre="INATEC", formula_tipo="formula"))

    db.session.commit()


def test_load_plugin_ready_payrolls_creates_two_payrolls_with_associations(app, db_session):
    with app.app_context():
        _create_lct_seed_data()

        load_plugin_ready_payrolls()

        planillas = db.session.execute(
            db.select(Planilla).filter(Planilla.nombre.in_(["Planilla Mensual (LCT2019)", "Planilla Aguinaldo (LCT2019)"]))
        ).scalars().all()

        assert len(planillas) == 2

        for planilla in planillas:
            ingresos = db.session.execute(db.select(PlanillaIngreso).filter_by(planilla_id=planilla.id)).scalars().all()
            deducciones = db.session.execute(
                db.select(PlanillaDeduccion).filter_by(planilla_id=planilla.id)
            ).scalars().all()
            prestaciones = db.session.execute(
                db.select(PlanillaPrestacion).filter_by(planilla_id=planilla.id)
            ).scalars().all()

            assert len(ingresos) == 1
            assert len(deducciones) == 1
            assert len(prestaciones) == 1


def test_load_plugin_ready_payrolls_is_idempotent(app, db_session):
    with app.app_context():
        _create_lct_seed_data()

        load_plugin_ready_payrolls()
        load_plugin_ready_payrolls()

        assert db.session.execute(db.select(Planilla)).scalars().all()
        assert db.session.execute(db.select(PlanillaIngreso)).scalars().all()
        assert db.session.execute(db.select(PlanillaDeduccion)).scalars().all()
        assert db.session.execute(db.select(PlanillaPrestacion)).scalars().all()

        assert len(db.session.execute(db.select(Planilla)).scalars().all()) == 2
        assert len(db.session.execute(db.select(PlanillaIngreso)).scalars().all()) == 2
        assert len(db.session.execute(db.select(PlanillaDeduccion)).scalars().all()) == 2
        assert len(db.session.execute(db.select(PlanillaPrestacion)).scalars().all()) == 2
