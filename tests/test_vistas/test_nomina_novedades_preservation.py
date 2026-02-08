# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Defensive regression tests for novedades preservation on payroll recalculation."""

import inspect

from coati_payroll.vistas.planilla.services.nomina_service import NominaService


def test_recalcular_nomina_does_not_delete_nomina_novedad_defensive():
    """DEFENSIVE: prevent reintroducing explicit NominaNovedad deletion."""
    source = inspect.getsource(NominaService.recalcular_nomina)

    assert "delete(NominaNovedad)" not in source
    assert "NominaNovedad must be preserved" in source
