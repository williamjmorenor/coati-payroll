# SPDX-License-Identifier: Apache-2.0
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
"""Mapping of novelty codes to their calculation behavior.

This module defines the mapping between novelty codes and their
calculation behavior (perception/deduction, gravable, etc.).
"""

# ................................ CONTANTES ................................ #
NOVELTY_CODES = {
    "HORAS_EXTRA": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Horas extra trabajadas",
    },
    "HORAS_EXTRA_DOBLES": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Horas extra dobles (feriados/domingos)",
    },
    "AUSENCIA": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Ausencia no justificada",
    },
    "INCAPACIDAD": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Incapacidad médica",
    },
    "COMISION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Comisiones por ventas",
    },
    "BONIFICACION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Bonificación",
    },
    "VIATICO": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Viáticos",
    },
    "VACACIONES": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Pago de vacaciones",
    },
    "ADELANTO": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Adelanto de salario",
    },
    "PRESTAMO": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Cuota de préstamo",
    },
    # A. Compensación Base y Directa
    "BONO_OBJETIVOS": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Bono por cumplimiento de objetivos",
    },
    "BONO_ANUAL": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Bono anual o trimestral",
    },
    "PLUS_PELIGROSIDAD": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Plus por peligrosidad o toxicidad",
    },
    "PLUS_NOCTURNO": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Plus por trabajo nocturno",
    },
    "PLUS_ANTIGUEDAD": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Plus por antigüedad",
    },
    # B. Compensaciones en Especie y Beneficios
    "USO_VEHICULO": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Uso de vehículo de empresa",
    },
    "SEGURO_SALUD": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Seguro de salud privado",
    },
    "APORTE_PENSION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Aporte patronal a pensión/retiro",
    },
    "STOCK_OPTIONS": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Opciones de compra de acciones",
    },
    "SUBSIDIO_ALIMENTACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Subsidio de alimentación",
    },
    "SUBSIDIO_TRANSPORTE": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Subsidio de transporte",
    },
    "SUBSIDIO_GUARDERIA": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Subsidio de guardería",
    },
    # C. Compensaciones por Tiempo y Bienestar
    "PAGO_FESTIVOS": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Pago por días festivos trabajados",
    },
    "THIRTEENTH_SALARY": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Aguinaldo o gratificación anual",
    },
    "UTILIDADES": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Participación en utilidades",
    },
    "PERMISO_PAGADO": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Permisos pagados (enfermedad, maternidad, etc.)",
    },
    "FONDO_AHORRO_EMPRESA": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Aporte empresa a fondo de ahorro",
    },
    "FONDO_AHORRO_EMPLEADO": {
        "tipo": "deduccion",
        "gravable": False,
        "descripcion": "Aporte empleado a fondo de ahorro",
    },
    # D. Reembolsos y Dietas
    "GASTOS_REPRESENTACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Gastos de representación",
    },
    "REEMBOLSO_FORMACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Reembolso de gastos de formación",
    },
    "REEMBOLSO_MEDICO": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Reembolso de gastos médicos",
    },
    # E. Pagos por Eventos Específicos
    "INDEMNIZACION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Indemnización por despido",
    },
    "COMPENSACION_REUBICACION": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Compensación por reubicación",
    },
    "PREMIO_PUNTUALIDAD": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Premio por puntualidad/asistencia",
    },
    "PREMIO_INNOVACION": {
        "tipo": "percepcion",
        "gravable": True,
        "descripcion": "Premio por ideas innovadoras",
    },
    "AYUDA_FALLECIMIENTO": {
        "tipo": "percepcion",
        "gravable": False,
        "descripcion": "Ayuda por fallecimiento de familiar",
    },
}
