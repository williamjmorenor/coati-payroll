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
"""Queue driver implementations."""

from __future__ import annotations

from coati_payroll.queue.drivers.dramatiq_driver import DramatiqDriver
from coati_payroll.queue.drivers.huey_driver import HueyDriver
from coati_payroll.queue.drivers.noop_driver import NoopQueueDriver

__all__ = ["DramatiqDriver", "HueyDriver", "NoopQueueDriver"]
