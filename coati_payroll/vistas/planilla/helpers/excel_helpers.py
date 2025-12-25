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
"""Excel helper functions for planilla views."""


def check_openpyxl_available():
    """Check if openpyxl is available and return necessary classes.

    Returns:
        tuple: (Workbook, Font, Alignment, PatternFill, Border, Side) or None if not available
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

        return Workbook, Font, Alignment, PatternFill, Border, Side
    except ImportError:
        return None
