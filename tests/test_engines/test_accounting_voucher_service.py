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
"""Unit tests for AccountingVoucherService - accounting integration.

This module tests the accounting voucher generation service that handles:
- Accounting configuration validation
- Voucher generation from payroll calculations
- Base salary accounting entries
- Loan/advance accounting entries
- Concept (perception/deduction/benefit) accounting entries
- Cost center allocation
- Summarization and netting
- Audit trail tracking
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from coati_payroll.model import (
    db,
    Empresa,
    Moneda,
    TipoPlanilla,
    Planilla,
    Empleado,
    Nomina,
    NominaEmpleado,
    NominaDetalle,
    Percepcion,
    Deduccion,
    Prestacion,
    Adelanto,
    PlanillaIngreso,
    PlanillaDeduccion,
    PlanillaPrestacion,
    ComprobanteContable,
    ComprobanteContableLinea,
)
from coati_payroll.nomina_engine.services.accounting_voucher_service import AccountingVoucherService
from coati_payroll.enums import NominaEstado, AdelantoEstado


class TestAccountingConfigurationValidation:
    """Tests for accounting configuration validation."""

    def test_validate_complete_configuration(self, app, db_session):
        """Test validation passes when all accounts are configured."""
        with app.app_context():
            # Create test data with complete accounting configuration
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                # Accounting configuration for base salary
                codigo_cuenta_debe_salario="5101",
                descripcion_cuenta_debe_salario="Gasto por Salario",
                codigo_cuenta_haber_salario="2101",
                descripcion_cuenta_haber_salario="Salario por Pagar",
            )
            db_session.add(planilla)
            db_session.flush()

            # Create percepcion with accounting config
            percepcion = Percepcion(
                codigo="BONO",
                nombre="Bono Producción",
                formula_tipo="fijo",
                activo=True,
                contabilizable=True,
                codigo_cuenta_debe="5102",
                descripcion_cuenta_debe="Gasto por Bono",
                codigo_cuenta_haber="2102",
                descripcion_cuenta_haber="Bonos por Pagar",
            )
            db_session.add(percepcion)
            db_session.flush()

            # Link percepcion to planilla
            planilla_ingreso = PlanillaIngreso(
                planilla_id=planilla.id,
                percepcion_id=percepcion.id,
                activo=True,
            )
            db_session.add(planilla_ingreso)
            db_session.commit()

            # Test validation
            service = AccountingVoucherService(db_session)
            is_valid, warnings = service.validate_accounting_configuration(planilla)

            assert is_valid is True
            assert len(warnings) == 0

    def test_validate_missing_base_salary_accounts(self, app, db_session):
        """Test validation fails when base salary accounts are missing."""
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                # Missing accounting configuration
                codigo_cuenta_debe_salario=None,
                codigo_cuenta_haber_salario=None,
            )
            db_session.add(planilla)
            db_session.commit()

            service = AccountingVoucherService(db_session)
            is_valid, warnings = service.validate_accounting_configuration(planilla)

            assert is_valid is False
            assert len(warnings) == 2
            assert any("débito para salario básico" in w for w in warnings)
            assert any("crédito para salario básico" in w for w in warnings)

    def test_validate_missing_concept_accounts(self, app, db_session):
        """Test validation detects missing accounts in concepts."""
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                codigo_cuenta_debe_salario="5101",
                codigo_cuenta_haber_salario="2101",
            )
            db_session.add(planilla)
            db_session.flush()

            # Create deduccion without accounting config
            deduccion = Deduccion(
                codigo="INSS",
                nombre="INSS Laboral",
                formula_tipo="porcentaje",
                activo=True,
                contabilizable=True,
                codigo_cuenta_debe=None,  # Missing
                codigo_cuenta_haber=None,  # Missing
            )
            db_session.add(deduccion)
            db_session.flush()

            planilla_deduccion = PlanillaDeduccion(
                planilla_id=planilla.id,
                deduccion_id=deduccion.id,
                activo=True,
                prioridad=100,
            )
            db_session.add(planilla_deduccion)
            db_session.commit()

            service = AccountingVoucherService(db_session)
            is_valid, warnings = service.validate_accounting_configuration(planilla)

            assert is_valid is False
            assert len(warnings) == 2
            assert any("INSS Laboral" in w and "débito" in w for w in warnings)
            assert any("INSS Laboral" in w and "crédito" in w for w in warnings)


class TestAccountingVoucherGeneration:
    """Tests for accounting voucher generation."""

    def test_generate_voucher_base_salary(self, app, db_session):
        """Test voucher generation for base salary."""
        with app.app_context():
            # Setup
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                codigo_cuenta_debe_salario="5101",
                descripcion_cuenta_debe_salario="Gasto por Salario",
                codigo_cuenta_haber_salario="2101",
                descripcion_cuenta_haber_salario="Salario por Pagar",
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                centro_costos="CC-01",
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()

            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 31),
                estado=NominaEstado.GENERADO,
                total_bruto=Decimal("15000.00"),
                total_deducciones=Decimal("0.00"),
                total_neto=Decimal("15000.00"),
            )
            db_session.add(nomina)
            db_session.flush()

            nomina_empleado = NominaEmpleado(
                nomina_id=nomina.id,
                empleado_id=empleado.id,
                salario_bruto=Decimal("15000.00"),
                total_ingresos=Decimal("15000.00"),
                total_deducciones=Decimal("0.00"),
                salario_neto=Decimal("15000.00"),
                centro_costos_snapshot="CC-01",
                sueldo_base_historico=Decimal("15000.00"),
            )
            db_session.add(nomina_empleado)
            db_session.commit()

            # Generate voucher
            service = AccountingVoucherService(db_session)
            comprobante = service.generate_accounting_voucher(nomina, planilla, date(2024, 12, 31), "test_user")

            assert comprobante is not None
            assert comprobante.nomina_id == nomina.id
            assert comprobante.total_debitos == Decimal("15000.00")
            assert comprobante.total_creditos == Decimal("15000.00")
            assert comprobante.balance == Decimal("0.00")

            # Check lines
            lineas = db_session.query(ComprobanteContableLinea).filter_by(comprobante_id=comprobante.id).all()
            assert len(lineas) == 2  # Debit and credit

            linea_debe = [l for l in lineas if l.tipo_debito_credito == "debito"][0]
            assert linea_debe.codigo_cuenta == "5101"
            assert linea_debe.debito == Decimal("15000.00")
            assert linea_debe.centro_costos == "CC-01"
            assert linea_debe.empleado_codigo == "EMP001"

            linea_haber = [l for l in lineas if l.tipo_debito_credito == "credito"][0]
            assert linea_haber.codigo_cuenta == "2101"
            assert linea_haber.credito == Decimal("15000.00")
            assert linea_haber.centro_costos == "CC-01"

    def test_generate_voucher_with_null_cost_center(self, app, db_session):
        """Test voucher generation when employee has no cost center."""
        with app.app_context():
            # Setup similar to previous test but without cost center
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                codigo_cuenta_debe_salario="5101",
                codigo_cuenta_haber_salario="2101",
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP002",
                primer_nombre="Maria",
                primer_apellido="Lopez",
                identificacion_personal="002-020290-0002B",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("10000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                centro_costos=None,  # No cost center
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()

            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 31),
                estado=NominaEstado.GENERADO,
            )
            db_session.add(nomina)
            db_session.flush()

            nomina_empleado = NominaEmpleado(
                nomina_id=nomina.id,
                empleado_id=empleado.id,
                salario_bruto=Decimal("10000.00"),
                sueldo_base_historico=Decimal("10000.00"),
                centro_costos_snapshot=None,
            )
            db_session.add(nomina_empleado)
            db_session.commit()

            # Generate voucher
            service = AccountingVoucherService(db_session)
            comprobante = service.generate_accounting_voucher(nomina, planilla)

            # Check that lines have null cost center
            lineas = db_session.query(ComprobanteContableLinea).filter_by(comprobante_id=comprobante.id).all()
            assert all(l.centro_costos is None for l in lineas)

    def test_generate_voucher_with_loan(self, app, db_session):
        """Test voucher generation with loan deductions."""
        with app.app_context():
            # Setup
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                codigo_cuenta_debe_salario="5101",
                codigo_cuenta_haber_salario="2101",
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP003",
                primer_nombre="Carlos",
                primer_apellido="Martinez",
                identificacion_personal="003-030390-0003C",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                centro_costos="CC-02",
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()

            # Create loan deduction
            deduccion_prestamo = Deduccion(
                codigo="PREST",
                nombre="Préstamo",
                formula_tipo="fijo",
                activo=True,
                contabilizable=True,
            )
            db_session.add(deduccion_prestamo)
            db_session.flush()

            # Create active loan
            adelanto = Adelanto(
                empleado_id=empleado.id,
                deduccion_id=deduccion_prestamo.id,
                tipo="prestamo",
                monto_aprobado=Decimal("10000.00"),
                saldo_pendiente=Decimal("8000.00"),
                cuotas_pactadas=10,
                monto_por_cuota=Decimal("1000.00"),
                estado=AdelantoEstado.APLICADO,
                cuenta_haber="1301",  # Loan control account
            )
            db_session.add(adelanto)
            db_session.flush()

            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 31),
                estado=NominaEstado.GENERADO,
            )
            db_session.add(nomina)
            db_session.flush()

            nomina_empleado = NominaEmpleado(
                nomina_id=nomina.id,
                empleado_id=empleado.id,
                salario_bruto=Decimal("15000.00"),
                total_deducciones=Decimal("1000.00"),
                salario_neto=Decimal("14000.00"),
                sueldo_base_historico=Decimal("15000.00"),
                centro_costos_snapshot="CC-02",
            )
            db_session.add(nomina_empleado)
            db_session.flush()

            # Add loan deduction detail
            nomina_detalle = NominaDetalle(
                nomina_empleado_id=nomina_empleado.id,
                tipo="deduccion",
                codigo="PREST",
                descripcion="Cuota Préstamo",
                monto=Decimal("1000.00"),
                orden=1,
                deduccion_id=deduccion_prestamo.id,
            )
            db_session.add(nomina_detalle)
            db_session.commit()

            # Generate voucher
            service = AccountingVoucherService(db_session)
            comprobante = service.generate_accounting_voucher(nomina, planilla)

            # Check lines include loan entries
            lineas = db_session.query(ComprobanteContableLinea).filter_by(comprobante_id=comprobante.id).all()
            
            # Should have base salary (2 lines) + loan (2 lines) = 4 lines
            assert len(lineas) >= 4

            # Find loan lines
            loan_lines = [l for l in lineas if l.tipo_concepto == "prestamo"]
            assert len(loan_lines) == 2

            # Check loan debit (salary payable)
            loan_debe = [l for l in loan_lines if l.tipo_debito_credito == "debito"][0]
            assert loan_debe.codigo_cuenta == "2101"  # Salary payable
            assert loan_debe.debito == Decimal("1000.00")

            # Check loan credit (loan control)
            loan_haber = [l for l in loan_lines if l.tipo_debito_credito == "credito"][0]
            assert loan_haber.codigo_cuenta == "1301"  # Loan control
            assert loan_haber.credito == Decimal("1000.00")


class TestAccountingVoucherSummarization:
    """Tests for voucher summarization and netting."""

    def test_summarize_voucher_by_account_and_cost_center(self, app, db_session):
        """Test summarization groups by account and cost center."""
        with app.app_context():
            # Create comprobante with multiple lines for same account/cost center
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()

            comprobante = ComprobanteContable(
                nomina_id="test_nomina_id",
                fecha_calculo=date(2024, 12, 31),
                concepto="Test Voucher",
                moneda_id=moneda.id,
                total_debitos=Decimal("30000.00"),
                total_creditos=Decimal("30000.00"),
                balance=Decimal("0.00"),
            )
            db_session.add(comprobante)
            db_session.flush()

            # Add multiple debits to same account
            linea1 = ComprobanteContableLinea(
                comprobante_id=comprobante.id,
                nomina_empleado_id="ne1",
                empleado_id="emp1",
                empleado_codigo="EMP001",
                empleado_nombre="Juan Pérez",
                codigo_cuenta="5101",
                descripcion_cuenta="Gasto por Salario",
                centro_costos="CC-01",
                tipo_debito_credito="debito",
                debito=Decimal("15000.00"),
                credito=Decimal("0.00"),
                monto_calculado=Decimal("15000.00"),
                concepto="Salario Base",
                tipo_concepto="salario_base",
                concepto_codigo="SALARIO",
                orden=1,
            )
            db_session.add(linea1)

            linea2 = ComprobanteContableLinea(
                comprobante_id=comprobante.id,
                nomina_empleado_id="ne2",
                empleado_id="emp2",
                empleado_codigo="EMP002",
                empleado_nombre="Maria Lopez",
                codigo_cuenta="5101",  # Same account
                descripcion_cuenta="Gasto por Salario",
                centro_costos="CC-01",  # Same cost center
                tipo_debito_credito="debito",
                debito=Decimal("15000.00"),
                credito=Decimal("0.00"),
                monto_calculado=Decimal("15000.00"),
                concepto="Salario Base",
                tipo_concepto="salario_base",
                concepto_codigo="SALARIO",
                orden=2,
            )
            db_session.add(linea2)

            # Add credit
            linea3 = ComprobanteContableLinea(
                comprobante_id=comprobante.id,
                nomina_empleado_id="ne1",
                empleado_id="emp1",
                empleado_codigo="EMP001",
                empleado_nombre="Juan Pérez",
                codigo_cuenta="2101",
                descripcion_cuenta="Salario por Pagar",
                centro_costos="CC-01",
                tipo_debito_credito="credito",
                debito=Decimal("0.00"),
                credito=Decimal("15000.00"),
                monto_calculado=Decimal("15000.00"),
                concepto="Salario Base",
                tipo_concepto="salario_base",
                concepto_codigo="SALARIO",
                orden=3,
            )
            db_session.add(linea3)

            linea4 = ComprobanteContableLinea(
                comprobante_id=comprobante.id,
                nomina_empleado_id="ne2",
                empleado_id="emp2",
                empleado_codigo="EMP002",
                empleado_nombre="Maria Lopez",
                codigo_cuenta="2101",  # Same account
                descripcion_cuenta="Salario por Pagar",
                centro_costos="CC-01",  # Same cost center
                tipo_debito_credito="credito",
                debito=Decimal("0.00"),
                credito=Decimal("15000.00"),
                monto_calculado=Decimal("15000.00"),
                concepto="Salario Base",
                tipo_concepto="salario_base",
                concepto_codigo="SALARIO",
                orden=4,
            )
            db_session.add(linea4)
            db_session.commit()

            # Summarize
            service = AccountingVoucherService(db_session)
            summarized = service.summarize_voucher(comprobante)

            # Should have 2 entries (one debit, one credit)
            assert len(summarized) == 2

            # Check debit summarization
            debit_entry = [e for e in summarized if e["codigo_cuenta"] == "5101"][0]
            assert debit_entry["debito"] == Decimal("30000.00")
            assert debit_entry["credito"] == Decimal("0.00")
            assert debit_entry["centro_costos"] == "CC-01"

            # Check credit summarization
            credit_entry = [e for e in summarized if e["codigo_cuenta"] == "2101"][0]
            assert credit_entry["debito"] == Decimal("0.00")
            assert credit_entry["credito"] == Decimal("30000.00")
            assert credit_entry["centro_costos"] == "CC-01"

    def test_summarize_voucher_nets_debits_and_credits(self, app, db_session):
        """Test summarization nets debits and credits for same account/cost center."""
        with app.app_context():
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)
            db_session.flush()

            comprobante = ComprobanteContable(
                nomina_id="test_nomina_id",
                fecha_calculo=date(2024, 12, 31),
                concepto="Test Voucher",
                moneda_id=moneda.id,
                total_debitos=Decimal("20000.00"),
                total_creditos=Decimal("20000.00"),
                balance=Decimal("0.00"),
            )
            db_session.add(comprobante)
            db_session.flush()

            # Add debit
            linea1 = ComprobanteContableLinea(
                comprobante_id=comprobante.id,
                nomina_empleado_id="ne1",
                empleado_id="emp1",
                empleado_codigo="EMP001",
                empleado_nombre="Juan Pérez",
                codigo_cuenta="2101",  # Same account for both debit and credit
                descripcion_cuenta="Salario por Pagar",
                centro_costos="CC-01",
                tipo_debito_credito="debito",
                debito=Decimal("5000.00"),  # Loan payment debits salary payable
                credito=Decimal("0.00"),
                monto_calculado=Decimal("5000.00"),
                concepto="Préstamo",
                tipo_concepto="prestamo",
                concepto_codigo="PREST",
                orden=1,
            )
            db_session.add(linea1)

            # Add credit to same account
            linea2 = ComprobanteContableLinea(
                comprobante_id=comprobante.id,
                nomina_empleado_id="ne1",
                empleado_id="emp1",
                empleado_codigo="EMP001",
                empleado_nombre="Juan Pérez",
                codigo_cuenta="2101",  # Same account
                descripcion_cuenta="Salario por Pagar",
                centro_costos="CC-01",  # Same cost center
                tipo_debito_credito="credito",
                debito=Decimal("0.00"),
                credito=Decimal("20000.00"),  # Salary credits salary payable
                monto_calculado=Decimal("20000.00"),
                concepto="Salario Base",
                tipo_concepto="salario_base",
                concepto_codigo="SALARIO",
                orden=2,
            )
            db_session.add(linea2)
            db_session.commit()

            # Summarize
            service = AccountingVoucherService(db_session)
            summarized = service.summarize_voucher(comprobante)

            # Should have 1 entry with netted amount
            assert len(summarized) == 1

            entry = summarized[0]
            assert entry["codigo_cuenta"] == "2101"
            # Credit (20000) - Debit (5000) = 15000 net credit
            assert entry["debito"] == Decimal("0.00")
            assert entry["credito"] == Decimal("15000.00")


class TestAccountingAuditTrail:
    """Tests for audit trail tracking."""

    def test_audit_trail_on_creation(self, app, db_session):
        """Test audit trail is set correctly on creation."""
        with app.app_context():
            # Setup
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                codigo_cuenta_debe_salario="5101",
                codigo_cuenta_haber_salario="2101",
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()

            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 31),
                estado=NominaEstado.APLICADO,  # Applied state
                aplicado_por="admin_user",
                aplicado_en=datetime(2024, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
            )
            db_session.add(nomina)
            db_session.flush()

            nomina_empleado = NominaEmpleado(
                nomina_id=nomina.id,
                empleado_id=empleado.id,
                salario_bruto=Decimal("15000.00"),
                sueldo_base_historico=Decimal("15000.00"),
            )
            db_session.add(nomina_empleado)
            db_session.commit()

            # Generate voucher
            service = AccountingVoucherService(db_session)
            comprobante = service.generate_accounting_voucher(nomina, planilla, usuario="test_user")

            # Check audit trail
            assert comprobante.aplicado_por == "admin_user"
            assert comprobante.fecha_aplicacion is not None
            assert comprobante.veces_modificado == 0
            assert comprobante.modificado_por is None

    def test_audit_trail_on_regeneration(self, app, db_session):
        """Test audit trail is updated on regeneration."""
        with app.app_context():
            # Setup with existing comprobante
            moneda = Moneda(codigo="NIO", nombre="Córdoba", simbolo="C$", activo=True)
            db_session.add(moneda)

            empresa = Empresa(codigo="TEST001", razon_social="Test Company SA", ruc="J-12345678")
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
                activo=True,
                codigo_cuenta_debe_salario="5101",
                codigo_cuenta_haber_salario="2101",
            )
            db_session.add(planilla)
            db_session.flush()

            empleado = Empleado(
                codigo_empleado="EMP001",
                primer_nombre="Juan",
                primer_apellido="Pérez",
                identificacion_personal="001-010180-0001A",
                fecha_alta=date(2024, 1, 1),
                salario_base=Decimal("15000.00"),
                moneda_id=moneda.id,
                empresa_id=empresa.id,
                activo=True,
            )
            db_session.add(empleado)
            db_session.flush()

            nomina = Nomina(
                planilla_id=planilla.id,
                periodo_inicio=date(2024, 12, 1),
                periodo_fin=date(2024, 12, 31),
                estado=NominaEstado.APLICADO,
            )
            db_session.add(nomina)
            db_session.flush()

            nomina_empleado = NominaEmpleado(
                nomina_id=nomina.id,
                empleado_id=empleado.id,
                salario_bruto=Decimal("15000.00"),
                sueldo_base_historico=Decimal("15000.00"),
            )
            db_session.add(nomina_empleado)
            db_session.commit()

            # First generation
            service = AccountingVoucherService(db_session)
            comprobante = service.generate_accounting_voucher(nomina, planilla, usuario="first_user")
            db_session.commit()

            original_aplicado_por = comprobante.aplicado_por
            assert comprobante.veces_modificado == 0

            # Regenerate
            comprobante = service.generate_accounting_voucher(nomina, planilla, usuario="second_user")
            db_session.commit()

            # Check audit trail updated
            assert comprobante.aplicado_por == original_aplicado_por  # Immutable
            assert comprobante.modificado_por == "second_user"
            assert comprobante.fecha_modificacion is not None
            assert comprobante.veces_modificado == 1

            # Regenerate again
            comprobante = service.generate_accounting_voucher(nomina, planilla, usuario="third_user")
            db_session.commit()

            assert comprobante.veces_modificado == 2
            assert comprobante.modificado_por == "third_user"
