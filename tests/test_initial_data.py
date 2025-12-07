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
"""Tests for initial data loading functionality."""

from __future__ import annotations

from coati_payroll.initial_data import (
    CURRENCIES,
    INCOME_CONCEPTS,
    DEDUCTION_CONCEPTS,
    BENEFIT_CONCEPTS,
    PAYROLL_TYPES,
    load_currencies,
    load_income_concepts,
    load_deduction_concepts,
    load_benefit_concepts,
    load_payroll_types,
    load_initial_data,
)
from coati_payroll.model import Moneda, Percepcion, Deduccion, Prestacion, TipoPlanilla, db


class TestInitialDataConstants:
    """Test the initial data constants."""

    def test_currencies_not_empty(self):
        """Test that currencies list is not empty."""
        assert len(CURRENCIES) > 0

    def test_currencies_have_required_fields(self):
        """Test that all currencies have required fields."""
        for currency in CURRENCIES:
            assert "codigo" in currency
            assert "nombre" in currency
            assert "simbolo" in currency

    def test_currencies_have_valid_codes(self):
        """Test that all currency codes are 3 characters."""
        for currency in CURRENCIES:
            assert len(currency["codigo"]) == 3
            assert currency["codigo"].isupper()

    def test_currencies_are_unique(self):
        """Test that all currency codes are unique."""
        codes = [c["codigo"] for c in CURRENCIES]
        assert len(codes) == len(set(codes))

    def test_income_concepts_not_empty(self):
        """Test that income concepts list is not empty."""
        assert len(INCOME_CONCEPTS) > 0

    def test_income_concepts_have_required_fields(self):
        """Test that all income concepts have required fields."""
        for concept in INCOME_CONCEPTS:
            assert "codigo" in concept
            assert "nombre" in concept
            assert "descripcion" in concept

    def test_income_concepts_are_unique(self):
        """Test that all income concept codes are unique."""
        codes = [c["codigo"] for c in INCOME_CONCEPTS]
        assert len(codes) == len(set(codes))

    def test_deduction_concepts_not_empty(self):
        """Test that deduction concepts list is not empty."""
        assert len(DEDUCTION_CONCEPTS) > 0

    def test_deduction_concepts_have_required_fields(self):
        """Test that all deduction concepts have required fields."""
        for concept in DEDUCTION_CONCEPTS:
            assert "codigo" in concept
            assert "nombre" in concept
            assert "descripcion" in concept

    def test_deduction_concepts_are_unique(self):
        """Test that all deduction concept codes are unique."""
        codes = [c["codigo"] for c in DEDUCTION_CONCEPTS]
        assert len(codes) == len(set(codes))

    def test_american_currencies_included(self):
        """Test that key American currencies are included."""
        codes = [c["codigo"] for c in CURRENCIES]
        # Check for major currencies
        assert "USD" in codes  # United States
        assert "CAD" in codes  # Canada
        assert "MXN" in codes  # Mexico
        assert "BRL" in codes  # Brazil
        assert "ARS" in codes  # Argentina
        assert "NIO" in codes  # Nicaragua

    def test_income_concepts_use_english_codes(self):
        """Test that income concept codes are in English, not Spanish."""
        codes = [c["codigo"] for c in INCOME_CONCEPTS]
        # Verify the codes mentioned in the issue are now in English
        assert "GOAL_INCENTIVES" in codes
        assert "SEVERANCE_PAY" in codes
        assert "PAID_LICENSE" in codes
        assert "RETROACTIVE_PAYMENTS" in codes
        assert "PAID_LEAVE" in codes
        assert "REPORTED_TIPS" in codes
        assert "PAID_VACATION" in codes
        # Verify old Spanish codes are NOT present
        assert "INCENTIVOS_METAS" not in codes
        assert "INDEMNIZACION_SALARIAL" not in codes
        assert "LICENCIAS_REMUNERADAS" not in codes
        assert "PAGOS_RETROACTIVOS" not in codes
        assert "PERMISOS_REMUNERADOS" not in codes
        assert "PROPINAS" not in codes
        assert "VACACIONES_PAGADAS" not in codes

    def test_deduction_concepts_use_english_codes(self):
        """Test that deduction concept codes are in English, not Spanish."""
        codes = [c["codigo"] for c in DEDUCTION_CONCEPTS]
        # Verify all codes are in English
        assert "SALARY_ADVANCE" in codes
        assert "VOLUNTARY_RETIREMENT" in codes
        assert "CAFETERIA" in codes
        assert "INTERNAL_LOANS" in codes
        assert "ALIMONY" in codes
        assert "UNION_DUES" in codes
        # Verify old Spanish codes are NOT present
        assert "ADELANTO_SALARIO" not in codes
        assert "PLAN_RETIRO_VOLUNTARIO" not in codes
        assert "COMEDOR" not in codes
        assert "PRESTAMOS_INTERNOS" not in codes
        assert "PENSION_ALIMENTICIA" not in codes
        assert "CUOTA_SINDICAL" not in codes

    def test_benefit_concepts_not_empty(self):
        """Test that benefit concepts list is not empty."""
        assert len(BENEFIT_CONCEPTS) > 0

    def test_benefit_concepts_have_required_fields(self):
        """Test that all benefit concepts have required fields."""
        for concept in BENEFIT_CONCEPTS:
            assert "codigo" in concept
            assert "nombre" in concept
            assert "descripcion" in concept

    def test_benefit_concepts_are_unique(self):
        """Test that all benefit concept codes are unique."""
        codes = [c["codigo"] for c in BENEFIT_CONCEPTS]
        assert len(codes) == len(set(codes))

    def test_benefit_concepts_include_three_main_concepts(self):
        """Test that the three main labor concepts in the Americas are included."""
        codes = [c["codigo"] for c in BENEFIT_CONCEPTS]
        # Paid Vacation - Universal right
        assert "PAID_VACATION_PROVISION" in codes
        # 13th Month Salary/Aguinaldo - Very widespread right
        assert "THIRTEENTH_SALARY_PROVISION" in codes
        # Severance Pay - Common legal principle
        assert "SEVERANCE_PROVISION" in codes
    def test_payroll_types_not_empty(self):
        """Test that payroll types list is not empty."""
        assert len(PAYROLL_TYPES) > 0

    def test_payroll_types_have_required_fields(self):
        """Test that all payroll types have required fields."""
        for payroll_type in PAYROLL_TYPES:
            assert "codigo" in payroll_type
            assert "descripcion" in payroll_type
            assert "dias" in payroll_type
            assert "periodicidad" in payroll_type
            assert "periodos_por_anio" in payroll_type

    def test_payroll_types_are_unique(self):
        """Test that all payroll type codes are unique."""
        codes = [pt["codigo"] for pt in PAYROLL_TYPES]
        assert len(codes) == len(set(codes))

    def test_payroll_types_use_english_codes(self):
        """Test that payroll type codes are in English."""
        codes = [pt["codigo"] for pt in PAYROLL_TYPES]
        # Verify all codes are in English
        assert "MONTHLY" in codes
        assert "BIWEEKLY" in codes
        assert "FORTNIGHTLY" in codes
        assert "WEEKLY" in codes

    def test_payroll_types_have_correct_values(self):
        """Test that payroll types have the correct values."""
        monthly = next((pt for pt in PAYROLL_TYPES if pt["codigo"] == "MONTHLY"), None)
        assert monthly is not None
        assert monthly["dias"] == 30
        assert monthly["periodos_por_anio"] == 12

        biweekly = next((pt for pt in PAYROLL_TYPES if pt["codigo"] == "BIWEEKLY"), None)
        assert biweekly is not None
        assert biweekly["dias"] == 15
        assert biweekly["periodos_por_anio"] == 24

        fortnightly = next((pt for pt in PAYROLL_TYPES if pt["codigo"] == "FORTNIGHTLY"), None)
        assert fortnightly is not None
        assert fortnightly["dias"] == 14
        assert fortnightly["periodos_por_anio"] == 26

        weekly = next((pt for pt in PAYROLL_TYPES if pt["codigo"] == "WEEKLY"), None)
        assert weekly is not None
        assert weekly["dias"] == 7
        assert weekly["periodos_por_anio"] == 52


class TestLoadCurrencies:
    """Test currency loading functionality."""

    def test_load_currencies(self, app):
        """Test loading currencies."""
        with app.app_context():
            # Clear existing currencies first
            db.session.execute(db.delete(Moneda))
            db.session.commit()

            load_currencies()

            # Check that currencies were loaded
            currencies = db.session.execute(db.select(Moneda)).scalars().all()
            assert len(currencies) >= len(CURRENCIES)

            # Check a specific currency
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one_or_none()
            assert usd is not None
            assert usd.codigo == "USD"
            assert usd.simbolo == "$"
            assert usd.activo is True

    def test_load_currencies_no_duplicates(self, app):
        """Test that loading currencies twice doesn't create duplicates."""
        with app.app_context():
            # Load currencies twice
            load_currencies()
            count_first = db.session.execute(db.select(Moneda)).scalars().all()

            load_currencies()
            count_second = db.session.execute(db.select(Moneda)).scalars().all()

            # Should have same count
            assert len(count_first) == len(count_second)

    def test_load_currencies_nicaraguan_cordoba(self, app):
        """Test that Nicaraguan Córdoba is included."""
        with app.app_context():
            load_currencies()

            nio = db.session.execute(db.select(Moneda).filter_by(codigo="NIO")).scalar_one_or_none()
            assert nio is not None
            assert nio.codigo == "NIO"


class TestLoadIncomeConcepts:
    """Test income concept loading functionality."""

    def test_load_income_concepts(self, app):
        """Test loading income concepts."""
        with app.app_context():
            # Clear existing concepts first
            db.session.execute(db.delete(Percepcion))
            db.session.commit()

            load_income_concepts()

            # Check that concepts were loaded
            concepts = db.session.execute(db.select(Percepcion)).scalars().all()
            assert len(concepts) >= len(INCOME_CONCEPTS)

            # Check a specific concept
            overtime = db.session.execute(db.select(Percepcion).filter_by(codigo="OVERTIME")).scalar_one_or_none()
            assert overtime is not None
            assert overtime.codigo == "OVERTIME"
            assert overtime.activo is True

    def test_load_income_concepts_no_duplicates(self, app):
        """Test that loading income concepts twice doesn't create duplicates."""
        with app.app_context():
            # Load concepts twice
            load_income_concepts()
            count_first = db.session.execute(db.select(Percepcion)).scalars().all()

            load_income_concepts()
            count_second = db.session.execute(db.select(Percepcion)).scalars().all()

            # Should have same count
            assert len(count_first) == len(count_second)

    def test_income_concepts_have_correct_properties(self, app):
        """Test that loaded income concepts have correct properties."""
        with app.app_context():
            load_income_concepts()

            # Get all loaded concepts
            concepts = db.session.execute(db.select(Percepcion)).scalars().all()

            for concept in concepts:
                # Check that they are active and editable
                assert concept.activo is True
                assert concept.editable_en_nomina is True
                # Check formula type is set
                assert concept.formula_tipo is not None


class TestLoadDeductionConcepts:
    """Test deduction concept loading functionality."""

    def test_load_deduction_concepts(self, app):
        """Test loading deduction concepts."""
        with app.app_context():
            # Clear existing concepts first
            db.session.execute(db.delete(Deduccion))
            db.session.commit()

            load_deduction_concepts()

            # Check that concepts were loaded
            concepts = db.session.execute(db.select(Deduccion)).scalars().all()
            assert len(concepts) >= len(DEDUCTION_CONCEPTS)

            # Check a specific concept
            advance = db.session.execute(db.select(Deduccion).filter_by(codigo="SALARY_ADVANCE")).scalar_one_or_none()
            assert advance is not None
            assert advance.codigo == "SALARY_ADVANCE"
            assert advance.activo is True

    def test_load_deduction_concepts_no_duplicates(self, app):
        """Test that loading deduction concepts twice doesn't create duplicates."""
        with app.app_context():
            # Load concepts twice
            load_deduction_concepts()
            count_first = db.session.execute(db.select(Deduccion)).scalars().all()

            load_deduction_concepts()
            count_second = db.session.execute(db.select(Deduccion)).scalars().all()

            # Should have same count
            assert len(count_first) == len(count_second)

    def test_deduction_concepts_have_correct_properties(self, app):
        """Test that loaded deduction concepts have correct properties."""
        with app.app_context():
            load_deduction_concepts()

            # Get all loaded concepts
            concepts = db.session.execute(db.select(Deduccion)).scalars().all()

            for concept in concepts:
                # Check that they are active and editable
                assert concept.activo is True
                assert concept.editable_en_nomina is True
                # Check formula type is set
                assert concept.formula_tipo is not None
                # Check they are not marked as tax by default
                assert concept.es_impuesto is False


class TestLoadBenefitConcepts:
    """Test employer benefit concept loading functionality."""

    def test_load_benefit_concepts(self, app):
        """Test loading benefit concepts."""
        with app.app_context():
            # Clear existing concepts first
            db.session.execute(db.delete(Prestacion))
            db.session.commit()

            load_benefit_concepts()

            # Check that concepts were loaded
            concepts = db.session.execute(db.select(Prestacion)).scalars().all()
            assert len(concepts) >= len(BENEFIT_CONCEPTS)

            # Check a specific concept - Paid Vacation
            vacation = db.session.execute(
                db.select(Prestacion).filter_by(codigo="PAID_VACATION_PROVISION")
            ).scalar_one_or_none()
            assert vacation is not None
            assert vacation.codigo == "PAID_VACATION_PROVISION"
            assert vacation.activo is True
            assert vacation.tipo == "patronal"

    def test_load_benefit_concepts_no_duplicates(self, app):
        """Test that loading benefit concepts twice doesn't create duplicates."""
        with app.app_context():
            # Load concepts twice
            load_benefit_concepts()
            count_first = db.session.execute(db.select(Prestacion)).scalars().all()

            load_benefit_concepts()
            count_second = db.session.execute(db.select(Prestacion)).scalars().all()
class TestLoadPayrollTypes:
    """Test payroll types loading functionality."""

    def test_load_payroll_types(self, app):
        """Test loading payroll types."""
        with app.app_context():
            # Clear existing types first
            db.session.execute(db.delete(TipoPlanilla))
            db.session.commit()

            load_payroll_types()

            # Check that payroll types were loaded
            types = db.session.execute(db.select(TipoPlanilla)).scalars().all()
            assert len(types) >= len(PAYROLL_TYPES)

            # Check a specific payroll type
            monthly = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="MONTHLY")
            ).scalar_one_or_none()
            assert monthly is not None
            assert monthly.codigo == "MONTHLY"
            assert monthly.dias == 30
            assert monthly.periodos_por_anio == 12
            assert monthly.activo is True

    def test_load_payroll_types_no_duplicates(self, app):
        """Test that loading payroll types twice doesn't create duplicates."""
        with app.app_context():
            # Load types twice
            load_payroll_types()
            count_first = db.session.execute(db.select(TipoPlanilla)).scalars().all()

            load_payroll_types()
            count_second = db.session.execute(db.select(TipoPlanilla)).scalars().all()

            # Should have same count
            assert len(count_first) == len(count_second)

    def test_benefit_concepts_have_correct_properties(self, app):
        """Test that loaded benefit concepts have correct properties."""
        with app.app_context():
            load_benefit_concepts()

            # Get all loaded concepts
            concepts = db.session.execute(db.select(Prestacion)).scalars().all()

            for concept in concepts:
                # Check that they are active and editable
                assert concept.activo is True
                assert concept.editable_en_nomina is True
                # Check formula type is set
                assert concept.formula_tipo is not None
                # Check they are marked as employer contributions
                assert concept.tipo == "patronal"

    def test_three_main_benefit_concepts_loaded(self, app):
        """Test that the three main labor concepts are properly loaded."""
        with app.app_context():
            # Clear existing concepts first
            db.session.execute(db.delete(Prestacion))
            db.session.commit()

            load_benefit_concepts()

            # Check for Paid Vacation provision
            vacation = db.session.execute(
                db.select(Prestacion).filter_by(codigo="PAID_VACATION_PROVISION")
            ).scalar_one_or_none()
            assert vacation is not None

            # Check for 13th Month Salary provision
            thirteenth = db.session.execute(
                db.select(Prestacion).filter_by(codigo="THIRTEENTH_SALARY_PROVISION")
            ).scalar_one_or_none()
            assert thirteenth is not None

            # Check for Severance Pay provision
            severance = db.session.execute(
                db.select(Prestacion).filter_by(codigo="SEVERANCE_PROVISION")
            ).scalar_one_or_none()
            assert severance is not None
    def test_load_payroll_types_have_correct_properties(self, app):
        """Test that loaded payroll types have correct properties."""
        with app.app_context():
            load_payroll_types()

            # Get all loaded types
            types = db.session.execute(db.select(TipoPlanilla)).scalars().all()

            for payroll_type in types:
                # Check that they are active
                assert payroll_type.activo is True
                # Check required fields are set
                assert payroll_type.codigo is not None
                assert payroll_type.dias > 0
                assert payroll_type.periodos_por_anio > 0
                # Check fiscal period defaults
                assert payroll_type.mes_inicio_fiscal == 1
                assert payroll_type.dia_inicio_fiscal == 1
                assert payroll_type.acumula_anual is True

    def test_payroll_types_all_four_loaded(self, app):
        """Test that all four common payroll types are loaded."""
        with app.app_context():
            # Clear existing types first
            db.session.execute(db.delete(TipoPlanilla))
            db.session.commit()

            load_payroll_types()

            # Check specific types
            monthly = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="MONTHLY")
            ).scalar_one_or_none()
            assert monthly is not None

            biweekly = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="BIWEEKLY")
            ).scalar_one_or_none()
            assert biweekly is not None

            fortnightly = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="FORTNIGHTLY")
            ).scalar_one_or_none()
            assert fortnightly is not None

            weekly = db.session.execute(
                db.select(TipoPlanilla).filter_by(codigo="WEEKLY")
            ).scalar_one_or_none()
            assert weekly is not None


class TestLoadInitialData:
    """Test the main load_initial_data function."""

    def test_load_initial_data(self, app):
        """Test loading all initial data."""
        with app.app_context():
            # Clear existing data
            db.session.execute(db.delete(Percepcion))
            db.session.execute(db.delete(Deduccion))
            db.session.execute(db.delete(Prestacion))
            db.session.execute(db.delete(Moneda))
            db.session.execute(db.delete(TipoPlanilla))
            db.session.commit()

            load_initial_data()

            # Check currencies
            currencies = db.session.execute(db.select(Moneda)).scalars().all()
            assert len(currencies) >= len(CURRENCIES)

            # Check income concepts
            income = db.session.execute(db.select(Percepcion)).scalars().all()
            assert len(income) >= len(INCOME_CONCEPTS)

            # Check deduction concepts
            deductions = db.session.execute(db.select(Deduccion)).scalars().all()
            assert len(deductions) >= len(DEDUCTION_CONCEPTS)

            # Check benefit concepts
            benefits = db.session.execute(db.select(Prestacion)).scalars().all()
            assert len(benefits) >= len(BENEFIT_CONCEPTS)
            # Check payroll types
            payroll_types = db.session.execute(db.select(TipoPlanilla)).scalars().all()
            assert len(payroll_types) >= len(PAYROLL_TYPES)

    def test_load_initial_data_idempotent(self, app):
        """Test that loading initial data multiple times is idempotent."""
        with app.app_context():
            # Load data twice
            load_initial_data()
            currencies_1 = len(db.session.execute(db.select(Moneda)).scalars().all())
            income_1 = len(db.session.execute(db.select(Percepcion)).scalars().all())
            deductions_1 = len(db.session.execute(db.select(Deduccion)).scalars().all())
            benefits_1 = len(db.session.execute(db.select(Prestacion)).scalars().all())
            payroll_types_1 = len(db.session.execute(db.select(TipoPlanilla)).scalars().all())

            load_initial_data()
            currencies_2 = len(db.session.execute(db.select(Moneda)).scalars().all())
            income_2 = len(db.session.execute(db.select(Percepcion)).scalars().all())
            deductions_2 = len(db.session.execute(db.select(Deduccion)).scalars().all())
            benefits_2 = len(db.session.execute(db.select(Prestacion)).scalars().all())
            payroll_types_2 = len(db.session.execute(db.select(TipoPlanilla)).scalars().all())

            # Counts should be the same
            assert currencies_1 == currencies_2
            assert income_1 == income_2
            assert deductions_1 == deductions_2
            assert benefits_1 == benefits_2
            assert payroll_types_1 == payroll_types_2
