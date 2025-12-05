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
"""Automatic queue driver selection based on environment."""

from __future__ import annotations

import os

from coati_payroll.log import log
from coati_payroll.queue.driver import QueueDriver
from coati_payroll.queue.drivers import DramatiqDriver, HueyDriver


_cached_driver: QueueDriver | None = None


def _ping_redis(redis_url: str) -> bool:
    """Test if Redis is available.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        True if Redis responds to ping, False otherwise
    """
    try:
        import redis
        # Use connection pool for efficiency if multiple pings needed
        # Socket timeout ensures we don't hang waiting for Redis
        client = redis.from_url(
            redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=False,
        )
        client.ping()
        # Close connection to avoid leaking resources
        client.close()
        return True
    except Exception:
        return False


def get_queue_driver(force_backend: str | None = None) -> QueueDriver:
    """Get the appropriate queue driver based on environment.
    
    Selection logic:
    1. If force_backend is specified, use that backend
    2. If REDIS_URL exists and Redis responds -> use Dramatiq
    3. Otherwise -> use Huey with filesystem backend
    
    Args:
        force_backend: Optional backend to force ('dramatiq' or 'huey')
        
    Returns:
        QueueDriver instance (Dramatiq or Huey)
        
    Raises:
        RuntimeError: If no driver is available
    """
    global _cached_driver
    
    # Return cached driver if available
    if _cached_driver is not None and force_backend is None:
        return _cached_driver
    
    # Get Redis URL from environment
    redis_url = os.environ.get("REDIS_URL") or os.environ.get("CACHE_REDIS_URL")
    
    # Try Dramatiq first if Redis is available (unless forcing Huey)
    if force_backend != "huey" and redis_url and _ping_redis(redis_url):
        driver = DramatiqDriver(redis_url=redis_url)
        if driver.is_available():
            log.info("Using Dramatiq driver with Redis backend")
            _cached_driver = driver
            return driver
        else:
            log.warning("Redis available but Dramatiq failed to initialize")
    
    # Fallback to Huey with filesystem (unless forcing Dramatiq)
    if force_backend != "dramatiq":
        storage_path = os.environ.get("COATI_QUEUE_PATH")
        driver = HueyDriver(storage_path=storage_path)
        if driver.is_available():
            log.info("Using Huey driver with filesystem backend")
            _cached_driver = driver
            return driver
        else:
            log.error("Huey driver failed to initialize")
    
    # No driver available
    raise RuntimeError(
        "No queue driver available. Please install 'dramatiq' and 'huey': "
        "pip install dramatiq[redis] huey"
    )


def reset_cached_driver() -> None:
    """Reset the cached driver instance.
    
    This is mainly useful for testing to force driver reinitialization.
    """
    global _cached_driver
    _cached_driver = None
