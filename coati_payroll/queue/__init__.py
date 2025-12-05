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
"""Queue module for background job processing.

This module provides a unified interface for background job processing
with automatic backend selection:
- Dramatiq + Redis (production/high-scale deployments)
- Huey + Filesystem (fallback for environments without Redis)

Usage:
    from coati_payroll.queue import get_queue_driver
    
    queue = get_queue_driver()
    queue.enqueue('calculate_employee_payroll', employee_id=123, payroll_id=456)
"""

from __future__ import annotations

from coati_payroll.queue.driver import QueueDriver
from coati_payroll.queue.selector import get_queue_driver

__all__ = ["QueueDriver", "get_queue_driver"]
