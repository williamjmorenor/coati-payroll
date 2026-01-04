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

from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest

from coati_payroll.model import Empresa, Empleado, Liquidacion, LiquidacionDetalle


def test_exportar_liquidacion_excel_success(app, db_session):
    with app.app_context():
        from coati_payroll.vistas.planilla.services.export_service import ExportService

        empresa = Empresa(codigo="E1", razon_social="Empresa", ruc="RUC", activo=True)
        db_session.add(empresa)
        db_session.flush()

        empleado = Empleado(
            empresa_id=empresa.id,
            codigo_empleado="EMPX",
            primer_nombre="Juan",
            primer_apellido="Perez",
            identificacion_personal="ID-EMPX",
            fecha_alta=date(2025, 1, 1),
            salario_base=Decimal("300.00"),
            activo=True,
        )
        db_session.add(empleado)
        db_session.flush()

        liquidacion = Liquidacion(
            empleado_id=empleado.id,
            fecha_calculo=date(2025, 1, 1),
            ultimo_dia_pagado=date(2024, 12, 31),
            dias_por_pagar=1,
            estado="borrador",
            total_bruto=Decimal("10.00"),
            total_deducciones=Decimal("0.00"),
            total_neto=Decimal("10.00"),
        )
        db_session.add(liquidacion)
        db_session.flush()

        d1 = LiquidacionDetalle(
            liquidacion_id=liquidacion.id,
            tipo="ingreso",
            codigo="DIAS_POR_PAGAR",
            descripcion="Días por pagar",
            monto=Decimal("10.00"),
            orden=1,
        )
        db_session.add(d1)
        db_session.commit()

        output, filename = ExportService.exportar_liquidacion_excel(liquidacion)

        assert isinstance(output, BytesIO)
        assert filename.startswith("liquidacion_")
        output.seek(0)
        content = output.read()
        assert content.startswith(b"PK")


def test_exportar_liquidacion_excel_missing_openpyxl(app, db_session, monkeypatch):
    with app.app_context():
        from coati_payroll.vistas.planilla.services import export_service
        from coati_payroll.vistas.planilla.services.export_service import ExportService

        def mock_check_openpyxl():
            return None

        monkeypatch.setattr(export_service, "check_openpyxl_available", mock_check_openpyxl)

        liquidacion = Liquidacion(
            empleado_id="dummy",
            fecha_calculo=date(2025, 1, 1),
            dias_por_pagar=0,
            estado="borrador",
        )

        with pytest.raises(ImportError, match="openpyxl no está disponible"):
            ExportService.exportar_liquidacion_excel(liquidacion)
