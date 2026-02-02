# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Base validator interface and exceptions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.payroll_context import PayrollContext
from ..results.validation_result import ValidationResult


class NominaEngineError(Exception):
    """Base exception for payroll engine errors."""

    pass


class ValidationError(NominaEngineError):
    """Exception for validation errors."""

    pass


class CalculationError(NominaEngineError):
    """Exception for calculation errors."""

    pass


class BaseValidator(ABC):
    """Base validator interface."""

    @abstractmethod
    def validate(self, context: PayrollContext) -> ValidationResult:
        """Validate the given context."""
        pass
