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
"""Tests for app module."""


def test_app_blueprint_exists():
    """Test that app blueprint can be imported."""
    from coati_payroll.app import app

    assert app is not None
    assert hasattr(app, "name")


def test_index_route_exists():
    """Test that index route exists in the app blueprint."""
    from coati_payroll.app import index

    assert index is not None
    assert callable(index)
