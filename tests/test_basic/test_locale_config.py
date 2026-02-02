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
"""Tests for locale configuration module."""

import pytest


def test_supported_languages_constant():
    """
    Test that SUPPORTED_LANGUAGES constant is defined.

    Setup:
        - None

    Action:
        - Import constant

    Verification:
        - Constant exists and contains expected languages
    """
    from coati_payroll.locale_config import SUPPORTED_LANGUAGES

    assert "en" in SUPPORTED_LANGUAGES
    assert "es" in SUPPORTED_LANGUAGES
    assert isinstance(SUPPORTED_LANGUAGES, list)


def test_default_language_constant():
    """
    Test that DEFAULT_LANGUAGE constant is defined.

    Setup:
        - None

    Action:
        - Import constant

    Verification:
        - Constant exists and is valid
    """
    from coati_payroll.locale_config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES


def test_get_language_from_db_returns_default(app, db_session):
    """
    Test get_language_from_db returns default when no config exists.

    Setup:
        - Clean database

    Action:
        - Get language from database

    Verification:
        - Returns default language
    """
    from coati_payroll.locale_config import (
        DEFAULT_LANGUAGE,
        get_language_from_db,
        invalidate_language_cache,
    )

    with app.app_context():
        # Invalidate cache first
        invalidate_language_cache()

        language = get_language_from_db()
        assert language == DEFAULT_LANGUAGE


def test_set_language_in_db_english(app, db_session):
    """
    Test setting language to English.

    Setup:
        - App and database

    Action:
        - Set language to English

    Verification:
        - Language is set successfully
    """
    from coati_payroll.locale_config import get_language_from_db, invalidate_language_cache, set_language_in_db

    with app.app_context():
        # Invalidate cache first
        invalidate_language_cache()

        set_language_in_db("en")
        language = get_language_from_db()
        assert language == "en"


def test_set_language_in_db_spanish(app, db_session):
    """
    Test setting language to Spanish.

    Setup:
        - App and database

    Action:
        - Set language to Spanish

    Verification:
        - Language is set successfully
    """
    from coati_payroll.locale_config import get_language_from_db, invalidate_language_cache, set_language_in_db

    with app.app_context():
        # Invalidate cache first
        invalidate_language_cache()

        set_language_in_db("es")
        language = get_language_from_db()
        assert language == "es"


def test_set_language_invalid_raises_error(app, db_session):
    """
    Test setting invalid language raises ValueError.

    Setup:
        - App and database

    Action:
        - Try to set invalid language

    Verification:
        - ValueError is raised
    """
    from coati_payroll.locale_config import set_language_in_db

    with app.app_context():
        with pytest.raises(ValueError):
            set_language_in_db("fr")


def test_invalidate_language_cache(app, db_session):
    """
    Test invalidating language cache.

    Setup:
        - Set language and let it cache

    Action:
        - Invalidate cache

    Verification:
        - Cache is cleared
    """
    from coati_payroll.locale_config import (
        get_language_from_db,
        invalidate_language_cache,
        set_language_in_db,
    )

    with app.app_context():
        # Set and cache language
        set_language_in_db("es")
        _ = get_language_from_db()

        # Invalidate cache
        invalidate_language_cache()

        # Should re-read from database
        language = get_language_from_db()
        assert language == "es"


def test_language_cache_works(app, db_session):
    """
    Test that language caching works correctly.

    Setup:
        - Set language in database

    Action:
        - Call get_language_from_db multiple times

    Verification:
        - Same result returned (from cache)
    """
    from coati_payroll.locale_config import get_language_from_db, invalidate_language_cache, set_language_in_db

    with app.app_context():
        invalidate_language_cache()
        set_language_in_db("en")

        # First call populates cache
        lang1 = get_language_from_db()

        # Second call should use cache
        lang2 = get_language_from_db()

        assert lang1 == lang2 == "en"


def test_set_language_updates_existing_config(app, db_session):
    """
    Test that setting language updates existing configuration.

    Setup:
        - Set initial language

    Action:
        - Change language

    Verification:
        - Language is updated
    """
    from coati_payroll.locale_config import get_language_from_db, invalidate_language_cache, set_language_in_db

    with app.app_context():
        invalidate_language_cache()

        # Set initial language
        set_language_in_db("en")
        assert get_language_from_db() == "en"

        # Update language
        set_language_in_db("es")
        assert get_language_from_db() == "es"


def test_get_language_handles_invalid_db_value(app, db_session):
    """
    Test that invalid language in DB falls back to default.

    Setup:
        - Manually set invalid language in DB

    Action:
        - Get language from DB

    Verification:
        - Returns default language
    """
    from coati_payroll.locale_config import (
        DEFAULT_LANGUAGE,
        get_language_from_db,
        invalidate_language_cache,
    )
    from coati_payroll.model import ConfiguracionGlobal, db

    with app.app_context():
        invalidate_language_cache()

        # Manually set invalid language directly in DB to simulate database corruption
        # This bypasses set_language_in_db() validation to test the fallback behavior
        # when corrupted/invalid data exists in the database (e.g., from manual edits
        # or data migration issues). This ensures robust error handling.
        config = ConfiguracionGlobal()
        config.idioma = "invalid"
        db.session.add(config)
        db.session.commit()

        invalidate_language_cache()

        language = get_language_from_db()
        assert language == DEFAULT_LANGUAGE


def test_language_functions_are_thread_safe(app, db_session):
    """
    Test that language functions use locking.

    Setup:
        - None

    Action:
        - Call cache operations

    Verification:
        - No errors occur (basic sanity check)
    """
    from coati_payroll.locale_config import get_language_from_db, invalidate_language_cache

    with app.app_context():
        # Multiple invalidations should be safe
        for _ in range(5):
            invalidate_language_cache()

        # Multiple gets should be safe
        for _ in range(5):
            _ = get_language_from_db()


def test_supported_languages_are_valid_codes():
    """
    Test that supported languages use valid ISO codes.

    Setup:
        - None

    Action:
        - Check language codes

    Verification:
        - All codes are 2-letter lowercase
    """
    from coati_payroll.locale_config import SUPPORTED_LANGUAGES

    for lang in SUPPORTED_LANGUAGES:
        assert len(lang) == 2
        assert lang.islower()
        assert lang.isalpha()
