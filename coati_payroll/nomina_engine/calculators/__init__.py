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
"""Calculators for payroll processing."""

from .concept_calculator import ConceptCalculator
from .salary_calculator import SalaryCalculator
from .perception_calculator import PerceptionCalculator
from .deduction_calculator import DeductionCalculator
from .benefit_calculator import BenefitCalculator
from .exchange_rate_calculator import ExchangeRateCalculator

__all__ = [
    "ConceptCalculator",
    "SalaryCalculator",
    "PerceptionCalculator",
    "DeductionCalculator",
    "BenefitCalculator",
    "ExchangeRateCalculator",
]
