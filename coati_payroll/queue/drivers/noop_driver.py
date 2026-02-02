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

"""No-op queue driver for test environments.

This driver avoids importing optional dependencies (huey/dramatiq) while
providing a compatible interface.
"""

from __future__ import annotations

from typing import Any, Callable

from coati_payroll.queue.driver import QueueDriver


class NoopQueueDriver(QueueDriver):
    """Queue driver that does nothing (used for tests)."""

    def enqueue(self, task_name: str, *args: Any, delay: int | None = None, **kwargs: Any) -> Any:
        return {"task": task_name, "enqueued": False, "noop": True}

    def register_task(
        self,
        func: Callable,
        name: str | None = None,
        max_retries: int = 0,
        min_backoff: int = 0,
        max_backoff: int = 0,
    ) -> Callable:
        return func

    def is_available(self) -> bool:
        return True

    def get_stats(self) -> dict[str, Any]:
        return {"driver": "noop", "available": True}

    def get_task_result(self, task_id: Any) -> dict[str, Any]:
        return {"status": "noop", "task_id": task_id}

    def get_bulk_results(self, task_ids: list[Any]) -> dict[str, Any]:
        return {"total": len(task_ids), "completed": 0, "failed": 0, "pending": len(task_ids), "tasks": {}}
