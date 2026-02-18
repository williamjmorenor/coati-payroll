# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Implementation helpers for initial system setup."""

from __future__ import annotations

from flask import Blueprint, render_template

from coati_payroll.enums import TipoUsuario
from coati_payroll.rbac import require_role

implementation_bp = Blueprint("implementation", __name__, url_prefix="/settings/helpers")


@implementation_bp.route("/")
@require_role(TipoUsuario.ADMIN)
def index():
    """Display the initial implementation helpers menu."""
    return render_template("modules/settings/implementation/index.html")
