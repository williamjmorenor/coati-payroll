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
"""Assertion helpers for tests."""

from coati_payroll.model import Usuario


def assert_user_exists(db_session, usuario):
    """
    Assert that a user exists in the database.
    
    Args:
        db_session: SQLAlchemy session
        usuario: Username to check
    
    Raises:
        AssertionError: If user does not exist
    """
    user = db_session.query(Usuario).filter_by(usuario=usuario).first()
    assert user is not None, f"User '{usuario}' should exist in database"
    return user


def assert_redirected_to(response, expected_location):
    """
    Assert that response is a redirect to the expected location.
    
    Args:
        response: Flask response object
        expected_location: Expected redirect location (can be partial match)
    
    Raises:
        AssertionError: If not a redirect or wrong location
    """
    assert response.status_code in (301, 302, 303, 307, 308), \
        f"Expected redirect but got status {response.status_code}"
    
    location = response.headers.get("Location", "")
    assert expected_location in location, \
        f"Expected redirect to contain '{expected_location}' but got '{location}'"
