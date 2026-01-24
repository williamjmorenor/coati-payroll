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
"""Execution result DTO."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


class ExecutionResult:
    """Result of formula execution."""

    def __init__(
        self,
        variables: dict[str, Decimal],
        step_results: dict[str, Any],
        final_output: Decimal,
    ):
        """Initialize execution result.

        Args:
            variables: All variables after execution
            step_results: Results from each step
            final_output: Final output value
        """
        self.variables = variables
        self.step_results = step_results
        self.final_output = final_output

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format.

        Returns:
            Dictionary representation of result
        """
        return {
            "variables": {k: float(v) for k, v in self.variables.items()},
            "results": {
                k: (
                    float(v)
                    if isinstance(v, Decimal)
                    else ({kk: float(vv) for kk, vv in v.items()} if isinstance(v, dict) else v)
                )
                for k, v in self.step_results.items()
            },
            "output": float(self.final_output),
        }
