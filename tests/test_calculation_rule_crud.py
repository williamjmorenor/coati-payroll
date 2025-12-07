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
"""Tests for CalculationRule (Regla de Cálculo) CRUD operations."""

import pytest


class TestCalculationRuleCRUD:
    """Test CRUD operations for CalculationRule."""

    def test_calculation_rule_index_loads(self, app, authenticated_client):
        """Test that calculation rule index page loads."""
        response = authenticated_client.get("/calculation-rule/")
        assert response.status_code == 200

    def test_calculation_rule_new_form_loads(self, app, authenticated_client):
        """Test that new calculation rule form loads."""
        response = authenticated_client.get("/calculation-rule/new")
        assert response.status_code == 200

    def test_calculation_rule_list_loads_with_pagination(self, app, authenticated_client):
        """Test that calculation rule list with pagination loads."""
        response = authenticated_client.get("/calculation-rule/?page=1")
        assert response.status_code == 200
