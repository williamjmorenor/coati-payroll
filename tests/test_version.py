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
"""Tests for version module that defines package version information."""


def test_version_exists():
    """Test that version is defined."""
    from coati_payroll.version import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_format():
    """Test that version follows semantic versioning pattern."""
    from coati_payroll.version import __version__

    # Check that version has at least one dot (e.g., "0.0.1")
    assert "." in __version__
    
    # Check that version parts are numeric
    parts = __version__.split(".")
    assert len(parts) >= 2  # At least major.minor
    
    # First two parts should be numeric
    assert parts[0].isdigit()
    assert parts[1].isdigit()
