# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Tests for plugin-prefixed novelty code normalization and formula input source mapping.

This test module validates the fixes from the upstream patch that enable proper
handling of plugin-provided novelty codes (e.g., bmonic_HORAS_EXTRAv_lct2019)
and formula input source metadata.
"""

import pytest
from decimal import Decimal
from datetime import date

from coati_payroll.nomina_engine.services.employee_processing_service import (
    EmployeeProcessingService,
)
from coati_payroll.nomina_engine.calculators.concept_calculator import ConceptCalculator
from coati_payroll.nomina_engine.domain.employee_calculation import EmpleadoCalculo


class TestNovedadCodeNormalization:
    """Tests for novelty code normalization."""

    def test_normalize_novedad_code_with_bmonic_prefix(self):
        """Test normalization of bmonic-prefixed novelty codes."""
        # Test Nicaragua plugin format
        assert (
            EmployeeProcessingService._normalize_novedad_code("bmonic_HORAS_EXTRAv_lct2019")
            == "HORAS_EXTRA"
        )
        assert (
            EmployeeProcessingService._normalize_novedad_code("bmonic_DESCUENTOv_lct2019")
            == "DESCUENTO"
        )
        assert (
            EmployeeProcessingService._normalize_novedad_code("bmonic_BONIFICACIONv_lct2019")
            == "BONIFICACION"
        )

    def test_normalize_novedad_code_without_prefix(self):
        """Test that codes without prefix return None."""
        assert EmployeeProcessingService._normalize_novedad_code("HORAS_EXTRA") is None
        assert EmployeeProcessingService._normalize_novedad_code("DESCUENTO") is None
        assert EmployeeProcessingService._normalize_novedad_code("BONIFICACION") is None

    def test_normalize_novedad_code_with_different_prefix(self):
        """Test that codes with different prefix return None."""
        assert EmployeeProcessingService._normalize_novedad_code("other_HORAS_EXTRAv_lct2019") is None
        assert EmployeeProcessingService._normalize_novedad_code("bmonic_HORAS_EXTRA") is None

    def test_normalize_novedad_code_empty_base(self):
        """Test that codes with empty base return None."""
        assert EmployeeProcessingService._normalize_novedad_code("bmonic_v_lct2019") is None
