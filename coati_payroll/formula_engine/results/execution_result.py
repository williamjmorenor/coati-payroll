# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Execution result DTO."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #


class ExecutionResult:
    """Result of formula execution."""

    def __init__(
        self,
        variables: dict[str, Decimal],
        step_results: dict[str, Any],
        final_output: Decimal,
    ):
        self.variables = variables
        self.step_results = step_results
        self.final_output = final_output

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format with 2 decimal places rounding."""

        def _round_to_two(value: Decimal) -> float:
            """Round Decimal to 2 decimal places."""
            rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return float(rounded)

        # Procesar variables
        processed_vars = {}
        for key, value in self.variables.items():
            if isinstance(value, Decimal):
                processed_vars[key] = _round_to_two(value)
            else:
                processed_vars[key] = value

        # Procesar step_results
        processed_results = {}
        for key, value in self.step_results.items():
            if isinstance(value, Decimal):
                processed_results[key] = _round_to_two(value)
            elif isinstance(value, dict):
                processed_dict = {}
                for k, v in value.items():
                    if isinstance(v, Decimal):
                        processed_dict[k] = _round_to_two(v)
                    else:
                        processed_dict[k] = v
                processed_results[key] = processed_dict
            else:
                processed_results[key] = value

        return {
            "variables": processed_vars,
            "results": processed_results,
            "output": _round_to_two(self.final_output),
        }
