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
"""Tests for locale_config module."""

from coati_payroll.locale_config import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    invalidate_language_cache,
)


def test_supported_languages_constant():
    """Test that SUPPORTED_LANGUAGES is defined and contains expected languages."""
    assert isinstance(SUPPORTED_LANGUAGES, (list, tuple))
    assert len(SUPPORTED_LANGUAGES) > 0
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES


def test_default_language_constant():
    """Test that DEFAULT_LANGUAGE is defined."""
    assert isinstance(DEFAULT_LANGUAGE, str)
    assert len(DEFAULT_LANGUAGE) > 0


def test_supported_languages_includes_spanish():
    """Test that Spanish is supported."""
    assert 'es' in SUPPORTED_LANGUAGES


def test_supported_languages_are_strings():
    """Test that all supported languages are strings."""
    for lang in SUPPORTED_LANGUAGES:
        assert isinstance(lang, str)
        assert len(lang) >= 2  # Language codes are at least 2 characters


def test_invalidate_language_cache():
    """Test that invalidate_language_cache runs without error."""
    # Should not raise any exceptions
    invalidate_language_cache()


def test_default_language_is_supported():
    """Test that default language is in supported languages list."""
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES


def test_supported_languages_lowercase():
    """Test that language codes are lowercase."""
    for lang in SUPPORTED_LANGUAGES:
        assert lang.islower() or not lang.isalpha()
