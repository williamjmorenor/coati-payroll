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
"""Security validation for AST nodes."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
import ast

# <-------------------------------------------------------------------------> #
# Third party packages
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from ..ast.safe_operators import ALLOWED_AST_TYPES, SAFE_FUNCTIONS
from ..exceptions import CalculationError


class SecurityValidator:
    """Validates AST security for expression evaluation."""

    @staticmethod
    def validate_ast_security(node: ast.AST) -> None:
        """Validate that an AST node only contains safe operations.

        Args:
            node: AST node to validate

        Raises:
            CalculationError: If unsafe operations are detected
        """
        # Validate all nodes in the tree in a single pass
        for child in ast.walk(node):
            if not isinstance(child, ALLOWED_AST_TYPES):
                raise CalculationError(
                    f"Unsafe operation detected: {child.__class__.__name__}. "
                    "Only basic arithmetic and safe functions are allowed."
                )
            # Validate function calls
            if isinstance(child, ast.Call):
                if not isinstance(child.func, ast.Name):
                    raise CalculationError("Only named functions are allowed")
                if child.func.id not in SAFE_FUNCTIONS:
                    raise CalculationError(
                        f"Function '{child.func.id}' is not allowed. "
                        f"Allowed functions: {', '.join(SAFE_FUNCTIONS.keys())}"
                    )
