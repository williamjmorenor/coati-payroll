# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Language configuration and caching for internationalization."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from os import environ
from threading import Lock

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #
from flask import current_app

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.log import log

# Supported languages
SUPPORTED_LANGUAGES = ["en", "es"]
DEFAULT_LANGUAGE = "en"

# Cache for language setting with thread-safe access
_language_cache = None
_cache_lock = Lock()


def get_language_from_db() -> str:
    """Get the configured language from the database.

    Returns the language code ('en' or 'es') from the global configuration table.
    If no configuration exists, returns the default language.
    Uses caching to avoid repeated database queries.

    Returns:
        str: Language code ('en' or 'es')
    """
    global _language_cache

    # Check cache first (thread-safe)
    with _cache_lock:
        if _language_cache is not None:
            return _language_cache

    # Cache miss - query database
    try:
        from coati_payroll.model import ConfiguracionGlobal, db

        with current_app.app_context():
            config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one_or_none()

            if config and config.idioma in SUPPORTED_LANGUAGES:
                language = config.idioma
            else:
                language = DEFAULT_LANGUAGE

            # Update cache (thread-safe)
            with _cache_lock:
                _language_cache = language

            log.trace("Language loaded from database: %s", language)
            return language

    except Exception as e:
        log.warning("Error reading language from database: %s", e)
        return DEFAULT_LANGUAGE


def set_language_in_db(language: str) -> None:
    """Set the configured language in the database.

    Updates the language setting in the global configuration table and
    invalidates the cache to ensure the change is immediately reflected.

    Args:
        language: Language code ('en' or 'es')

    Raises:
        ValueError: If language is not supported
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}. Must be one of {SUPPORTED_LANGUAGES}")

    from coati_payroll.model import ConfiguracionGlobal, db

    with current_app.app_context():
        config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one_or_none()

        if config:
            config.idioma = language
        else:
            # Create new configuration record
            config = ConfiguracionGlobal()
            config.idioma = language
            db.session.add(config)

        db.session.commit()

        # Invalidate cache to force reload on next access
        invalidate_language_cache()

        log.info("Language updated to: %s", language)


def invalidate_language_cache() -> None:
    """Invalidate the language cache.

    Forces the next call to get_language_from_db() to query the database.
    Call this after updating the language setting.
    """
    global _language_cache

    with _cache_lock:
        _language_cache = None

    log.trace("Language cache invalidated")


def initialize_language_from_env() -> None:
    """Initialize language from COATI_LANG environment variable.

    Called during application startup to set the initial language from
    the environment variable if provided. Only updates the database if
    no configuration exists yet.
    """
    env_lang = environ.get("COATI_LANG", "").strip().lower()

    if not env_lang:
        return

    if env_lang not in SUPPORTED_LANGUAGES:
        log.warning("Invalid COATI_LANG value: %s. Must be one of %s. Using default.", env_lang, SUPPORTED_LANGUAGES)
        return

    try:
        from coati_payroll.model import ConfiguracionGlobal, db

        with current_app.app_context():
            config = db.session.execute(db.select(ConfiguracionGlobal)).scalar_one_or_none()

            # Only set from environment if no config exists yet
            if not config:
                config = ConfiguracionGlobal()
                config.idioma = env_lang
                db.session.add(config)
                db.session.commit()
                log.info("Language initialized from COATI_LANG: %s", env_lang)

    except Exception as e:
        log.warning("Error initializing language from environment: %s", e)
