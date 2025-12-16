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
"""Interest calculation engine for loans.

This module provides functions to calculate interest for loans based on
different methods and amortization schedules.

Supported methods:
- French method (Préstamo Francés): Constant payment amount
- German method (Préstamo Alemán): Constant principal amortization
- Simple and compound interest calculations
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple

from coati_payroll.enums import MetodoAmortizacion, TipoInteres


class CuotaPrestamo(NamedTuple):
    """Represents a single loan installment."""

    numero: int  # Installment number
    fecha_estimada: date  # Estimated payment date
    cuota_total: Decimal  # Total payment amount
    interes: Decimal  # Interest portion
    capital: Decimal  # Principal portion
    saldo: Decimal  # Remaining balance after payment


def calcular_interes_simple(principal: Decimal, tasa_anual: Decimal, dias: int) -> Decimal:
    """Calculate simple interest.

    Formula: I = P * r * t
    Where:
        P = principal (saldo)
        r = annual interest rate (as decimal, e.g., 0.05 for 5%)
        t = time in years (dias / 365)

    Args:
        principal: Loan balance
        tasa_anual: Annual interest rate as percentage (e.g., 5.0 for 5%)
        dias: Number of days to calculate interest for

    Returns:
        Interest amount
    """
    if principal <= 0 or tasa_anual <= 0 or dias <= 0:
        return Decimal("0.00")

    # Convert percentage to decimal (5.0 -> 0.05)
    tasa_decimal = tasa_anual / Decimal("100")

    # Calculate time in years
    tiempo_anios = Decimal(dias) / Decimal("365")

    # Calculate interest: I = P * r * t
    interes = principal * tasa_decimal * tiempo_anios

    return interes.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_interes_compuesto(principal: Decimal, tasa_anual: Decimal, dias: int) -> Decimal:
    """Calculate compound interest.

    Formula: A = P * (1 + r/n)^(n*t)
    Interest = A - P

    For daily compounding:
        n = 365 (compounds daily)

    Args:
        principal: Loan balance
        tasa_anual: Annual interest rate as percentage (e.g., 5.0 for 5%)
        dias: Number of days to calculate interest for

    Returns:
        Interest amount
    """
    if principal <= 0 or tasa_anual <= 0 or dias <= 0:
        return Decimal("0.00")

    # Convert percentage to decimal
    tasa_decimal = tasa_anual / Decimal("100")

    # For simplicity, we compound daily
    n = Decimal("365")
    tiempo_anios = Decimal(dias) / Decimal("365")

    # A = P * (1 + r/n)^(n*t)
    # Use iterative multiplication to maintain decimal precision
    # This is more precise than float conversion for financial calculations
    base = Decimal("1") + (tasa_decimal / n)
    num_periodos = int(n * tiempo_anios)

    # Calculate factor iteratively to maintain precision
    factor = Decimal("1")
    for _ in range(num_periodos):
        factor *= base

    monto_final = principal * factor

    interes = monto_final - principal

    return interes.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_cuota_frances(principal: Decimal, tasa_anual: Decimal, num_cuotas: int) -> Decimal:
    """Calculate constant payment amount for French method.

    Formula: C = P * [r(1+r)^n] / [(1+r)^n - 1]
    Where:
        C = constant payment
        P = principal
        r = periodic interest rate (monthly)
        n = number of periods

    Args:
        principal: Loan amount
        tasa_anual: Annual interest rate as percentage
        num_cuotas: Number of installments

    Returns:
        Constant payment amount
    """
    if principal <= 0 or num_cuotas <= 0:
        return Decimal("0.00")

    # If no interest, simple division
    if tasa_anual <= 0:
        return (principal / Decimal(num_cuotas)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Convert annual rate to monthly rate
    tasa_decimal = tasa_anual / Decimal("100")
    tasa_mensual = tasa_decimal / Decimal("12")

    # Calculate (1 + r)^n using iterative multiplication for precision
    base = Decimal("1") + tasa_mensual
    factor = Decimal("1")
    for _ in range(num_cuotas):
        factor *= base

    # Calculate payment: C = P * [r(1+r)^n] / [(1+r)^n - 1]
    numerador = principal * tasa_mensual * factor
    denominador = factor - Decimal("1")

    if denominador == 0:
        return principal / Decimal(num_cuotas)

    cuota = numerador / denominador

    return cuota.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generar_tabla_amortizacion(
    principal: Decimal,
    tasa_anual: Decimal,
    num_cuotas: int,
    fecha_inicio: date,
    metodo: str = MetodoAmortizacion.FRANCES,
    tipo_interes: str = TipoInteres.SIMPLE,
) -> list[CuotaPrestamo]:
    """Generate complete amortization schedule for a loan.

    Args:
        principal: Loan amount
        tasa_anual: Annual interest rate as percentage
        num_cuotas: Number of installments
        fecha_inicio: Start date for first payment
        metodo: Amortization method (frances or aleman)
        tipo_interes: Interest type (simple or compuesto)

    Returns:
        List of loan installments
    """
    if principal <= 0 or num_cuotas <= 0:
        return []

    tabla: list[CuotaPrestamo] = []
    saldo = principal
    tasa_decimal = tasa_anual / Decimal("100")
    tasa_mensual = tasa_decimal / Decimal("12")

    # Calculate based on method
    if metodo == MetodoAmortizacion.FRANCES:
        # French method: constant payment
        cuota_constante = calcular_cuota_frances(principal, tasa_anual, num_cuotas)

        for i in range(num_cuotas):
            numero = i + 1

            # Calculate interest for this period
            if tasa_anual > 0:
                interes = (saldo * tasa_mensual).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                interes = Decimal("0.00")

            # For last payment, adjust to clear remaining balance
            if numero == num_cuotas:
                capital = saldo
                cuota_total = capital + interes
            else:
                capital = cuota_constante - interes
                cuota_total = cuota_constante

            saldo_nuevo = saldo - capital

            # Estimate payment date (monthly intervals)
            from dateutil.relativedelta import relativedelta

            fecha_estimada = fecha_inicio + relativedelta(months=numero)

            tabla.append(
                CuotaPrestamo(
                    numero=numero,
                    fecha_estimada=fecha_estimada,
                    cuota_total=cuota_total,
                    interes=interes,
                    capital=capital,
                    saldo=max(saldo_nuevo, Decimal("0.00")),
                )
            )

            saldo = saldo_nuevo

    elif metodo == MetodoAmortizacion.ALEMAN:
        # German method: constant principal amortization
        capital_constante = (principal / Decimal(num_cuotas)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        for i in range(num_cuotas):
            numero = i + 1

            # Calculate interest for this period
            if tasa_anual > 0:
                interes = (saldo * tasa_mensual).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                interes = Decimal("0.00")

            # For last payment, adjust to clear remaining balance
            if numero == num_cuotas:
                capital = saldo
            else:
                capital = capital_constante

            cuota_total = capital + interes
            saldo_nuevo = saldo - capital

            # Estimate payment date (monthly intervals)
            from dateutil.relativedelta import relativedelta

            fecha_estimada = fecha_inicio + relativedelta(months=numero)

            tabla.append(
                CuotaPrestamo(
                    numero=numero,
                    fecha_estimada=fecha_estimada,
                    cuota_total=cuota_total,
                    interes=interes,
                    capital=capital,
                    saldo=max(saldo_nuevo, Decimal("0.00")),
                )
            )

            saldo = saldo_nuevo

    return tabla


def calcular_interes_periodo(
    saldo: Decimal, tasa_anual: Decimal, fecha_desde: date, fecha_hasta: date, tipo_interes: str = TipoInteres.SIMPLE
) -> tuple[Decimal, int]:
    """Calculate interest for a specific period.

    This function is used during payroll processing to calculate
    interest for the days elapsed since the last calculation.

    Args:
        saldo: Current loan balance
        tasa_anual: Annual interest rate as percentage
        fecha_desde: Start date of period
        fecha_hasta: End date of period
        tipo_interes: Type of interest (simple or compuesto)

    Returns:
        Tuple of (interest amount, number of days)
    """
    if saldo <= 0 or tasa_anual <= 0:
        return Decimal("0.00"), 0

    # Calculate days elapsed
    dias = (fecha_hasta - fecha_desde).days

    if dias <= 0:
        return Decimal("0.00"), 0

    # Calculate interest based on type
    if tipo_interes == TipoInteres.COMPUESTO:
        interes = calcular_interes_compuesto(saldo, tasa_anual, dias)
    else:
        # Default to simple interest
        interes = calcular_interes_simple(saldo, tasa_anual, dias)

    return interes, dias
