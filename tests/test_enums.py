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
"""Tests for enums module."""


def test_formula_type_enum_exists():
    """Test that FormulaType enum exists and has expected values."""
    from coati_payroll.enums import FormulaType

    # Check enum exists
    assert FormulaType is not None

    # Check common values exist
    assert hasattr(FormulaType, "FIJO")
    assert hasattr(FormulaType, "PORCENTAJE")
    assert hasattr(FormulaType, "FORMULA")


def test_step_type_enum_exists():
    """Test that StepType enum exists and has expected values."""
    from coati_payroll.enums import StepType

    # Check enum exists
    assert StepType is not None

    # Check common values exist
    assert hasattr(StepType, "CALCULATION")
    assert hasattr(StepType, "CONDITIONAL")


def test_nomina_estado_enum_exists():
    """Test that NominaEstado enum exists and has expected values."""
    from coati_payroll.enums import NominaEstado

    # Check enum exists
    assert NominaEstado is not None

    # Check common values exist
    assert hasattr(NominaEstado, "CALCULANDO")
    assert hasattr(NominaEstado, "GENERADO")


def test_tipo_usuario_enum_exists():
    """Test that TipoUsuario enum exists and has expected values."""
    from coati_payroll.enums import TipoUsuario

    # Check enum exists
    assert TipoUsuario is not None

    # Check common values exist
    assert hasattr(TipoUsuario, "ADMIN")
    assert hasattr(TipoUsuario, "HHRR")


def test_enum_values_are_strings():
    """Test that enum values are strings."""
    from coati_payroll.enums import FormulaType, StepType, NominaEstado

    # FormulaType values should be strings
    assert isinstance(FormulaType.FIJO.value, str)
    assert isinstance(FormulaType.PORCENTAJE.value, str)

    # StepType values should be strings
    assert isinstance(StepType.CALCULATION.value, str)
    assert isinstance(StepType.CONDITIONAL.value, str)

    # NominaEstado values should be strings
    assert isinstance(NominaEstado.CALCULANDO.value, str)
    assert isinstance(NominaEstado.GENERADO.value, str)


def test_can_compare_enum_values():
    """Test that we can compare enum values."""
    from coati_payroll.enums import FormulaType

    fijo = FormulaType.FIJO
    also_fijo = FormulaType.FIJO
    porcentaje = FormulaType.PORCENTAJE

    # Same enum values should be equal
    assert fijo == also_fijo
    assert fijo is also_fijo

    # Different enum values should not be equal
    assert fijo != porcentaje


def test_can_iterate_enum():
    """Test that we can iterate over enum values."""
    from coati_payroll.enums import FormulaType

    # Should be able to iterate
    values = list(FormulaType)
    assert len(values) > 0
    assert all(isinstance(v, FormulaType) for v in values)


def test_enum_has_value_method():
    """Test that enum instances have value method."""
    from coati_payroll.enums import FormulaType

    fijo = FormulaType.FIJO
    assert hasattr(fijo, "value")
    assert fijo.value is not None
