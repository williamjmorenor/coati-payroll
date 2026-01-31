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
"""Table lookup implementation."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from decimal import Decimal
from typing import Any, Callable

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.i18n import _
from ..ast.type_converter import to_decimal
from ..exceptions import CalculationError
from .bracket_calculator import BracketCalculator


class TableLookup:
    """Handles lookups in tax tables."""

    def __init__(self, tax_tables: dict[str, Any], trace_callback: Callable[[str], None] | None = None):
        """Initialize table lookup.

        Args:
            tax_tables: Dictionary of tax table names to table definitions
            trace_callback: Optional callback for trace logging
        """
        self.tax_tables = tax_tables
        self.trace_callback = trace_callback or (lambda _: None)

    def lookup(self, table_name: str, input_value: Decimal) -> dict[str, Decimal]:
        """Look up tax bracket in a tax table.

        Args:
            table_name: Name of the tax table
            input_value: Value to look up

        Returns:
            Dictionary with 'tax', 'rate', 'fixed', 'over' values

        Raises:
            CalculationError: If table not found or lookup fails
        """
        if table_name not in self.tax_tables:
            raise CalculationError(f"Tax table '{table_name}' not found")

        table = self.tax_tables[table_name]
        if not isinstance(table, list):
            raise CalculationError(f"Tax table '{table_name}' must be a list")

        if not table:
            # Defensive: empty table
            self.trace_callback(
                _("Advertencia: tabla de impuestos '%(table)s' está vacía, devolviendo ceros") % {"table": table_name}
            )
            return {
                "tax": Decimal("0"),
                "rate": Decimal("0"),
                "fixed": Decimal("0"),
                "over": Decimal("0"),
            }

        self.trace_callback(
            _("Buscando tabla de impuestos '%(table)s' con valor %(value)s; brackets=%(count)s")
            % {"table": table_name, "value": input_value, "count": len(table)}
        )

        # Defensive: Sort brackets by min value if not already sorted
        try:
            sorted_table = sorted(table, key=lambda b: to_decimal(b.get("min", 0)))
            if sorted_table != table:
                self.trace_callback(
                    _("Advertencia: tabla '%(table)s' no estaba ordenada, ordenando automáticamente")
                    % {"table": table_name}
                )
                table = sorted_table
        except Exception as e:
            self.trace_callback(
                _("Advertencia: no se pudo ordenar la tabla '%(table)s': %(error)s")
                % {"table": table_name, "error": str(e)}
            )

        # Find the applicable bracket
        matched_brackets = []
        for i, bracket in enumerate(table):
            try:
                min_val = to_decimal(bracket.get("min", 0))
                max_val = bracket.get("max")

                if max_val is None:
                    # Open-ended bracket (highest tier)
                    if input_value >= min_val:
                        matched_brackets.append((i, bracket, min_val, None))
                else:
                    max_val = to_decimal(max_val)
                    # Defensive: validate bracket range
                    if max_val < min_val:
                        msg = _("Advertencia: tramo %(index)s de tabla '%(table)s' tiene max < min, omitiendo")
                        self.trace_callback(msg % {"index": i, "table": table_name})
                        continue

                    if min_val <= input_value <= max_val:
                        matched_brackets.append((i, bracket, min_val, max_val))
            except Exception as e:
                # Defensive: skip invalid brackets
                self.trace_callback(
                    _("Advertencia: error procesando tramo %(index)s de tabla '%(table)s': %(error)s")
                    % {"index": i, "table": table_name, "error": str(e)}
                )
                continue

        # Handle multiple matches (overlaps) - use the first valid match
        if matched_brackets:
            if len(matched_brackets) > 1:
                # Multiple brackets match - this indicates an overlap
                self.trace_callback(
                    _(
                        "ADVERTENCIA CRÍTICA: múltiples tramos coinciden para valor %(value)s en tabla '%(table)s'. "
                        "Esto indica solapamiento. Usando el primer tramo encontrado."
                    )
                    % {"value": input_value, "table": table_name}
                )

            i, bracket, min_val, max_val = matched_brackets[0]
            result = BracketCalculator.calculate(bracket, input_value)
            if max_val is None:
                self.trace_callback(
                    _("Aplicando tramo abierto desde %(min)s para valor %(value)s -> %(result)s")
                    % {"min": min_val, "value": input_value, "result": result}
                )
            else:
                self.trace_callback(
                    _("Aplicando tramo %(min)s - %(max)s para valor %(value)s -> %(result)s")
                    % {"min": min_val, "max": max_val, "value": input_value, "result": result}
                )
            return result

        # If no bracket found, return zeros
        self.trace_callback(
            _(
                "No se encontró tramo para valor %(value)s en tabla '%(table)s', devolviendo ceros. "
                "Esto puede indicar un gap en la configuración de la tabla."
            )
            % {"value": input_value, "table": table_name}
        )
        return {
            "tax": Decimal("0"),
            "rate": Decimal("0"),
            "fixed": Decimal("0"),
            "over": Decimal("0"),
        }
