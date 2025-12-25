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
"""Type conversion utilities for formula engine."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from ..exceptions import ValidationError


def to_decimal(value: Any) -> Decimal:
    """Safely convert a value to Decimal.

    Args:
        value: Value to convert (int, float, str, Decimal, bool)

    Returns:
        Decimal representation of the value

    Raises:
        ValidationError: If value cannot be converted to Decimal
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    # Handle boolean values explicitly (True -> 1, False -> 0)
    # Must check before int/str conversion since bool is a subclass of int
    if isinstance(value, bool):
        return Decimal("1") if value else Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(f"Cannot convert '{value}' to Decimal: {e}") from e


def safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Safely divide two decimals, handling division by zero.

    Args:
        numerator: The dividend
        denominator: The divisor

    Returns:
        Result of division or 0 if denominator is 0
    """
    if denominator == 0:
        return Decimal("0")
    return numerator / denominator
