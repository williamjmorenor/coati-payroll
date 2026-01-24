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
"""Bracket tax calculation."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from ..ast.type_converter import to_decimal


class BracketCalculator:
    """Calculates tax for a specific bracket."""

    @staticmethod
    def calculate(bracket: dict[str, Any], input_value: Decimal) -> dict[str, Decimal]:
        """Calculate tax for a specific bracket.

        Args:
            bracket: Tax bracket definition
            input_value: Value being taxed

        Returns:
            Dictionary with calculated tax components
        """
        rate = to_decimal(bracket.get("rate", 0))
        fixed = to_decimal(bracket.get("fixed", 0))
        over = to_decimal(bracket.get("over", 0))

        # Calculate tax: fixed + (input_value - over) * rate
        excess = max(input_value - over, Decimal("0"))
        tax = fixed + (excess * rate)

        return {
            "tax": tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "rate": rate,
            "fixed": fixed,
            "over": over,
        }
