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
"""Helper functions for tests."""

from tests.helpers.auth import login_user, logout_user
from tests.helpers.assertions import assert_user_exists, assert_redirected_to
from tests.helpers.http import follow_redirects_once

__all__ = [
    "login_user",
    "logout_user",
    "assert_user_exists",
    "assert_redirected_to",
    "follow_redirects_once",
]
