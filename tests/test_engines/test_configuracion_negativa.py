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
"""CRITICAL tests for negative deduction/perception configuration prevention.

These tests ensure that misconfigured deductions/perceptions with negative values
don't cause incorrect calculations (e.g., negative deduction would add to salary).
This is critical for:
- Mathematical correctness
- Preventing configuration errors from affecting payroll
- Data integrity
"""

from datetime import date
from decimal import Decimal

import pytest

from coati_payroll.enums import FormulaType
from coati_payroll.nomina_engine import NominaEngine, EmpleadoCalculo


class TestConfiguracionNegativaPrevencion:
    """CRITICAL tests to ensure negative configurations are handled safely."""

    def test_deduccion_porcentaje_negativo(self, app, db_session):
        """Test that negative percentage in deduction is adjusted to 0."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()
            
            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678"
            )
            db_session.add(empresa)
            db_session.flush()
            
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()
            
            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True
            )
            db_session.add(planilla)
            db_session.flush()
            
            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True
            )
            db_session.add(empleado)
            db_session.flush()
            
            planilla_emp = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True
            )
            db_session.add(planilla_emp)
            
            # MISCONFIGURED deduction with NEGATIVE percentage
            deduccion_mala = Deduccion(
                codigo="INSS_MAL",
                nombre="INSS Mal Configurado",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("-7.00"),  # NEGATIVE! This is wrong!
                activo=True
            )
            db_session.add(deduccion_mala)
            db_session.flush()
            
            planilla_ded = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion_mala.id,
                prioridad=1,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded)
            db_session.commit()
            
            # Execute payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2025, 1, 1),
                periodo_fin=date(2025, 1, 31),
                fecha_calculo=date(2025, 1, 31),
                usuario="admin"
            )
            
            nomina = engine.ejecutar()
            
            # Should complete successfully
            assert nomina is not None
            
            # Should have warning about negative configuration
            assert len(engine.warnings) > 0
            warning_found = any("monto negativo" in w and "INSS_MAL" in w for w in engine.warnings)
            assert warning_found, f"Expected warning about negative amount. Warnings: {engine.warnings}"
            
            # Negative percentage should be treated as 0, so no deduction applied
            # Net should equal gross
            assert nomina.total_neto == Decimal("10000.00")
            assert nomina.total_deducciones == Decimal("0.00")

    def test_deduccion_monto_fijo_negativo(self, app, db_session):
        """Test that negative fixed amount in deduction is adjusted to 0."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()
            
            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678"
            )
            db_session.add(empresa)
            db_session.flush()
            
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()
            
            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True
            )
            db_session.add(planilla)
            db_session.flush()
            
            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="María",
                primer_apellido="López",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True
            )
            db_session.add(empleado)
            db_session.flush()
            
            planilla_emp = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True
            )
            db_session.add(planilla_emp)
            
            # MISCONFIGURED deduction with NEGATIVE fixed amount
            deduccion_negativa = Deduccion(
                codigo="DED_NEG",
                nombre="Deducción Negativa",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("-500.00"),  # NEGATIVE! Error!
                activo=True
            )
            db_session.add(deduccion_negativa)
            db_session.flush()
            
            planilla_ded = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion_negativa.id,
                prioridad=1,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded)
            db_session.commit()
            
            # Execute payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2025, 1, 1),
                periodo_fin=date(2025, 1, 31),
                fecha_calculo=date(2025, 1, 31),
                usuario="admin"
            )
            
            nomina = engine.ejecutar()
            
            # Should complete successfully
            assert nomina is not None
            
            # Should have warning
            assert len(engine.warnings) > 0
            warning_found = any("monto negativo" in w for w in engine.warnings)
            assert warning_found
            
            # Negative amount should be treated as 0
            assert nomina.total_neto == Decimal("15000.00")
            assert nomina.total_deducciones == Decimal("0.00")

    def test_percepcion_porcentaje_negativo(self, app, db_session):
        """Test that negative percentage in perception is adjusted to 0."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Percepcion, PlanillaIngreso
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()
            
            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678"
            )
            db_session.add(empresa)
            db_session.flush()
            
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()
            
            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True
            )
            db_session.add(planilla)
            db_session.flush()
            
            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Carlos",
                primer_apellido="Ruiz",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("20000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True
            )
            db_session.add(empleado)
            db_session.flush()
            
            planilla_emp = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True
            )
            db_session.add(planilla_emp)
            
            # MISCONFIGURED perception with NEGATIVE percentage
            percepcion_negativa = Percepcion(
                codigo="BONO_NEG",
                nombre="Bono Negativo",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("-10.00"),  # NEGATIVE!
                gravable=True,
                activo=True
            )
            db_session.add(percepcion_negativa)
            db_session.flush()
            
            planilla_perc = PlanillaIngreso(
                planilla_id=planilla.id,
                percepcion_id=percepcion_negativa.id,
                orden=1,
                activo=True
            )
            db_session.add(planilla_perc)
            db_session.commit()
            
            # Execute payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2025, 1, 1),
                periodo_fin=date(2025, 1, 31),
                fecha_calculo=date(2025, 1, 31),
                usuario="admin"
            )
            
            nomina = engine.ejecutar()
            
            # Should complete successfully
            assert nomina is not None
            
            # Should have warning
            assert len(engine.warnings) > 0
            
            # Negative perception should be 0, so no addition to salary
            # Total bruto should equal base salary
            assert nomina.total_bruto == Decimal("20000.00")

    def test_deduccion_con_override_negativo(self, app, db_session):
        """Test that negative override value is adjusted to 0."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()
            
            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678"
            )
            db_session.add(empresa)
            db_session.flush()
            
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()
            
            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True
            )
            db_session.add(planilla)
            db_session.flush()
            
            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Ana",
                primer_apellido="Martínez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("12000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True
            )
            db_session.add(empleado)
            db_session.flush()
            
            planilla_emp = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True
            )
            db_session.add(planilla_emp)
            
            # Normal deduction but with NEGATIVE override in planilla
            deduccion = Deduccion(
                codigo="DED_NORMAL",
                nombre="Deducción Normal",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("100.00"),  # Normal positive
                activo=True
            )
            db_session.add(deduccion)
            db_session.flush()
            
            planilla_ded = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion.id,
                monto_predeterminado=Decimal("-200.00"),  # NEGATIVE override!
                prioridad=1,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded)
            db_session.commit()
            
            # Execute payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2025, 1, 1),
                periodo_fin=date(2025, 1, 31),
                fecha_calculo=date(2025, 1, 31),
                usuario="admin"
            )
            
            nomina = engine.ejecutar()
            
            # Should complete successfully
            assert nomina is not None
            
            # Should have warning
            assert len(engine.warnings) > 0
            
            # Negative override should be treated as 0
            assert nomina.total_deducciones == Decimal("0.00")

    def test_multiple_configuraciones_negativas(self, app, db_session):
        """Test handling of multiple misconfigured concepts with negative values."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion, 
            Percepcion, PlanillaIngreso
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()
            
            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678"
            )
            db_session.add(empresa)
            db_session.flush()
            
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()
            
            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True
            )
            db_session.add(planilla)
            db_session.flush()
            
            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Luis",
                primer_apellido="García",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("18000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True
            )
            db_session.add(empleado)
            db_session.flush()
            
            planilla_emp = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True
            )
            db_session.add(planilla_emp)
            
            # Multiple misconfigured concepts
            ded1 = Deduccion(
                codigo="DED1",
                nombre="Deducción 1",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("-5.00"),  # Negative!
                activo=True
            )
            db_session.add(ded1)
            
            ded2 = Deduccion(
                codigo="DED2",
                nombre="Deducción 2",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("-100.00"),  # Negative!
                activo=True
            )
            db_session.add(ded2)
            
            perc1 = Percepcion(
                codigo="PERC1",
                nombre="Percepción 1",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("-3.00"),  # Negative!
                gravable=True,
                activo=True
            )
            db_session.add(perc1)
            db_session.flush()
            
            for i, ded in enumerate([ded1, ded2]):
                pd = PlanillaDeduccion(
                    planilla_id=planilla.id,
                    deduccion_id=ded.id,
                    prioridad=i + 1,
                    es_obligatoria=True,
                    activo=True
                )
                db_session.add(pd)
            
            pi = PlanillaIngreso(
                planilla_id=planilla.id,
                percepcion_id=perc1.id,
                orden=1,
                activo=True
            )
            db_session.add(pi)
            db_session.commit()
            
            # Execute payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2025, 1, 1),
                periodo_fin=date(2025, 1, 31),
                fecha_calculo=date(2025, 1, 31),
                usuario="admin"
            )
            
            nomina = engine.ejecutar()
            
            # Should complete successfully
            assert nomina is not None
            
            # Should have multiple warnings (one for each negative config)
            assert len(engine.warnings) >= 3
            
            # All negatives should be 0, so net = gross = base
            assert nomina.total_bruto == Decimal("18000.00")
            assert nomina.total_deducciones == Decimal("0.00")
            assert nomina.total_neto == Decimal("18000.00")

    def test_warning_message_includes_concepto_name(self, app, db_session):
        """Test that warning message includes the concept code for identification."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()
            
            empresa = Empresa(
                codigo="TEST001",
                razon_social="Test Company SA",
                ruc="J-12345678"
            )
            db_session.add(empresa)
            db_session.flush()
            
            tipo_planilla = TipoPlanilla(
                codigo="MENSUAL",
                descripcion="Mensual",
                periodicidad="mensual",
                dias=30,
                periodos_por_anio=12,
                mes_inicio_fiscal=1,
                dia_inicio_fiscal=1,
            )
            db_session.add(tipo_planilla)
            db_session.flush()
            
            planilla = Planilla(
                nombre="Planilla Test",
                tipo_planilla_id=tipo_planilla.id,
                empresa_id=empresa.id,
                moneda_id=moneda.id,
                activo=True
            )
            db_session.add(planilla)
            db_session.flush()
            
            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Test",
                primer_apellido="User",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True
            )
            db_session.add(empleado)
            db_session.flush()
            
            planilla_emp = PlanillaEmpleado(
                planilla_id=planilla.id,
                empleado_id=empleado.id,
                activo=True
            )
            db_session.add(planilla_emp)
            
            deduccion = Deduccion(
                codigo="INSS_LABORAL_ERROR",  # Specific code for identification
                nombre="INSS Laboral",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("-7.00"),  # Negative!
                activo=True
            )
            db_session.add(deduccion)
            db_session.flush()
            
            planilla_ded = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion.id,
                prioridad=1,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded)
            db_session.commit()
            
            # Execute payroll
            engine = NominaEngine(
                planilla=planilla,
                periodo_inicio=date(2025, 1, 1),
                periodo_fin=date(2025, 1, 31),
                fecha_calculo=date(2025, 1, 31),
                usuario="admin"
            )
            
            nomina = engine.ejecutar()
            
            # Verify warning message format
            assert len(engine.warnings) > 0
            warning = engine.warnings[0]
            
            # Warning should include concept code for easy identification
            assert "INSS_LABORAL_ERROR" in warning
            assert "monto negativo" in warning
            assert "Verifique la configuración" in warning
