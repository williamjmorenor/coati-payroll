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
"""Vistas module for the payroll application."""

from coati_payroll.vistas.user import user_bp
from coati_payroll.vistas.currency import currency_bp
from coati_payroll.vistas.exchange_rate import exchange_rate_bp
from coati_payroll.vistas.employee import employee_bp
from coati_payroll.vistas.custom_field import custom_field_bp
from coati_payroll.vistas.calculation_rule import calculation_rule_bp
from coati_payroll.vistas.payroll_concepts import (
    percepcion_bp,
    deduccion_bp,
    prestacion_bp,
)
from coati_payroll.vistas.planilla import planilla_bp
from coati_payroll.vistas.tipo_planilla import tipo_planilla_bp
from coati_payroll.vistas.prestamo import prestamo_bp

__all__ = [
    "user_bp",
    "currency_bp",
    "exchange_rate_bp",
    "employee_bp",
    "custom_field_bp",
    "calculation_rule_bp",
    "percepcion_bp",
    "deduccion_bp",
    "prestacion_bp",
    "planilla_bp",
    "tipo_planilla_bp",
    "prestamo_bp",
]
