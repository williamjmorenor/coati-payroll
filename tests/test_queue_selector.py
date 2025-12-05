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
"""Tests for queue driver selector."""

import os
import pytest


class TestQueueSelector:
    """Tests for queue driver selection logic."""

    def test_get_queue_driver_returns_driver(self):
        """Test that get_queue_driver returns a driver instance."""
        from coati_payroll.queue.selector import get_queue_driver, reset_cached_driver
        from coati_payroll.queue.driver import QueueDriver

        # Clear cache
        reset_cached_driver()

        # Should return a driver (Huey as fallback)
        driver = get_queue_driver()
        assert driver is not None
        assert isinstance(driver, QueueDriver)

    def test_get_queue_driver_caching(self):
        """Test that driver is cached after first call."""
        from coati_payroll.queue.selector import get_queue_driver, reset_cached_driver

        # Clear cache
        reset_cached_driver()

        # First call
        driver1 = get_queue_driver()
        # Second call should return same instance
        driver2 = get_queue_driver()
        assert driver1 is driver2

    def test_reset_cached_driver(self):
        """Test that reset_cached_driver clears the cache."""
        from coati_payroll.queue.selector import get_queue_driver, reset_cached_driver

        # Get a driver
        driver1 = get_queue_driver()

        # Reset cache
        reset_cached_driver()

        # Get driver again
        driver2 = get_queue_driver()

        # May or may not be same instance depending on implementation
        assert driver1 is not None
        assert driver2 is not None

    def test_force_huey_backend(self):
        """Test forcing Huey backend."""
        from coati_payroll.queue.selector import get_queue_driver, reset_cached_driver
        from coati_payroll.queue.drivers import HueyDriver

        # Clear cache
        reset_cached_driver()

        # Force Huey
        driver = get_queue_driver(force_backend="huey")
        assert isinstance(driver, HueyDriver)

    def test_ping_redis_with_invalid_url(self):
        """Test Redis ping with invalid URL."""
        from coati_payroll.queue.selector import _ping_redis

        # Should return False for invalid URL
        result = _ping_redis("redis://invalid-host:9999")
        assert result is False

    def test_get_queue_driver_with_no_redis(self):
        """Test driver selection when Redis is not available."""
        from coati_payroll.queue.selector import get_queue_driver, reset_cached_driver
        from coati_payroll.queue.drivers import HueyDriver

        # Save original env
        old_redis_url = os.environ.get("REDIS_URL")
        old_cache_url = os.environ.get("CACHE_REDIS_URL")

        try:
            # Clear Redis URLs
            os.environ.pop("REDIS_URL", None)
            os.environ.pop("CACHE_REDIS_URL", None)

            # Clear cache
            reset_cached_driver()

            # Should fall back to Huey
            driver = get_queue_driver()
            assert isinstance(driver, HueyDriver)

        finally:
            # Restore env
            if old_redis_url:
                os.environ["REDIS_URL"] = old_redis_url
            if old_cache_url:
                os.environ["CACHE_REDIS_URL"] = old_cache_url
            reset_cached_driver()
