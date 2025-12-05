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
"""Tests for background queue system."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from coati_payroll.queue import get_queue_driver
from coati_payroll.queue.driver import QueueDriver
from coati_payroll.queue.drivers import DramatiqDriver, HueyDriver
from coati_payroll.queue.selector import reset_cached_driver


class TestQueueDriverSelection:
    """Test automatic queue driver selection."""

    def setup_method(self):
        """Reset cached driver before each test."""
        reset_cached_driver()

    def teardown_method(self):
        """Reset cached driver after each test."""
        reset_cached_driver()

    def test_huey_driver_selected_without_redis(self):
        """Test that Huey driver is selected when Redis is not available."""
        with patch.dict(os.environ, {}, clear=True):
            driver = get_queue_driver()
            assert isinstance(driver, HueyDriver)
            assert driver.is_available()

    @patch("coati_payroll.queue.selector._ping_redis")
    @patch("redis.from_url")
    def test_dramatiq_driver_selected_with_redis(self, mock_redis, mock_ping):
        """Test that Dramatiq driver is selected when Redis is available."""
        mock_ping.return_value = True
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0"}):
            driver = get_queue_driver()
            assert isinstance(driver, DramatiqDriver)

    def test_force_huey_backend(self):
        """Test forcing Huey backend even with Redis available."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0"}):
            driver = get_queue_driver(force_backend="huey")
            assert isinstance(driver, HueyDriver)

    def test_cached_driver_returned(self):
        """Test that subsequent calls return cached driver."""
        driver1 = get_queue_driver()
        driver2 = get_queue_driver()
        assert driver1 is driver2


class TestHueyDriver:
    """Test Huey driver functionality."""

    def test_huey_driver_initialization(self):
        """Test Huey driver initializes successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            driver = HueyDriver(storage_path=tmpdir)
            assert driver.is_available()

    def test_huey_task_registration(self):
        """Test registering a task with Huey driver."""
        with tempfile.TemporaryDirectory() as tmpdir:
            driver = HueyDriver(storage_path=tmpdir)

            def sample_task(x: int, y: int) -> int:
                return x + y

            registered = driver.register_task(sample_task, name="add_numbers")
            assert registered is not None
            assert "add_numbers" in driver._tasks

    def test_huey_get_stats(self):
        """Test getting stats from Huey driver."""
        with tempfile.TemporaryDirectory() as tmpdir:
            driver = HueyDriver(storage_path=tmpdir)
            if driver.is_available():
                stats = driver.get_stats()

                assert stats["driver"] == "huey"
                assert stats["backend"] == "filesystem"
                assert stats["available"] is True
                assert "storage_path" in stats

    def test_huey_enqueue_without_registered_task_fails(self):
        """Test that enqueueing unregistered task raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            driver = HueyDriver(storage_path=tmpdir)

            if driver.is_available():
                with pytest.raises(ValueError, match="not registered"):
                    driver.enqueue("nonexistent_task", 1, 2)
            else:
                with pytest.raises(RuntimeError, match="not available"):
                    driver.enqueue("nonexistent_task", 1, 2)

    def test_huey_filesystem_permissions(self):
        """Test that Huey validates filesystem permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            driver = HueyDriver(storage_path=tmpdir)
            # Should initialize successfully with writable temp directory
            assert driver.is_available()

            # Verify permission test file was cleaned up
            test_file = Path(tmpdir) / ".huey_permissions_test"
            assert not test_file.exists()

    def test_huey_bulk_results(self):
        """Test Huey bulk results for progress feedback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            driver = HueyDriver(storage_path=tmpdir)

            if driver.is_available():
                results = driver.get_bulk_results([])
                assert results["total"] == 0
                assert results["completed"] == 0
                assert "progress_percentage" in results


class TestDramatiqDriver:
    """Test Dramatiq driver functionality (with mocking)."""

    @patch("redis.from_url")
    def test_dramatiq_driver_with_redis_unavailable(self, mock_redis):
        """Test Dramatiq driver when Redis is unavailable."""
        mock_redis.side_effect = ConnectionError("Redis not available")

        driver = DramatiqDriver(redis_url="redis://localhost:6379/0")
        assert not driver.is_available()

    @patch("redis.from_url")
    def test_dramatiq_driver_with_redis_available(self, mock_redis):
        """Test Dramatiq driver when Redis is available."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        driver = DramatiqDriver(redis_url="redis://localhost:6379/0")
        assert driver.is_available()

    @patch("redis.from_url")
    def test_dramatiq_get_stats(self, mock_redis):
        """Test getting stats from Dramatiq driver."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.keys.return_value = [b"dramatiq:default:msgs"]
        mock_client.llen.return_value = 5

        driver = DramatiqDriver(redis_url="redis://localhost:6379/0")
        if driver.is_available():
            stats = driver.get_stats()
            assert stats["driver"] == "dramatiq"
            assert stats["backend"] == "redis"

    @patch("redis.from_url")
    def test_dramatiq_bulk_results_without_backend(self, mock_redis):
        """Test bulk results without Results backend."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        driver = DramatiqDriver(redis_url="redis://localhost:6379/0")
        if driver.is_available():
            results = driver.get_bulk_results([1, 2, 3])
            assert results["total"] == 3
            assert "message" in results


class TestQueueIntegration:
    """Integration tests for queue system."""

    def setup_method(self):
        """Reset cached driver before each test."""
        reset_cached_driver()

    def teardown_method(self):
        """Reset cached driver after each test."""
        reset_cached_driver()

    def test_queue_driver_implements_interface(self):
        """Test that returned driver implements QueueDriver interface."""
        driver = get_queue_driver()
        assert isinstance(driver, QueueDriver)
        assert hasattr(driver, "enqueue")
        assert hasattr(driver, "register_task")
        assert hasattr(driver, "is_available")
        assert hasattr(driver, "get_stats")

    def test_task_registration_and_stats(self):
        """Test task registration shows in stats."""
        driver = get_queue_driver()

        def test_task(value: int) -> int:
            return value * 2

        driver.register_task(test_task, name="multiply_by_two")

        stats = driver.get_stats()
        assert "registered_tasks" in stats
        assert "multiply_by_two" in stats["registered_tasks"]

    def test_bulk_results_feedback(self):
        """Test bulk results for progress feedback (x of y completed)."""
        driver = get_queue_driver()

        # Test with empty list
        results = driver.get_bulk_results([])
        assert results["total"] == 0

        # Huey driver should provide feedback
        if isinstance(driver, HueyDriver):
            assert "progress_percentage" in results
