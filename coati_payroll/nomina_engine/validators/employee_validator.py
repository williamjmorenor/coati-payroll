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
"""Validator for Employee."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from coati_payroll.model import Empleado
from ..domain.payroll_context import PayrollContext
from ..results.validation_result import ValidationResult
from ..validators.base_validator import BaseValidator


class EmployeeValidator(BaseValidator):
    """Validates that an employee is eligible for payroll processing."""

    def validate(self, context: PayrollContext) -> ValidationResult:
        """Validate employee - this method signature is required by BaseValidator."""
        # This validator is called per-employee, not per-context
        # So we provide a separate method
        result = ValidationResult()
        return result

    def validate_employee(
        self, empleado: Empleado, planilla_empresa_id: str | None, periodo_inicio: date, periodo_fin: date
    ) -> ValidationResult:
        """Validate employee for payroll processing."""
        result = ValidationResult()

        if not empleado.activo:
            result.add_error(f"Empleado {empleado.codigo_empleado} no está activo")

        if empleado.fecha_alta:
            if empleado.fecha_alta > date.today():
                result.add_error(
                    f"Empleado {empleado.codigo_empleado}: fecha de ingreso ({empleado.fecha_alta}) "
                    f"es posterior a la fecha actual"
                )
            if empleado.fecha_alta > periodo_fin:
                result.add_error(
                    f"Empleado {empleado.codigo_empleado}: fecha de ingreso ({empleado.fecha_alta}) "
                    f"es posterior al período a procesar ({periodo_fin})"
                )
        else:
            result.add_error(f"Empleado {empleado.codigo_empleado} no tiene fecha de ingreso definida")

        if empleado.fecha_baja and empleado.fecha_baja < periodo_inicio:
            result.add_error(
                f"Empleado {empleado.codigo_empleado}: fecha de salida ({empleado.fecha_baja}) "
                f"es anterior al inicio del período ({periodo_inicio})"
            )

        if not empleado.identificacion_personal:
            result.add_error(f"Empleado {empleado.codigo_empleado} no tiene identificación personal")

        if empleado.salario_base <= Decimal("0.00"):
            result.add_error(
                f"Empleado {empleado.codigo_empleado} tiene salario base inválido ({empleado.salario_base})"
            )

        if not empleado.empresa_id:
            result.add_error(f"Empleado {empleado.codigo_empleado} no está asignado a ninguna empresa")

        if planilla_empresa_id and empleado.empresa_id:
            if empleado.empresa_id != planilla_empresa_id:
                result.add_error(
                    f"Empleado {empleado.codigo_empleado} pertenece a empresa diferente a la planilla. "
                    f"Empleado empresa_id={empleado.empresa_id}, Planilla empresa_id={planilla_empresa_id}"
                )

        if not empleado.moneda_id:
            result.add_error(f"Empleado {empleado.codigo_empleado} no tiene moneda definida")

        return result
