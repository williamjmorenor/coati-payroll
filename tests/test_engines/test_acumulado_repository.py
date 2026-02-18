# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Tests for AcumuladoRepository initialization behavior."""

from datetime import date
from decimal import Decimal

from coati_payroll.model import Moneda, Empresa, Empleado, TipoPlanilla, db
from coati_payroll.nomina_engine.repositories.acumulado_repository import AcumuladoRepository


class TestAcumuladoRepository:
    """Tests for annual accumulation bootstrap behavior."""

    def test_get_or_create_maps_midyear_implementation_balances(self, app, db_session):
        """It should map initial IR balance as retained tax and preserve closed fiscal periods."""
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Corp Inc", ruc="1234567")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="monthly",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Ir",
                primer_apellido="Midyear",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
                anio_implementacion_inicial=2025,
                mes_ultimo_cierre=7,
                salario_acumulado=Decimal("70416.67"),
                impuesto_acumulado=Decimal("1073.67"),
            )
            db_session.add(empleado)
            db_session.commit()

            repo = AcumuladoRepository(db.session)
            acumulado = repo.get_or_create(
                empleado=empleado,
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                periodo_fiscal_inicio=date(2025, 1, 1),
            )

            assert acumulado.salario_bruto_acumulado == Decimal("70416.67")
            assert acumulado.impuesto_retenido_acumulado == Decimal("1073.67")
            assert acumulado.deducciones_antes_impuesto_acumulado == Decimal("0.00")
            assert acumulado.periodos_procesados == 7

    def test_get_or_create_does_not_reapply_initial_balances_next_fiscal_year(self, app, db_session):
        """It should not carry bootstrap balances into a different fiscal year."""
        with app.app_context():
            moneda = Moneda(codigo="USD", nombre="Dollar", simbolo="$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST002", razon_social="Test Corp 2", ruc="7654321")
            db_session.add(empresa)
            db_session.flush()

            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL2",
                descripcion="Mensual",
                periodicidad="monthly",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP002",
                primer_nombre="Ir",
                primer_apellido="NoCarry",
                identificacion_personal="001-010180-0002A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
                anio_implementacion_inicial=2025,
                mes_ultimo_cierre=7,
                salario_acumulado=Decimal("70416.67"),
                impuesto_acumulado=Decimal("1073.67"),
            )
            db_session.add(empleado)
            db_session.commit()

            repo = AcumuladoRepository(db.session)
            acumulado = repo.get_or_create(
                empleado=empleado,
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                periodo_fiscal_inicio=date(2026, 1, 1),
            )

            assert acumulado.salario_bruto_acumulado == Decimal("0.00")
            assert acumulado.impuesto_retenido_acumulado == Decimal("0.00")
            assert acumulado.deducciones_antes_impuesto_acumulado == Decimal("0.00")
            assert acumulado.periodos_procesados == 0
