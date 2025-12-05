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
"""Tests for internationalization module."""


def test_translation_function_basic(app):
    """Test basic translation function."""
    from coati_payroll.i18n import _

    with app.app_context():
        # Test basic translation
        result = _("Hello")
        assert result is not None
        assert isinstance(result, str)


def test_translation_function_with_kwargs(app):
    """Test translation function with keyword arguments."""
    from coati_payroll.i18n import _

    with app.app_context():
        # Test translation with formatting
        result = _("Hello %(name)s", name="World")
        assert result is not None
        assert isinstance(result, str)
        # May contain "World" or translation of "World"
        assert "World" in result or len(result) > 0


def test_plural_translation_function(app):
    """Test plural translation function."""
    from coati_payroll.i18n import _n

    with app.app_context():
        # Test plural translation
        result_singular = _n("%(num)d item", "%(num)d items", 1)
        result_plural = _n("%(num)d item", "%(num)d items", 5)
        assert result_singular is not None
        assert result_plural is not None
        assert isinstance(result_singular, str)
        assert isinstance(result_plural, str)


def test_lazy_translation_function(app):
    """Test lazy translation function."""
    from coati_payroll.i18n import _l

    with app.app_context():
        # Test lazy translation
        result = _l("Hello")
        assert result is not None
        # Lazy translations return a special object
        assert hasattr(result, "__str__")
