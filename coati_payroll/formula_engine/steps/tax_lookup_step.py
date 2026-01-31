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
"""Tax lookup step implementation."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from decimal import Decimal
from typing import TYPE_CHECKING

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from ..tables.table_lookup import TableLookup
from .base_step import Step

if TYPE_CHECKING:
    from ..execution.execution_context import ExecutionContext


class TaxLookupStep(Step):
    """Step for looking up values in tax tables."""

    def execute(self, context: "ExecutionContext") -> dict[str, Decimal]:
        """Execute tax lookup step.

        Args:
            context: Execution context

        Returns:
            Dictionary with tax calculation results
        """
        table_name = self.config.get("table", "")
        input_var = self.config.get("input", "")
        input_value = context.variables.get(input_var, Decimal("0"))

        table_lookup = TableLookup(context.tax_tables, context.trace_callback)
        return table_lookup.lookup(table_name, input_value)
