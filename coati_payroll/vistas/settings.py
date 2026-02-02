# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
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
"""Settings page to consolidate administrative options."""

from __future__ import annotations

from flask import Blueprint, render_template

from coati_payroll.rbac import require_write_access

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@require_write_access()
def index():
    """Display settings page with links to all configuration options."""
    return render_template("modules/settings/index.html")
