# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
# Copyright 2025 - 2026 BMO Soluciones, S.A.
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
"""Tests for enums module to ensure type safety."""


def test_formula_type_enum_values():
    """
    Test FormulaType enum has expected values.

    Setup:
        - None

    Action:
        - Import and check enum values

    Verification:
        - All expected values are present
    """
    from coati_payroll.enums import FormulaType

    assert FormulaType.FIJO == "fijo"
    assert FormulaType.PORCENTAJE == "porcentaje"
    assert FormulaType.PORCENTAJE_SALARIO == "porcentaje_salario"
    assert FormulaType.PORCENTAJE_BRUTO == "porcentaje_bruto"
    assert FormulaType.FORMULA == "formula"
    assert FormulaType.HORAS == "horas"
    assert FormulaType.DIAS == "dias"


def test_tipo_usuario_enum_values():
    """
    Test TipoUsuario enum has expected values.

    Setup:
        - None

    Action:
        - Import and check enum values

    Verification:
        - All expected values are present
    """
    from coati_payroll.enums import TipoUsuario

    assert TipoUsuario.ADMIN == "admin"
    assert TipoUsuario.HHRR == "hhrr"
    assert TipoUsuario.AUDIT == "audit"


def test_nomina_estado_enum_values():
    """
    Test NominaEstado enum has expected values.

    Setup:
        - None

    Action:
        - Import and check enum values

    Verification:
        - All expected values are present
    """
    from coati_payroll.enums import NominaEstado

    assert NominaEstado.CALCULANDO == "calculando"
    assert NominaEstado.GENERADO == "generado"
    assert NominaEstado.APROBADO == "aprobado"
    assert NominaEstado.APLICADO == "aplicado"
    assert NominaEstado.ERROR == "error"


def test_metodo_amortizacion_enum_values():
    """
    Test MetodoAmortizacion enum has expected values.

    Setup:
        - None

    Action:
        - Import and check enum values

    Verification:
        - All expected values are present
    """
    from coati_payroll.enums import MetodoAmortizacion

    assert MetodoAmortizacion.FRANCES == "frances"
    assert MetodoAmortizacion.ALEMAN == "aleman"


def test_tipo_interes_enum_values():
    """
    Test TipoInteres enum has expected values.

    Setup:
        - None

    Action:
        - Import and check enum values

    Verification:
        - All expected values are present
    """
    from coati_payroll.enums import TipoInteres

    assert TipoInteres.SIMPLE == "simple"
    assert TipoInteres.COMPUESTO == "compuesto"


def test_enums_are_strings():
    """
    Test that enum values are strings.

    Setup:
        - None

    Action:
        - Import enums and check type

    Verification:
        - All enum values are strings
    """
    from coati_payroll.enums import FormulaType, TipoUsuario

    assert isinstance(FormulaType.FIJO, str)
    assert isinstance(TipoUsuario.ADMIN, str)


def test_enum_comparison():
    """
    Test that enum values can be compared with strings.

    Setup:
        - None

    Action:
        - Compare enum with string

    Verification:
        - Comparison works correctly
    """
    from coati_payroll.enums import TipoUsuario

    user_type = "admin"
    assert user_type == TipoUsuario.ADMIN


def test_enum_in_list():
    """
    Test that enum values can be used in lists.

    Setup:
        - None

    Action:
        - Check membership in list

    Verification:
        - Membership check works
    """
    from coati_payroll.enums import TipoUsuario

    allowed_types = [TipoUsuario.ADMIN, TipoUsuario.HHRR]
    assert TipoUsuario.ADMIN in allowed_types
    assert TipoUsuario.AUDIT not in allowed_types


def test_step_type_enum():
    """
    Test StepType enum used in formula engine.

    Setup:
        - None

    Action:
        - Import and check enum values

    Verification:
        - Expected values are present
    """
    from coati_payroll.enums import StepType

    assert StepType.CALCULATION == "calculation"
    # StepType should have more values, test at least one exists
    assert isinstance(StepType.CALCULATION, str)
