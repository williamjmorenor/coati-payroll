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
"""Tax table data structure."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from typing import Any

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #


class TaxTable:
    """Represents a tax table with brackets."""

    def __init__(self, name: str, brackets: list[dict[str, Any]]):
        """Initialize tax table.

        Args:
            name: Table name
            brackets: List of bracket dictionaries
        """
        self.name = name
        self.brackets = brackets
