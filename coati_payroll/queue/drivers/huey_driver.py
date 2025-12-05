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
"""Huey driver for filesystem-based queue processing (fallback mode)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from coati_payroll.log import log
from coati_payroll.queue.driver import QueueDriver


class HueyDriver(QueueDriver):
    """Queue driver using Huey with filesystem backend.

    This driver provides a fallback queue implementation that works
    without Redis or any database, using only the filesystem for
    persistence. Suitable for small deployments or development.

    Features:
    - No external dependencies (Redis, databases)
    - Persistent queue using filesystem
    - Thread-safe execution
    - Multiple workers support (local only)

    Limitations:
    - Cannot scale horizontally (single-server only)
    - Lower performance than Dramatiq+Redis
    """

    def __init__(self, storage_path: str | None = None):
        """Initialize Huey driver with filesystem backend.

        Args:
            storage_path: Path to store queue files (default: /var/lib/coati/queue)
        """
        self._storage_path = storage_path or self._get_default_storage_path()
        self._huey = None
        self._tasks = {}
        self._available = self._initialize_huey()

    def _get_default_storage_path(self) -> str:
        """Get default storage path for queue files.

        Ensures proper permissions are available for reading and writing queue files.

        Returns:
            Path to queue storage directory
        """
        # Try to use /var/lib/coati/queue if writable, otherwise use user directory
        # Try standard system and user directories first (secure locations)
        paths_to_try = [
            "/var/lib/coati/queue",
            os.path.expanduser("~/.local/share/coati-payroll/queue"),
        ]

        for path in paths_to_try:
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
                # Test read/write permissions
                test_file = Path(path) / ".test_permissions"
                test_file.write_text("test")
                content = test_file.read_text()
                test_file.unlink()

                if content == "test":
                    log.info(f"Queue storage path verified with read/write access: {path}")
                    return path
            except (OSError, PermissionError) as e:
                log.debug(f"Cannot use path {path}: {e}")
                continue

        # Try current working directory as last resort (with warning about security)
        try:
            cwd_path = os.path.join(os.getcwd(), ".coati_queue")
            Path(cwd_path).mkdir(parents=True, exist_ok=True)
            test_file = Path(cwd_path) / ".test_permissions"
            test_file.write_text("test")
            test_file.read_text()
            test_file.unlink()
            log.warning(
                f"Using current working directory for queue storage: {cwd_path}. "
                f"This may be insecure if running in a public directory. "
                f"Consider setting COATI_QUEUE_PATH to a secure location."
            )
            return cwd_path
        except (OSError, PermissionError):
            pass

        # Fallback to temp directory
        import tempfile

        path = os.path.join(tempfile.gettempdir(), "coati_queue")
        Path(path).mkdir(parents=True, exist_ok=True)
        log.warning(
            f"Using temporary directory for queue storage: {path}. " f"Queue data will be lost on system reboot."
        )
        return path

    def _initialize_huey(self) -> bool:
        """Initialize Huey with filesystem backend.

        Validates read/write permissions before initialization to ensure
        the process has necessary access to queue files.

        Returns:
            True if Huey initialized successfully, False otherwise
        """
        try:
            from huey import FileHuey

            # Ensure storage directory exists with proper permissions
            Path(self._storage_path).mkdir(parents=True, exist_ok=True)

            # Validate read/write permissions
            test_file = Path(self._storage_path) / ".huey_permissions_test"
            try:
                test_file.write_text("permission_test")
                if test_file.read_text() != "permission_test":
                    raise PermissionError("Cannot verify read access")
                test_file.unlink()
            except (OSError, PermissionError) as e:
                log.error(
                    f"Insufficient permissions for queue storage at {self._storage_path}: {e}. "
                    f"Please ensure the process has read/write access to this directory."
                )
                return False

            # Initialize FileHuey with filesystem storage
            # Note: FileHuey accepts storage_kwargs which are passed to FileStorage
            self._huey = FileHuey(
                name="coati_payroll",
                path=self._storage_path,  # Path for FileStorage
                immediate=False,  # Don't execute tasks immediately
                results=True,  # Store results for feedback
            )

            log.info(
                f"Huey driver initialized with filesystem storage at {self._storage_path}. "
                f"Read/write permissions verified."
            )
            return True

        except ImportError as e:
            log.warning(f"Huey not available: {e}")
            return False
        except Exception as e:
            log.error(f"Failed to initialize Huey: {e}")
            return False

    def enqueue(self, task_name: str, *args: Any, delay: int | None = None, **kwargs: Any) -> Any:
        """Enqueue a task for background processing.

        Args:
            task_name: Name of the registered task
            *args: Positional arguments for the task
            delay: Optional delay in seconds before execution
            **kwargs: Keyword arguments for the task

        Returns:
            Huey result object

        Raises:
            ValueError: If task is not registered
            RuntimeError: If driver is not available
        """
        if not self._available:
            raise RuntimeError("Huey driver is not available")

        if task_name not in self._tasks:
            raise ValueError(f"Task '{task_name}' not registered")

        task = self._tasks[task_name]

        if delay:
            return task.schedule(args=args, kwargs=kwargs, delay=delay)
        else:
            return task(*args, **kwargs)

    def register_task(
        self,
        func: Callable,
        name: str | None = None,
        max_retries: int = 3,
        min_backoff: int = 15000,
        max_backoff: int = 86400000,
    ) -> Callable:
        """Register a function as a Huey task.

        Args:
            func: Function to register
            name: Optional task name (defaults to function name)
            max_retries: Maximum retry attempts
            min_backoff: Minimum backoff in milliseconds (converted to seconds)
            max_backoff: Maximum backoff in milliseconds (not used by Huey)

        Returns:
            Huey task that can be called or enqueued
        """
        if not self._available or not self._huey:
            log.warning(f"Cannot register task '{name or func.__name__}': Huey not available")
            return func

        try:
            task_name = name or func.__name__

            # Convert milliseconds to seconds for retry delay
            retry_delay = min_backoff / 1000

            # Decorate with huey.task
            task = self._huey.task(
                name=task_name,
                retries=max_retries,
                retry_delay=int(retry_delay),
            )(func)

            self._tasks[task_name] = task
            log.debug(f"Registered Huey task: {task_name}")

            return task

        except Exception as e:
            log.error(f"Failed to register task '{name or func.__name__}': {e}")
            return func

    def is_available(self) -> bool:
        """Check if Huey driver is available.

        Returns:
            True if driver initialized successfully
        """
        return self._available

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        if not self._available or not self._huey:
            return {"error": "Huey driver not available"}

        try:
            stats = {
                "driver": "huey",
                "backend": "filesystem",
                "storage_path": self._storage_path,
                "available": True,
                "registered_tasks": list(self._tasks.keys()),
            }

            # Try to get pending task count
            try:
                pending = len(self._huey.pending())
                stats["pending_tasks"] = pending
            except Exception as e:
                log.debug(f"Could not fetch pending tasks: {e}")

            # Try to get scheduled task count
            try:
                scheduled = len(self._huey.scheduled())
                stats["scheduled_tasks"] = scheduled
            except Exception as e:
                log.debug(f"Could not fetch scheduled tasks: {e}")

            return stats

        except Exception as e:
            log.error(f"Failed to get Huey stats: {e}")
            return {"error": str(e)}

    def get_task_result(self, task_id: Any) -> dict[str, Any]:
        """Get the result of a task by its ID.

        Huey supports result storage when results=True is enabled.

        Args:
            task_id: Huey result object (must be callable with no args)

        Returns:
            Dictionary with task status and result
        """
        if not self._available or not self._huey:
            return {"status": "error", "error": "Huey driver not available"}

        try:
            # Verify task_id is a Huey result object (callable with no args)
            if not callable(task_id):
                return {
                    "status": "error",
                    "error": "Invalid task_id: expected Huey result object (callable)",
                }

            # Try to get the result (non-blocking check)
            # Huey results raise TaskException or DataStoreTimeout if not ready
            try:
                from huey.exceptions import TaskException

                result = task_id()
                return {
                    "status": "completed",
                    "result": result,
                }
            except TaskException:
                # Task is not ready yet or failed
                return {
                    "status": "pending",
                    "message": "Task is still processing",
                }
            except Exception as e:
                # Actual error during result retrieval
                log.error(f"Error retrieving task result: {e}")
                return {
                    "status": "failed",
                    "error": str(e),
                }

        except Exception as e:
            log.error(f"Failed to get task result: {e}")
            return {"status": "error", "error": str(e)}

    def get_bulk_results(self, task_ids: list[Any]) -> dict[str, Any]:
        """Get results for multiple tasks (for bulk feedback: x of y completed).

        This provides feedback on bulk operations like parallel payroll processing.

        Args:
            task_ids: List of Huey result objects

        Returns:
            Dictionary with aggregated status
        """
        if not self._available or not self._huey:
            return {"error": "Huey driver not available"}

        total = len(task_ids)
        completed = 0
        failed = 0
        pending = 0
        tasks = {}

        for i, task_id in enumerate(task_ids):
            try:
                result_info = self.get_task_result(task_id)
                status = result_info.get("status", "unknown")

                tasks[f"task_{i}"] = result_info

                if status == "completed":
                    completed += 1
                elif status == "error" or status == "failed":
                    failed += 1
                else:
                    pending += 1

            except Exception as e:
                log.debug(f"Error checking task {i}: {e}")
                failed += 1
                tasks[f"task_{i}"] = {"status": "error", "error": str(e)}

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "processing": 0,  # Huey doesn't distinguish pending from processing
            "tasks": tasks,
            "progress_percentage": round((completed / total * 100) if total > 0 else 0, 2),
        }

    def get_huey_instance(self):
        """Get the underlying Huey instance for advanced usage.

        Returns:
            Huey instance or None if not initialized
        """
        return self._huey
