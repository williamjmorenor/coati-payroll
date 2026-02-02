# SPDX-License-Identifier: Apache-2.0
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
"""Base step interface for Strategy pattern."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #

if TYPE_CHECKING:
    from ..execution.execution_context import ExecutionContext


class Step(ABC):
    """Base interface for all step types."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize step.

        Args:
            name: Step name
            config: Step configuration dictionary
        """
        self.name = name
        self.config = config

    @abstractmethod
    def execute(self, context: "ExecutionContext") -> Any:
        """Execute the step and return result.

        Args:
            context: Execution context with variables and tax tables

        Returns:
            Step execution result
        """
        pass
