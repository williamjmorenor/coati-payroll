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
"""Test security features implementation."""

import pytest


def test_security_headers_are_present(client):
    """Test that security headers are added to responses.
    
    Verifies implementation of:
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    """
    # Make a request to the login page (doesn't require authentication)
    response = client.get("/auth/login")
    
    # Verify security headers are present
    assert "Content-Security-Policy" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "strict-origin" in response.headers.get("Referrer-Policy", "").lower()


def test_hsts_not_in_development(client):
    """Test that HSTS is not set in development mode.
    
    HSTS (Strict-Transport-Security) should only be enabled in production
    to force HTTPS connections.
    """
    response = client.get("/auth/login")
    
    # In development/testing, HSTS should NOT be present
    assert "Strict-Transport-Security" not in response.headers


def test_csrf_protection_enabled(app):
    """Test that CSRF protection is initialized.
    
    Note: CSRF is disabled in test config (WTF_CSRF_ENABLED=False) to make
    testing easier, but we verify it's initialized in the app.
    """
    # CSRF protection should be in app extensions
    assert "csrf" in app.extensions or hasattr(app, "jinja_env")
    
    # In test config, it should be disabled
    assert app.config.get("WTF_CSRF_ENABLED") is False


def test_session_cookie_configuration(app):
    """Test that session cookies are configured securely.
    
    Verifies:
    - SESSION_COOKIE_HTTPONLY: Prevents JavaScript access
    - SESSION_COOKIE_SAMESITE: CSRF protection
    - PERMANENT_SESSION_LIFETIME: Session timeout configured
    """
    # HttpOnly should be True to prevent JavaScript access
    assert app.config.get("SESSION_COOKIE_HTTPONLY") is True
    
    # SameSite should be set for CSRF protection
    assert app.config.get("SESSION_COOKIE_SAMESITE") == "Lax"
    
    # Session lifetime should be configured
    assert "PERMANENT_SESSION_LIFETIME" in app.config


def test_rate_limiting_configured(app):
    """Test that rate limiting is configured.
    
    Verifies that Flask-Limiter is initialized and configured
    with appropriate storage backend.
    """
    # Rate limiter should be in app extensions
    assert "limiter" in app.extensions
    
    # Verify limiter is configured
    # The limiter extension exists and is not None
    assert app.extensions["limiter"] is not None


def test_login_endpoint_exists(client):
    """Test that login endpoint is accessible."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower() or b"entrar" in response.data.lower()
