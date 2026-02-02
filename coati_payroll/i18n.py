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
"""Internationalization module."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask_babel import gettext, lazy_gettext, ngettext

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #


# ---------------------------------------------------------------------------------------
# Translation functions
# ---------------------------------------------------------------------------------------
def _(text: str, **kwargs) -> str:
    """Mark text for translation.

    Supports keyword arguments for string formatting.
    Example: _("Hello %(name)s", name="World")
    """
    translated = gettext(text)
    if kwargs:
        return translated % kwargs
    return translated


def _n(singular: str, plural: str, n: int) -> str:
    """Mark text for plural translation."""
    return ngettext(singular, plural, n)


def _l(text: str) -> str:
    """Mark text for lazy translation (useful in forms)."""
    return lazy_gettext(text)
