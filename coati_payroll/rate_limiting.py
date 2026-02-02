# SPDX-License-Identifier: Apache-2.0
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
"""Rate limiting configuration for the application.

This module configures rate limiting to protect against brute force attacks
and abuse, particularly for authentication endpoints.
"""

from __future__ import annotations

from os import environ
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def get_rate_limiter_storage():
    """Get storage backend for rate limiter based on available configuration.

    Returns:
        str: Storage URI for rate limiter
        - Uses Redis if REDIS_URL or SESSION_REDIS_URL is available (production)
        - Falls back to memory storage for development/testing
    """
    # Try to get Redis URL from environment
    redis_url = environ.get("REDIS_URL") or environ.get("SESSION_REDIS_URL")

    if redis_url:
        # Use Redis for distributed rate limiting (production)
        return redis_url
    else:
        # Use memory storage for development/testing
        # Note: This won't work across multiple processes
        return "memory://"


def configure_rate_limiting(app):
    """Configure rate limiting for the Flask application.

    Sets up Flask-Limiter with appropriate storage backend:
    - Redis for production (distributed, persistent)
    - Memory for development (simple, non-persistent)

    Args:
        app: Flask application instance

    Returns:
        Limiter: Configured Flask-Limiter instance
    """
    from coati_payroll.log import log

    storage_uri = get_rate_limiter_storage()

    # Log which storage backend we're using
    if storage_uri.startswith("redis"):
        log.info("Rate limiting configured with Redis storage (production mode)")
    else:
        log.info("Rate limiting configured with memory storage (development mode)")

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["200 per day", "50 per hour"],  # Global limits
        storage_options={"socket_connect_timeout": 30},
        strategy="fixed-window",  # Count resets at fixed intervals
    )

    # Note: Specific endpoint rate limits can be applied using decorators in the blueprints.
    # For the login endpoint, we apply a stricter limit (5 per minute) to prevent brute force.
    # This is documented in the security audit report.

    return limiter
