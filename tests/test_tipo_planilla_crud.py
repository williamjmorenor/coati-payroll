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
"""Tests for TipoPlanilla (Payroll Type) CRUD operations."""

import pytest


class TestTipoPlanillaCRUD:
    """Test CRUD operations for TipoPlanilla."""

    def test_tipo_planilla_index_loads(self, app, authenticated_client):
        """Test that tipo planilla index page loads."""
        response = authenticated_client.get("/tipo-planilla/")
        assert response.status_code == 200

    def test_tipo_planilla_new_form_loads(self, app, authenticated_client):
        """Test that new tipo planilla form loads."""
        response = authenticated_client.get("/tipo-planilla/new")
        assert response.status_code == 200

    def test_tipo_planilla_list_loads_with_pagination(self, app, authenticated_client):
        """Test that tipo planilla list with pagination loads."""
        response = authenticated_client.get("/tipo-planilla/?page=1")
        assert response.status_code == 200
