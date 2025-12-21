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
"""Formula engine package.

This package contains the formula engine module and supporting submodules:
- Main engine: Imported from parent module formula_engine.py
- data_sources: Available data sources for formula calculations
- novelty_codes: Mapping of novelty codes to their calculation behavior
"""

# Import constants from submodules
from coati_payroll.formula_engine.data_sources import AVAILABLE_DATA_SOURCES
from coati_payroll.formula_engine.novelty_codes import NOVELTY_CODES

# Import everything from the parent formula_engine.py module
# We need to use importlib to avoid circular imports
import importlib.util
import sys
from pathlib import Path

# Get the path to the parent formula_engine.py file
_parent_dir = Path(__file__).parent.parent
_formula_engine_py = _parent_dir / "formula_engine.py"

# Load the parent module dynamically
# Use a unique module name to avoid conflicts
_module_name = "coati_payroll._formula_engine_impl"
if _formula_engine_py.exists() and _module_name not in sys.modules:
    spec = importlib.util.spec_from_file_location(_module_name, _formula_engine_py)
    if spec and spec.loader:
        _formula_engine_module = importlib.util.module_from_spec(spec)
        sys.modules[_module_name] = _formula_engine_module
        spec.loader.exec_module(_formula_engine_module)

        # Re-export everything from the parent module
        FormulaEngine = _formula_engine_module.FormulaEngine
        FormulaEngineError = _formula_engine_module.FormulaEngineError
        TaxEngineError = _formula_engine_module.TaxEngineError
        ValidationError = _formula_engine_module.ValidationError
        CalculationError = _formula_engine_module.CalculationError
        EXAMPLE_IR_NICARAGUA_SCHEMA = _formula_engine_module.EXAMPLE_IR_NICARAGUA_SCHEMA
        calculate_with_rule_schema = getattr(_formula_engine_module, "calculate_with_rule_schema", None) or getattr(
            _formula_engine_module, "calculate_with_rule", None
        )
        get_available_sources_for_ui = _formula_engine_module.get_available_sources_for_ui
        to_decimal = getattr(_formula_engine_module, "to_decimal", None)
        safe_divide = getattr(_formula_engine_module, "safe_divide", None)
elif _module_name in sys.modules:
    # Module already loaded, just re-export
    _formula_engine_module = sys.modules[_module_name]
    FormulaEngine = _formula_engine_module.FormulaEngine
    FormulaEngineError = _formula_engine_module.FormulaEngineError
    TaxEngineError = _formula_engine_module.TaxEngineError
    ValidationError = _formula_engine_module.ValidationError
    CalculationError = _formula_engine_module.CalculationError
    EXAMPLE_IR_NICARAGUA_SCHEMA = _formula_engine_module.EXAMPLE_IR_NICARAGUA_SCHEMA
    calculate_with_rule_schema = getattr(_formula_engine_module, "calculate_with_rule_schema", None) or getattr(
        _formula_engine_module, "calculate_with_rule", None
    )
    get_available_sources_for_ui = _formula_engine_module.get_available_sources_for_ui
    to_decimal = getattr(_formula_engine_module, "to_decimal", None)
    safe_divide = getattr(_formula_engine_module, "safe_divide", None)

__all__ = [
    "FormulaEngine",
    "FormulaEngineError",
    "TaxEngineError",
    "ValidationError",
    "CalculationError",
    "EXAMPLE_IR_NICARAGUA_SCHEMA",
    "calculate_with_rule_schema",
    "get_available_sources_for_ui",
    "AVAILABLE_DATA_SOURCES",
    "NOVELTY_CODES",
]

# Add optional exports if they exist and were loaded
# Check if to_decimal and safe_divide were successfully loaded
if globals().get("to_decimal") is not None:
    __all__.append("to_decimal")
if globals().get("safe_divide") is not None:
    __all__.append("safe_divide")
