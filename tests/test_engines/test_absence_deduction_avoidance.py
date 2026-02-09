# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Tests for absence (inasistencia) deduction avoidance.

This module validates that absences marked for payment discount don't get
double-deducted when they also exist as deductions in the planilla.

The system tracks three types of absences:
1. Absences that do NOT affect payment (es_inasistencia=True, descontar_pago_inasistencia=False)
2. Absences that ARE deducted from payment (es_inasistencia=True, descontar_pago_inasistencia=True)
3. Absences deducted from payment but paid in a different concept (tracked codes avoid double deduction)
"""

from datetime import date
from decimal import Decimal

import pytest

from coati_payroll.enums import FormulaType
from coati_payroll.nomina_engine.processors.novelty_processor import NoveltyProcessor
from coati_payroll.nomina_engine.calculators.deduction_calculator import DeductionCalculator
from coati_payroll.nomina_engine.calculators.concept_calculator import ConceptCalculator
from coati_payroll.nomina_engine.domain.employee_calculation import EmpleadoCalculo
from coati_payroll.nomina_engine.results.warning_collector import WarningCollector
from coati_payroll.nomina_engine.repositories.novelty_repository import NoveltyRepository
from coati_payroll.model import (
    db,
    Empresa,
    Moneda,
    TipoPlanilla,
    Planilla,
    Empleado,
    Deduccion,
    PlanillaDeduccion,
    NominaNovedad,
)


class TestNoveltyProcessor:
    """Tests for NoveltyProcessor with absence tracking."""

    def test_load_novelties_with_absence_discount_tracking(self, app, db_session):
        """Test that novelties with absence discount are tracked correctly."""
        with app.app_context():
            # Create basic setup
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678",
                
            )
            db_session.add(empresa)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()

            # Create novelties with and without payment discount
            novedad1 = NominaNovedad(
                nomina_id="test_nomina",
                empleado_id=empleado.id,
                codigo_concepto="AUSENCIA_JUSTIFICADA",
                valor_cantidad=Decimal("1.00"),
                tipo_valor="dias",
                fecha_novedad=date(2025, 1, 10),
                es_inasistencia=True,
                descontar_pago_inasistencia=False,  # No discount
            )
            db_session.add(novedad1)

            novedad2 = NominaNovedad(
                nomina_id="test_nomina",
                empleado_id=empleado.id,
                codigo_concepto="AUSENCIA_INJUSTIFICADA",
                valor_cantidad=Decimal("2.00"),
                tipo_valor="dias",
                fecha_novedad=date(2025, 1, 15),
                es_inasistencia=True,
                descontar_pago_inasistencia=True,  # With discount
            )
            db_session.add(novedad2)

            novedad3 = NominaNovedad(
                nomina_id="test_nomina",
                empleado_id=empleado.id,
                codigo_concepto="HORAS_EXTRA",
                valor_cantidad=Decimal("10.00"),
                tipo_valor="horas",
                fecha_novedad=date(2025, 1, 20),
                es_inasistencia=False,  # Not an absence
                descontar_pago_inasistencia=False,
            )
            db_session.add(novedad3)

            db_session.flush()
            db_session.commit()

            # Test NoveltyProcessor
            novelty_repo = NoveltyRepository(db_session)
            processor = NoveltyProcessor(novelty_repo)

            novedades, ausencia_resumen, codigos_descuento = processor.load_novelties_with_absences(
                empleado, date(2025, 1, 1), date(2025, 1, 31)
            )

            # Verify novelties are loaded
            assert "AUSENCIA_JUSTIFICADA" in novedades
            assert "AUSENCIA_INJUSTIFICADA" in novedades
            assert "HORAS_EXTRA" in novedades

            assert novedades["AUSENCIA_JUSTIFICADA"] == Decimal("1.00")
            assert novedades["AUSENCIA_INJUSTIFICADA"] == Decimal("2.00")
            assert novedades["HORAS_EXTRA"] == Decimal("10.00")

            # Verify only absences with discount are tracked
            assert ausencia_resumen["dias"] == Decimal("2.00")  # Only AUSENCIA_INJUSTIFICADA
            assert ausencia_resumen["horas"] == Decimal("0.00")

            # Verify discount codes are tracked
            assert "AUSENCIA_INJUSTIFICADA" in codigos_descuento
            assert "AUSENCIA_JUSTIFICADA" not in codigos_descuento
            assert "HORAS_EXTRA" not in codigos_descuento

    def test_load_novelties_with_hours_absence(self, app, db_session):
        """Test absence tracking with hours."""
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678",
                
            )
            db_session.add(empresa)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()

            # Create absence in hours
            novedad = NominaNovedad(
                nomina_id="test_nomina",
                empleado_id=empleado.id,
                codigo_concepto="AUSENCIA_HORAS",
                valor_cantidad=Decimal("4.00"),
                tipo_valor="horas",
                fecha_novedad=date(2025, 1, 15),
                es_inasistencia=True,
                descontar_pago_inasistencia=True,
            )
            db_session.add(novedad)
            db_session.flush()
            db_session.commit()

            # Test processor
            novelty_repo = NoveltyRepository(db_session)
            processor = NoveltyProcessor(novelty_repo)

            novedades, ausencia_resumen, codigos_descuento = processor.load_novelties_with_absences(
                empleado, date(2025, 1, 1), date(2025, 1, 31)
            )

            # Verify hours are tracked
            assert ausencia_resumen["dias"] == Decimal("0.00")
            assert ausencia_resumen["horas"] == Decimal("4.00")
            assert "AUSENCIA_HORAS" in codigos_descuento


