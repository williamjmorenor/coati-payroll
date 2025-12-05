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
"""Tests for logging configuration."""

import logging


def test_log_instance_exists():
    """Test that log instance exists."""
    from coati_payroll.log import log

    assert log is not None
    assert isinstance(log, logging.Logger)


def test_logger_instance_exists():
    """Test that logger instance exists."""
    from coati_payroll.log import logger

    assert logger is not None
    assert isinstance(logger, logging.Logger)


def test_log_level_constant_exists():
    """Test that LOG_LEVEL constant exists."""
    from coati_payroll.log import LOG_LEVEL

    assert LOG_LEVEL is not None
    assert isinstance(LOG_LEVEL, int)


def test_trace_level_defined():
    """Test that TRACE level is defined."""
    from coati_payroll.log import TRACE_LEVEL_NUM

    assert TRACE_LEVEL_NUM == 5
    assert logging.getLevelName(TRACE_LEVEL_NUM) == "TRACE"


def test_trace_method_exists():
    """Test that trace method is added to Logger."""
    from coati_payroll.log import log

    assert hasattr(log, "trace")
    assert callable(log.trace)


def test_can_log_trace_message():
    """Test that we can log a trace message."""
    from coati_payroll.log import log

    # Should not raise an error
    log.trace("Test trace message")


def test_can_log_debug_message():
    """Test that we can log a debug message."""
    from coati_payroll.log import log

    # Should not raise an error
    log.debug("Test debug message")


def test_can_log_info_message():
    """Test that we can log an info message."""
    from coati_payroll.log import log

    # Should not raise an error
    log.info("Test info message")


def test_can_log_warning_message():
    """Test that we can log a warning message."""
    from coati_payroll.log import log

    # Should not raise an error
    log.warning("Test warning message")


def test_can_log_error_message():
    """Test that we can log an error message."""
    from coati_payroll.log import log

    # Should not raise an error
    log.error("Test error message")
