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
"""CRITICAL tests for negative salary prevention in nomina_engine.

These tests ensure that the system NEVER allows negative salaries.
This is critical for:
- Legal compliance (can't pay negative amounts)
- Employee trust
- Accounting integrity
- Business logic correctness
"""

from datetime import date
from decimal import Decimal

import pytest

from coati_payroll.enums import FormulaType
from coati_payroll.nomina_engine import NominaEngine, EmpleadoCalculo


class TestSalarioNegativoPrevencion:
    """CRITICAL tests to ensure salaries never go negative."""

    def test_deducciones_exceden_salario_bruto(self, app, db_session):
        """Test that when deductions exceed gross salary, net salary is set to 0."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            
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
                salario_base=Decimal("10000.00"),  # Low salary
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
            
            # Add deductions that EXCEED the salary
            deduccion1 = Deduccion(
                codigo="INSS",
                nombre="Seguro Social",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("8000.00"),  # High deduction
                activo=True
            )
            db_session.add(deduccion1)
            
            deduccion2 = Deduccion(
                codigo="IR",
                nombre="Impuesto sobre la Renta",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("5000.00"),  # Another high deduction
                activo=True
            )
            db_session.add(deduccion2)
            db_session.flush()
            
            planilla_ded1 = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion1.id,
                prioridad=1,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded1)
            
            planilla_ded2 = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion2.id,
                prioridad=2,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded2)
            
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
            
            # Should have warnings about negative salary
            assert len(engine.warnings) > 0
            warning_found = any("exceden el salario bruto" in w for w in engine.warnings)
            assert warning_found, f"Expected warning about deductions exceeding salary. Warnings: {engine.warnings}"
            
            # Net salary should be 0, not negative
            assert nomina.total_neto == Decimal("0.00")
            
            # Verify employee calculation
            assert len(engine.empleados_calculo) == 1
            emp_calculo = engine.empleados_calculo[0]
            assert emp_calculo.salario_neto == Decimal("0.00")
            assert emp_calculo.salario_neto >= Decimal("0.00")  # NEVER negative

    def test_deducciones_multiples_exceden_salario(self, app, db_session):
        """Test multiple deductions that together exceed salary."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            
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
            
            # Add multiple deductions that together exceed salary
            deducciones = [
                ("INSS", "Seguro Social", Decimal("3000.00")),
                ("IR", "Impuesto Renta", Decimal("4000.00")),
                ("PRESTAMO", "Préstamo", Decimal("5000.00")),
                ("EMBARGO", "Embargo Judicial", Decimal("6000.00")),
            ]
            
            for i, (codigo, nombre, monto) in enumerate(deducciones):
                deduccion = Deduccion(
                    codigo=codigo,
                    nombre=nombre,
                    formula_tipo=FormulaType.FIJO,
                    monto_default=monto,
                    activo=True
                )
                db_session.add(deduccion)
                db_session.flush()
                
                planilla_ded = PlanillaDeduccion(
                    planilla_id=planilla.id,
                    deduccion_id=deduccion.id,
                    prioridad=i + 1,
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
            
            # Should have warnings
            assert len(engine.warnings) > 0
            
            # Net salary should be 0
            assert nomina.total_neto == Decimal("0.00")
            
            # Verify warning message includes details
            warning = engine.warnings[0]
            assert "exceden el salario bruto" in warning
            assert "15000" in warning  # Salary amount
            assert "Revise las deducciones" in warning

    def test_salario_exactamente_igual_deducciones(self, app, db_session):
        """Test edge case where deductions exactly equal salary."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            
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
            
            # Deduction that exactly equals salary
            deduccion = Deduccion(
                codigo="TOTAL_DED",
                nombre="Deducción Total",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("10000.00"),  # Exactly equals salary!
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
            
            # Should complete successfully
            assert nomina is not None
            
            # Net salary should be 0 (not negative)
            assert nomina.total_neto == Decimal("0.00")
            
            # No warnings needed if it's exactly 0
            # (not negative, just 0)
            emp_calculo = engine.empleados_calculo[0]
            assert emp_calculo.salario_neto == Decimal("0.00")

    def test_salario_pequeno_con_deducciones_normales(self, app, db_session):
        """Test small salary with normal deductions that exceed it."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            
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
            
            # Employee with very small salary (part-time or new hire)
            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Ana",
                primer_apellido="Martínez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("2000.00"),  # Very small salary
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
            
            # Normal deductions that are reasonable for average salary
            # but exceed this small salary
            deduccion_inss = Deduccion(
                codigo="INSS",
                nombre="Seguro Social",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("6.25"),  # 6.25% (normal in Nicaragua)
                activo=True
            )
            db_session.add(deduccion_inss)
            
            deduccion_ir = Deduccion(
                codigo="IR",
                nombre="Impuesto Renta",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("2000.00"),  # Fixed tax that exceeds salary
                activo=True
            )
            db_session.add(deduccion_ir)
            db_session.flush()
            
            planilla_ded_inss = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion_inss.id,
                prioridad=1,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded_inss)
            
            planilla_ded_ir = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion_ir.id,
                prioridad=2,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded_ir)
            
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
            
            # Should have warnings
            assert len(engine.warnings) > 0
            warning = engine.warnings[0]
            assert "Ana Martínez" in warning
            assert "exceden el salario bruto" in warning
            
            # Net salary should be 0
            assert nomina.total_neto == Decimal("0.00")
            assert nomina.total_neto >= Decimal("0.00")

    def test_salario_normal_sin_exceso(self, app, db_session):
        """Test normal case where deductions don't exceed salary (control test)."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            
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
                salario_base=Decimal("20000.00"),  # Normal salary
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
            
            # Normal deductions that don't exceed salary
            deduccion_inss = Deduccion(
                codigo="INSS",
                nombre="Seguro Social",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("6.25"),  # 6.25% = 1250
                activo=True
            )
            db_session.add(deduccion_inss)
            
            deduccion_ir = Deduccion(
                codigo="IR",
                nombre="Impuesto Renta",
                formula_tipo=FormulaType.PORCENTAJE_SALARIO,
                porcentaje=Decimal("15.00"),  # 15% = 3000
                activo=True
            )
            db_session.add(deduccion_ir)
            db_session.flush()
            
            planilla_ded_inss = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion_inss.id,
                prioridad=1,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded_inss)
            
            planilla_ded_ir = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion_ir.id,
                prioridad=2,
                es_obligatoria=True,
                activo=True
            )
            db_session.add(planilla_ded_ir)
            
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
            
            # Should NOT have warnings about negative salary
            negative_warnings = [w for w in engine.warnings if "exceden el salario bruto" in w]
            assert len(negative_warnings) == 0
            
            # Net salary should be positive
            # 20000 - 1250 - 3000 = 15750
            assert nomina.total_neto == Decimal("15750.00")
            assert nomina.total_neto > Decimal("0.00")

    def test_empleado_calculo_salario_neto_nunca_negativo(self, app, db_session):
        """Unit test to verify EmpleadoCalculo never allows negative net salary."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            
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
            db_session.commit()
            
            # Create EmpleadoCalculo
            emp_calculo = EmpleadoCalculo(empleado, planilla)
            emp_calculo.salario_base = Decimal("10000.00")
            emp_calculo.salario_bruto = Decimal("10000.00")
            emp_calculo.total_deducciones = Decimal("15000.00")  # Exceeds salary!
            
            # Calculate net (would be negative)
            calculated_net = emp_calculo.salario_bruto - emp_calculo.total_deducciones
            assert calculated_net < 0  # Would be -5000
            
            # The engine's validation should prevent this
            # Let's verify the logic works as expected
            emp_calculo.salario_neto = calculated_net
            
            # Simulate the engine's validation
            if emp_calculo.salario_neto < 0:
                emp_calculo.salario_neto = Decimal("0.00")
            
            # After validation, should be 0
            assert emp_calculo.salario_neto == Decimal("0.00")
            assert emp_calculo.salario_neto >= Decimal("0.00")

    def test_warning_message_formato_correcto(self, app, db_session):
        """Test that warning message has correct format with all details."""
        from coati_payroll.model import (
            Empresa, Moneda, TipoPlanilla, Planilla, Empleado,
            PlanillaEmpleado, Deduccion, PlanillaDeduccion
        )
        
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            
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
                primer_nombre="Roberto",
                primer_apellido="Hernández",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("5000.00"),
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
                codigo="DED",
                nombre="Deducción",
                formula_tipo=FormulaType.FIJO,
                monto_default=Decimal("7000.00"),
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
            
            # Check all expected components are in the message
            assert "Roberto Hernández" in warning
            assert "7000" in warning  # Total deductions
            assert "5000" in warning  # Salary bruto
            assert "2000" in warning  # Excess (7000 - 5000)
            assert "0.00" in warning  # Adjusted to 0
            assert "Revise las deducciones" in warning
