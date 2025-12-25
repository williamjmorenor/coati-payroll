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

This package contains the refactored formula engine with modular architecture:
- AST parsing and evaluation using Visitor pattern
- Step execution using Strategy pattern
- Validation, tables, execution, and results modules
"""

from __future__ import annotations

# Import from formula_engine_examples for backward compatibility
from coati_payroll.formula_engine_examples import EXAMPLE_IR_NICARAGUA_SCHEMA

# Import main engine and functions
from .engine import FormulaEngine, calculate_with_rule, get_available_sources_for_ui

# Import exceptions
from .exceptions import CalculationError, FormulaEngineError, TaxEngineError, ValidationError

# Import utilities for backward compatibility
from .ast.type_converter import safe_divide, to_decimal

# Import submodules
from .ast import (
    ALLOWED_AST_TYPES,
    ASTVisitor,
    COMPARISON_OPERATORS,
    ExpressionEvaluator,
    SAFE_FUNCTIONS,
    SAFE_OPERATORS,
    SafeASTVisitor,
)
from .data_sources import AVAILABLE_DATA_SOURCES
from .novelty_codes import NOVELTY_CODES

__all__ = [
    # Main engine
    "FormulaEngine",
    "calculate_with_rule",
    "get_available_sources_for_ui",
    # Exceptions
    "FormulaEngineError",
    "TaxEngineError",
    "ValidationError",
    "CalculationError",
    # Examples
    "EXAMPLE_IR_NICARAGUA_SCHEMA",
    # Utilities
    "to_decimal",
    "safe_divide",
    # AST modules
    "ASTVisitor",
    "SafeASTVisitor",
    "ExpressionEvaluator",
    "SAFE_OPERATORS",
    "COMPARISON_OPERATORS",
    "SAFE_FUNCTIONS",
    "ALLOWED_AST_TYPES",
    # Data sources
    "AVAILABLE_DATA_SOURCES",
    "NOVELTY_CODES",
]
