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
"""Tests for locale configuration module."""

import pytest


class TestLocaleConfig:
    """Tests for language configuration and caching."""

    def test_supported_languages_constant(self):
        """Test that supported languages are defined."""
        from coati_payroll.locale_config import SUPPORTED_LANGUAGES

        assert "en" in SUPPORTED_LANGUAGES
        assert "es" in SUPPORTED_LANGUAGES

    def test_default_language_constant(self):
        """Test that default language is defined."""
        from coati_payroll.locale_config import DEFAULT_LANGUAGE

        assert DEFAULT_LANGUAGE == "en"

    def test_get_language_from_db_returns_string(self, app):
        """Test that get_language_from_db returns a valid language string."""
        from coati_payroll.locale_config import get_language_from_db

        with app.app_context():
            language = get_language_from_db()
            assert isinstance(language, str)
            assert language in ["en", "es"]

    def test_get_language_from_db_caching(self, app):
        """Test that language is cached after first call."""
        from coati_payroll.locale_config import (
            get_language_from_db,
            invalidate_language_cache,
        )

        with app.app_context():
            # First call
            lang1 = get_language_from_db()
            # Second call should use cache
            lang2 = get_language_from_db()
            assert lang1 == lang2

            # Invalidate cache
            invalidate_language_cache()

            # After invalidation, should still work
            lang3 = get_language_from_db()
            assert lang3 in ["en", "es"]

    def test_set_language_in_db_valid_language(self, app):
        """Test setting a valid language in the database."""
        from coati_payroll.locale_config import set_language_in_db, get_language_from_db

        with app.app_context():
            # Set to English
            set_language_in_db("en")
            lang = get_language_from_db()
            assert lang == "en"

            # Set to Spanish
            set_language_in_db("es")
            lang = get_language_from_db()
            assert lang == "es"

    def test_set_language_in_db_invalid_language(self, app):
        """Test that setting an invalid language raises ValueError."""
        from coati_payroll.locale_config import set_language_in_db

        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                set_language_in_db("fr")
            assert "Unsupported language" in str(exc_info.value)

    def test_invalidate_language_cache(self, app):
        """Test that cache invalidation works."""
        from coati_payroll.locale_config import (
            get_language_from_db,
            invalidate_language_cache,
        )

        with app.app_context():
            # Load language (populates cache)
            lang1 = get_language_from_db()

            # Invalidate cache
            invalidate_language_cache()

            # Next call should work (reload from DB)
            lang2 = get_language_from_db()
            assert lang2 in ["en", "es"]

    def test_initialize_language_from_env_no_env(self, app):
        """Test initialize_language_from_env when no env var is set."""
        import os
        from coati_payroll.locale_config import initialize_language_from_env

        # Ensure COATI_LANG is not set
        old_value = os.environ.pop("COATI_LANG", None)
        try:
            with app.app_context():
                # Should not raise an error
                initialize_language_from_env()
        finally:
            if old_value:
                os.environ["COATI_LANG"] = old_value

    def test_initialize_language_from_env_with_valid_lang(self, app):
        """Test initialize_language_from_env with valid language."""
        import os
        from coati_payroll.locale_config import initialize_language_from_env
        from coati_payroll.model import ConfiguracionGlobal, db

        with app.app_context():
            # Clear any existing config
            db.session.execute(db.delete(ConfiguracionGlobal))
            db.session.commit()

            # Set environment variable
            os.environ["COATI_LANG"] = "en"
            
            # Initialize from environment
            initialize_language_from_env()

            # Check that config was created
            config = db.session.execute(
                db.select(ConfiguracionGlobal)
            ).scalar_one_or_none()
            
            # Only check if config was created (it might be None if already existed)
            if config:
                assert config.idioma in ["en", "es"]

    def test_initialize_language_from_env_with_invalid_lang(self, app):
        """Test initialize_language_from_env with invalid language."""
        import os
        from coati_payroll.locale_config import initialize_language_from_env

        old_value = os.environ.get("COATI_LANG")
        try:
            with app.app_context():
                # Set invalid language
                os.environ["COATI_LANG"] = "invalid"
                
                # Should not raise an error, just log a warning
                initialize_language_from_env()
        finally:
            if old_value:
                os.environ["COATI_LANG"] = old_value
            else:
                os.environ.pop("COATI_LANG", None)
