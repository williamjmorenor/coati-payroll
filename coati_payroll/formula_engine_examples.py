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
"""Formula calculation engine examples for payroll processing."""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #


# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #


# Example Nicaragua IR schema for reference
EXAMPLE_IR_NICARAGUA_SCHEMA = {
    "meta": {
        "name": "IR Laboral Nicaragua",
        "jurisdiction": "Nicaragua",
        "reference_currency": "NIO",
        "version": "1.0.0",
        "description": "Cálculo del Impuesto sobre la Renta para salarios en Nicaragua. "
        "La moneda de referencia es NIO. El tipo de cambio se aplica si la planilla "
        "está en una moneda diferente.",
    },
    "inputs": [
        {
            "name": "salario_mensual",
            "type": "decimal",
            "source": "empleado.salario_base",
            "description": "Salario mensual bruto",
        },
        {
            "name": "inss_laboral",
            "type": "decimal",
            "source": "calculated",
            "description": "Deducción INSS laboral",
        },
        {
            "name": "meses_restantes",
            "type": "integer",
            "default": 12,
            "description": "Meses restantes en el año fiscal",
        },
        {
            "name": "salario_acumulado",
            "type": "decimal",
            "default": 0,
            "description": "Salario bruto acumulado del año",
        },
        {
            "name": "ir_retenido_acumulado",
            "type": "decimal",
            "default": 0,
            "description": "IR ya retenido en el año",
        },
    ],
    "steps": [
        {
            "name": "salario_neto_mensual",
            "type": "calculation",
            "formula": "salario_mensual - inss_laboral",
            "description": "Salario después de INSS",
        },
        {
            "name": "expectativa_anual",
            "type": "calculation",
            "formula": "salario_neto_mensual * meses_restantes",
            "description": "Proyección de salario restante del año",
        },
        {
            "name": "base_imponible_anual",
            "type": "calculation",
            "formula": "salario_acumulado + expectativa_anual",
            "description": "Base imponible anual total",
        },
        {
            "name": "ir_anual",
            "type": "tax_lookup",
            "table": "tabla_ir_nicaragua",
            "input": "base_imponible_anual",
            "description": "Cálculo IR anual según tabla",
        },
        {
            "name": "ir_pendiente",
            "type": "calculation",
            "formula": "ir_anual - ir_retenido_acumulado",
            "description": "IR pendiente de retener",
        },
        {
            "name": "ir_mensual",
            "type": "calculation",
            "formula": "ir_pendiente / meses_restantes",
            "description": "IR a retener este mes",
        },
    ],
    "tax_tables": {
        "tabla_ir_nicaragua": [
            {"min": 0, "max": 100000, "rate": 0, "fixed": 0, "over": 0},
            {"min": 100000.01, "max": 200000, "rate": 0.15, "fixed": 0, "over": 100000},
            {
                "min": 200000.01,
                "max": 350000,
                "rate": 0.20,
                "fixed": 15000,
                "over": 200000,
            },
            {
                "min": 350000.01,
                "max": 500000,
                "rate": 0.25,
                "fixed": 45000,
                "over": 350000,
            },
            {
                "min": 500000.01,
                "max": None,
                "rate": 0.30,
                "fixed": 82500,
                "over": 500000,
            },
        ]
    },
    "output": "ir_mensual",
}
