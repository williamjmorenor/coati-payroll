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
"""Unit tests for the formula calculation engine."""

from decimal import Decimal

import pytest

from coati_payroll.formula_engine import (
    FormulaEngine,
    ValidationError,
    CalculationError,
    to_decimal,
    safe_divide,
    calculate_with_rule,
    get_available_sources_for_ui,
    SAFE_OPERATORS,
    COMPARISON_OPERATORS,
)


class TestToDecimal:
    """Tests for the to_decimal helper function."""

    def test_convert_integer(self):
        """Test converting integer to Decimal."""
        result = to_decimal(100)
        assert result == Decimal("100")

    def test_convert_float(self):
        """Test converting float to Decimal."""
        result = to_decimal(10.5)
        assert result == Decimal("10.5")

    def test_convert_string(self):
        """Test converting string to Decimal."""
        result = to_decimal("123.45")
        assert result == Decimal("123.45")

    def test_convert_decimal(self):
        """Test passing Decimal returns same value."""
        original = Decimal("50.00")
        result = to_decimal(original)
        assert result == original

    def test_convert_none(self):
        """Test converting None returns zero."""
        result = to_decimal(None)
        assert result == Decimal("0")

    def test_invalid_value_raises_error(self):
        """Test invalid value raises ValidationError."""
        with pytest.raises(ValidationError):
            to_decimal("not_a_number")


class TestSafeDivide:
    """Tests for the safe_divide function."""

    def test_normal_division(self):
        """Test normal division works correctly."""
        result = safe_divide(Decimal("10"), Decimal("2"))
        assert result == Decimal("5")

    def test_division_by_zero(self):
        """Test division by zero returns zero."""
        result = safe_divide(Decimal("10"), Decimal("0"))
        assert result == Decimal("0")

    def test_zero_numerator(self):
        """Test zero numerator returns zero."""
        result = safe_divide(Decimal("0"), Decimal("5"))
        assert result == Decimal("0")


class TestFormulaEngineValidation:
    """Tests for FormulaEngine schema validation."""

    def test_valid_schema(self, simple_formula_schema):
        """Test valid schema creates engine successfully."""
        engine = FormulaEngine(simple_formula_schema)
        assert engine.schema == simple_formula_schema

    def test_invalid_schema_not_dict(self):
        """Test non-dict schema raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            FormulaEngine("not a dict")

    def test_missing_steps_raises_error(self):
        """Test missing 'steps' raises ValidationError."""
        with pytest.raises(ValidationError, match="must contain 'steps'"):
            FormulaEngine({"inputs": []})

    def test_step_missing_name_raises_error(self):
        """Test step without name raises ValidationError."""
        schema = {"steps": [{"type": "calculation"}]}
        with pytest.raises(ValidationError, match="must have a 'name'"):
            FormulaEngine(schema)

    def test_step_missing_type_raises_error(self):
        """Test step without type raises ValidationError."""
        schema = {"steps": [{"name": "test_step"}]}
        with pytest.raises(ValidationError, match="must have a 'type'"):
            FormulaEngine(schema)


class TestFormulaEngineCalculations:
    """Tests for FormulaEngine calculation execution."""

    def test_simple_calculation(self, simple_formula_schema):
        """Test simple multiplication calculation."""
        engine = FormulaEngine(simple_formula_schema)
        result = engine.execute({"base": 200, "rate": 0.15})
        assert result["output"] == 30.0

    def test_calculation_with_defaults(self, simple_formula_schema):
        """Test calculation uses default values when inputs not provided."""
        engine = FormulaEngine(simple_formula_schema)
        result = engine.execute({})
        assert result["output"] == 10.0  # 100 * 0.1

    def test_addition_calculation(self):
        """Test addition in formula."""
        schema = {
            "inputs": [
                {"name": "a", "default": 5},
                {"name": "b", "default": 3},
            ],
            "steps": [{"name": "sum", "type": "calculation", "formula": "a + b"}],
            "output": "sum",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 8.0

    def test_subtraction_calculation(self):
        """Test subtraction in formula."""
        schema = {
            "inputs": [
                {"name": "a", "default": 10},
                {"name": "b", "default": 3},
            ],
            "steps": [{"name": "diff", "type": "calculation", "formula": "a - b"}],
            "output": "diff",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 7.0

    def test_division_calculation(self):
        """Test division in formula."""
        schema = {
            "inputs": [
                {"name": "a", "default": 20},
                {"name": "b", "default": 4},
            ],
            "steps": [{"name": "quot", "type": "calculation", "formula": "a / b"}],
            "output": "quot",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 5.0

    def test_division_by_zero_returns_zero(self):
        """Test division by zero is handled safely."""
        schema = {
            "inputs": [
                {"name": "a", "default": 10},
                {"name": "b", "default": 0},
            ],
            "steps": [{"name": "quot", "type": "calculation", "formula": "a / b"}],
            "output": "quot",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 0.0


class TestFormulaEngineConditionals:
    """Tests for conditional step execution."""

    def test_conditional_true_branch(self):
        """Test conditional executes if_true when condition is true."""
        schema = {
            "inputs": [{"name": "value", "default": 100}],
            "steps": [
                {
                    "name": "result",
                    "type": "conditional",
                    "condition": {"left": "value", "operator": ">", "right": 50},
                    "if_true": "200",
                    "if_false": "0",
                }
            ],
            "output": "result",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 200.0

    def test_conditional_false_branch(self):
        """Test conditional executes if_false when condition is false."""
        schema = {
            "inputs": [{"name": "value", "default": 30}],
            "steps": [
                {
                    "name": "result",
                    "type": "conditional",
                    "condition": {"left": "value", "operator": ">", "right": 50},
                    "if_true": "200",
                    "if_false": "0",
                }
            ],
            "output": "result",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 0.0


class TestFormulaEngineTaxLookup:
    """Tests for tax table lookup functionality."""

    def test_tax_lookup_zero_bracket(self, sample_tax_schema):
        """Test tax lookup in zero-rate bracket."""
        engine = FormulaEngine(sample_tax_schema)
        result = engine.execute({"salario_mensual": 800, "inss_laboral": 0})
        tax_result = result["results"]["impuesto"]
        assert tax_result["rate"] == 0
        assert tax_result["tax"] == 0

    def test_tax_lookup_middle_bracket(self, sample_tax_schema):
        """Test tax lookup in middle bracket."""
        engine = FormulaEngine(sample_tax_schema)
        result = engine.execute({"salario_mensual": 3000, "inss_laboral": 0})
        tax_result = result["results"]["impuesto"]
        assert tax_result["rate"] == 0.10
        # (3000 - 1000) * 0.10 = 200
        assert float(tax_result["tax"]) == 200.0

    def test_tax_lookup_highest_bracket(self, sample_tax_schema):
        """Test tax lookup in highest (open-ended) bracket."""
        engine = FormulaEngine(sample_tax_schema)
        result = engine.execute({"salario_mensual": 10000, "inss_laboral": 0})
        tax_result = result["results"]["impuesto"]
        assert tax_result["rate"] == 0.20
        # fixed 400 + (10000 - 5000) * 0.20 = 400 + 1000 = 1400
        assert float(tax_result["tax"]) == 1400.0

    def test_tax_lookup_missing_table_raises_error(self):
        """Test missing tax table raises CalculationError."""
        schema = {
            "inputs": [{"name": "income", "default": 1000}],
            "steps": [
                {
                    "name": "tax",
                    "type": "tax_lookup",
                    "table": "nonexistent_table",
                    "input": "income",
                }
            ],
            "output": "tax",
        }
        engine = FormulaEngine(schema)
        with pytest.raises(CalculationError, match="Tax table.*not found"):
            engine.execute({})


class TestFormulaEngineAssignment:
    """Tests for assignment step type."""

    def test_assignment_with_value(self):
        """Test assignment step assigns value correctly."""
        schema = {
            "inputs": [{"name": "source", "default": 500}],
            "steps": [
                {
                    "name": "target",
                    "type": "assignment",
                    "value": "source",
                }
            ],
            "output": "target",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 500.0

    def test_assignment_with_literal(self):
        """Test assignment with literal value."""
        schema = {
            "inputs": [],
            "steps": [
                {
                    "name": "constant",
                    "type": "assignment",
                    "value": 42,
                }
            ],
            "output": "constant",
        }
        engine = FormulaEngine(schema)
        result = engine.execute({})
        assert result["output"] == 42.0


class TestCalculateWithRule:
    """Tests for the calculate_with_rule convenience function."""

    def test_calculate_with_employee_data(self, simple_formula_schema):
        """Test calculation with employee data."""
        result = calculate_with_rule(
            simple_formula_schema, employee_data={"base": 500, "rate": 0.2}
        )
        assert result["output"] == 100.0

    def test_calculate_with_accumulated_data(self):
        """Test calculation includes accumulated data with prefix."""
        schema = {
            "inputs": [
                {"name": "salario", "default": 0},
                {"name": "acumulado_salario", "default": 0},
            ],
            "steps": [
                {
                    "name": "total",
                    "type": "calculation",
                    "formula": "salario + acumulado_salario",
                }
            ],
            "output": "total",
        }
        result = calculate_with_rule(
            schema,
            employee_data={"salario": 1000},
            accumulated_data={"salario": 5000},
        )
        assert result["output"] == 6000.0


class TestGetAvailableSourcesForUI:
    """Tests for UI helper function."""

    def test_returns_list(self):
        """Test function returns a list."""
        sources = get_available_sources_for_ui()
        assert isinstance(sources, list)

    def test_sources_have_required_fields(self):
        """Test each source has required fields."""
        sources = get_available_sources_for_ui()
        required_fields = {"value", "label", "type", "description", "category"}
        for source in sources:
            assert required_fields.issubset(source.keys())

    def test_empleado_salario_base_exists(self):
        """Test empleado.salario_base is in available sources."""
        sources = get_available_sources_for_ui()
        values = [s["value"] for s in sources]
        assert "empleado.salario_base" in values


class TestOperators:
    """Tests for operator dictionaries."""

    def test_safe_operators_available(self):
        """Test all basic operators are defined."""
        assert "+" in SAFE_OPERATORS
        assert "-" in SAFE_OPERATORS
        assert "*" in SAFE_OPERATORS
        assert "/" in SAFE_OPERATORS
        assert "**" in SAFE_OPERATORS

    def test_comparison_operators_available(self):
        """Test all comparison operators are defined."""
        assert ">" in COMPARISON_OPERATORS
        assert ">=" in COMPARISON_OPERATORS
        assert "<" in COMPARISON_OPERATORS
        assert "<=" in COMPARISON_OPERATORS
        assert "==" in COMPARISON_OPERATORS
        assert "!=" in COMPARISON_OPERATORS
