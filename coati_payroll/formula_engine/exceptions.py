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
"""Exceptions for formula engine."""

from __future__ import annotations

from coati_payroll.schema_validator import ValidationError as _BaseValidationError


class FormulaEngineError(Exception):
    """Base exception for formula engine errors.

    Python 3.11+ enhancement: Supports exception notes via add_note() method.
    """

    pass


# Alias for backward compatibility
TaxEngineError = FormulaEngineError


class ValidationError(_BaseValidationError, FormulaEngineError):
    """Exception for validation errors in schema or data.

    Inherits from both the base ValidationError (for schema_validator) and
    FormulaEngineError (for backward compatibility with existing error handling).

    Python 3.11+ enhancement: Can use add_note() to append contextual information.
    """

    pass


class CalculationError(FormulaEngineError):
    """Exception for calculation errors during execution.

    Python 3.11+ enhancement: Supports add_note() for additional context.
    """

    pass
