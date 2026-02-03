# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Internationalization module."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from typing import Any

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


def _l(text: str) -> str | Any:
    """Mark text for lazy translation (useful in forms)."""
    return lazy_gettext(text)
