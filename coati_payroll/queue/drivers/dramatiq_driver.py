# SPDX-License-Identifier: Apache-2.0 \r\n # Copyright 2025 - 2026 BMO Soluciones, S.A.
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
"""Dramatiq driver for high-performance queue processing with Redis."""

from __future__ import annotations

from typing import Any, Callable

from coati_payroll.log import log
from coati_payroll.queue.driver import QueueDriver


class DramatiqDriver(QueueDriver):
    """Queue driver using Dramatiq with Redis backend.

    This driver provides high-performance, distributed job processing
    suitable for production environments with Redis available.

    Features:
    - Multi-threaded workers
    - Automatic retries with exponential backoff
    - Distributed processing across multiple workers
    - Results backend (optional)
    """

    def __init__(self, redis_url: str | None = None):
        """Initialize Dramatiq driver.

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379/0)
        """
        self._redis_url = redis_url or "redis://localhost:6379/0"
        self._broker = None
        self._tasks = {}
        self._available = self._initialize_broker()

    def _initialize_broker(self) -> bool:
        """Initialize the Dramatiq broker.

        Returns:
            True if broker initialized successfully, False otherwise
        """
        try:
            import dramatiq
            from dramatiq.brokers.redis import RedisBroker
            from dramatiq.middleware import (
                AgeLimit,
                Retries,
                TimeLimit,
            )

            # Test Redis connection
            import redis

            client = redis.from_url(self._redis_url, socket_connect_timeout=2)
            client.ping()

            # Configure broker with middleware
            self._broker = RedisBroker(url=self._redis_url)

            # Add middleware for retries, age limits, and time limits
            self._broker.add_middleware(Retries(max_retries=3, min_backoff=15000, max_backoff=86400000))
            self._broker.add_middleware(TimeLimit(time_limit=3600000))  # 1 hour max
            self._broker.add_middleware(AgeLimit(max_age=86400000))  # 24 hours max age

            # Set as default broker
            dramatiq.set_broker(self._broker)

            log.info(f"Dramatiq driver initialized with Redis at {self._redis_url}")
            return True

        except ImportError as e:
            log.warning(f"Dramatiq not available: {e}")
            return False
        except Exception as e:
            log.warning(f"Failed to connect to Redis for Dramatiq: {e}")
            return False

    def enqueue(self, task_name: str, *args: Any, delay: int | None = None, **kwargs: Any) -> Any:
        """Enqueue a task for background processing.

        Args:
            task_name: Name of the registered task
            *args: Positional arguments for the task
            delay: Optional delay in seconds before execution
            **kwargs: Keyword arguments for the task

        Returns:
            Dramatiq message object

        Raises:
            ValueError: If task is not registered
            RuntimeError: If driver is not available
        """
        if not self._available:
            raise RuntimeError("Dramatiq driver is not available")

        if task_name not in self._tasks:
            raise ValueError(f"Task '{task_name}' not registered")

        task = self._tasks[task_name]

        if delay:
            # Convert seconds to milliseconds for Dramatiq
            return task.send_with_options(args=args, kwargs=kwargs, delay=delay * 1000)
        else:
            return task.send(*args, **kwargs)

    def register_task(
        self,
        func: Callable,
        name: str | None = None,
        max_retries: int = 3,
        min_backoff: int = 15000,
        max_backoff: int = 86400000,
    ) -> Callable:
        """Register a function as a Dramatiq actor.

        Args:
            func: Function to register
            name: Optional task name (defaults to function name)
            max_retries: Maximum retry attempts
            min_backoff: Minimum backoff in milliseconds
            max_backoff: Maximum backoff in milliseconds

        Returns:
            Dramatiq actor that can be called or enqueued
        """
        if not self._available:
            log.warning(f"Cannot register task '{name or func.__name__}': Dramatiq not available")
            return func

        try:
            import dramatiq

            task_name = name or func.__name__

            # Decorate with dramatiq.actor
            actor = dramatiq.actor(
                func,
                actor_name=task_name,
                max_retries=max_retries,
                min_backoff=min_backoff,
                max_backoff=max_backoff,
            )

            self._tasks[task_name] = actor
            log.debug(f"Registered Dramatiq task: {task_name}")

            return actor

        except Exception as e:
            log.error(f"Failed to register task '{name or func.__name__}': {e}")
            return func

    def is_available(self) -> bool:
        """Check if Dramatiq driver is available.

        Returns:
            True if driver initialized successfully
        """
        return self._available

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics from Redis.

        Returns:
            Dictionary with queue statistics
        """
        if not self._available or not self._broker:
            return {"error": "Dramatiq driver not available"}

        try:
            import redis

            client = redis.from_url(self._redis_url)

            # Get basic stats from Redis
            stats = {
                "driver": "dramatiq",
                "backend": "redis",
                "available": True,
                "registered_tasks": list(self._tasks.keys()),
            }

            # Try to get queue lengths
            try:
                keys = client.keys("dramatiq:*:msgs")
                stats["queues"] = {}
                for key in keys:
                    queue_name = key.decode("utf-8").split(":")[1]
                    length = client.llen(key)
                    stats["queues"][queue_name] = length
            except Exception as e:
                log.debug(f"Could not fetch queue lengths: {e}")

            return stats

        except Exception as e:
            log.error(f"Failed to get Dramatiq stats: {e}")
            return {"error": str(e)}

    def get_task_result(self, task_id: Any) -> dict[str, Any]:
        """Get the result of a task by its ID.

        Note: Dramatiq doesn't have built-in result storage by default.
        This returns limited information based on message ID.

        Args:
            task_id: Dramatiq message object

        Returns:
            Dictionary with task status (limited in Dramatiq without results backend)
        """
        if not self._available:
            return {"status": "error", "error": "Dramatiq driver not available"}

        try:
            # Dramatiq messages don't have built-in result tracking
            # unless using Results middleware with a backend
            return {
                "status": "pending",
                "message": "Dramatiq task enqueued. Result tracking requires Results middleware.",
                "task_id": str(task_id) if task_id else None,
            }
        except Exception as e:
            log.error(f"Failed to get task result: {e}")
            return {"status": "error", "error": str(e)}

    def get_bulk_results(self, task_ids: list[Any]) -> dict[str, Any]:
        """Get results for multiple tasks (for bulk feedback: x of y completed).

        Note: Without Results middleware, Dramatiq cannot track task completion.
        This returns estimated status based on queue inspection.

        Args:
            task_ids: List of Dramatiq message objects

        Returns:
            Dictionary with aggregated status (limited without Results backend)
        """
        if not self._available:
            return {"error": "Dramatiq driver not available"}

        total = len(task_ids)

        # Without Results middleware, we can only provide limited feedback
        return {
            "total": total,
            "completed": 0,
            "failed": 0,
            "pending": total,  # Assume all pending without result tracking
            "processing": 0,
            "tasks": {},
            "message": "Bulk result tracking requires Results middleware with a backend.",
            "progress_percentage": 0,
        }
