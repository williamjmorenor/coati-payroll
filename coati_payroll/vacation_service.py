# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Vacation service for integration with payroll engine.

This module provides the service layer for vacation accrual and usage
during payroll execution.
"""

from __future__ import annotations

# <-------------------------------------------------------------------------> #
# Standard library
# <-------------------------------------------------------------------------> #
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING

# <-------------------------------------------------------------------------> #
# Third party libraries
# <-------------------------------------------------------------------------> #

# <-------------------------------------------------------------------------> #
# Local modules
# <-------------------------------------------------------------------------> #
from coati_payroll.enums import VacationLedgerType, AccrualMethod, AccrualFrequency
from coati_payroll.log import log

if TYPE_CHECKING:
    from coati_payroll.model import (
        Empleado,
        Planilla,
        VacationPolicy,
        VacationAccount,
        NominaEmpleado,
        ConfiguracionCalculos,
    )


class VacationService:
    """Service for vacation accrual and usage during payroll execution."""

    def __init__(self, planilla: Planilla, periodo_inicio: date, periodo_fin: date):
        """Initialize vacation service.

        Args:
            planilla: The payroll being executed
            periodo_inicio: Start date of payroll period
            periodo_fin: End date of payroll period
        """
        self.planilla = planilla
        self.periodo_inicio = periodo_inicio
        self.periodo_fin = periodo_fin

    def _obtener_config_calculos(self) -> ConfiguracionCalculos:
        """Get calculation configuration for the current planilla.

        Returns configuration specific to the planilla's company, or global defaults.
        Always returns a valid configuration object with defaults if none exists.

        Returns:
            ConfiguracionCalculos instance with appropriate values
        """
        from coati_payroll.model import db, ConfiguracionCalculos

        empresa_id = self.planilla.empresa_id if self.planilla else None

        # Try to find company-specific configuration
        if empresa_id:
            config = (
                db.session.execute(
                    db.select(ConfiguracionCalculos).filter(
                        ConfiguracionCalculos.empresa_id == empresa_id,
                        ConfiguracionCalculos.activo.is_(True),
                    )
                )
                .scalars()
                .first()
            )
            if config:
                return config

        # Try to find global default (no empresa_id, no pais_id)
        config = (
            db.session.execute(
                db.select(ConfiguracionCalculos).filter(
                    ConfiguracionCalculos.empresa_id.is_(None),
                    ConfiguracionCalculos.pais_id.is_(None),
                    ConfiguracionCalculos.activo.is_(True),
                )
            )
            .scalars()
            .first()
        )
        if config:
            return config

        # If no configuration exists, return a default instance (not saved to DB)
        # This ensures backward compatibility with existing tests
        from decimal import Decimal

        return ConfiguracionCalculos(
            empresa_id=None,
            pais_id=None,
            dias_mes_nomina=30,
            dias_anio_nomina=365,
            horas_jornada_diaria=Decimal("8.00"),
            dias_mes_vacaciones=30,
            dias_anio_vacaciones=365,
            considerar_bisiesto_vacaciones=True,
            dias_anio_financiero=365,
            meses_anio_financiero=12,
            dias_quincena=15,
            dias_mes_antiguedad=30,
            dias_anio_antiguedad=365,
            activo=True,
        )

    def acumular_vacaciones_empleado(
        self, empleado: Empleado, nomina_empleado: NominaEmpleado, usuario: str | None = None
    ) -> Decimal:
        """Accumulate vacation for an employee during payroll execution.

        This method is called during payroll processing to automatically
        accrue vacation time based on the employee's vacation policy.

        Args:
            empleado: The employee to accrue vacation for
            nomina_empleado: The payroll record for this employee
            usuario: Username executing the payroll

        Returns:
            The amount of vacation accrued
        """
        from coati_payroll.model import db, VacationAccount, VacationLedger

        # Get active vacation account for this employee and payroll
        account = db.session.execute(
            db.select(VacationAccount)
            .filter(
                VacationAccount.empleado_id == empleado.id,
                VacationAccount.activo.is_(True),
            )
            .join(VacationAccount.policy)
            .filter(
                (VacationAccount.policy.has(planilla_id=self.planilla.id))
                | (VacationAccount.policy.has(empresa_id=self.planilla.empresa_id))
                | ((VacationAccount.policy.has(planilla_id=None)) & (VacationAccount.policy.has(empresa_id=None)))
            )
        ).scalar_one_or_none()

        if not account:
            log.debug(
                f"No active vacation account found for employee {empleado.codigo_empleado} "
                f"in payroll {self.planilla.nombre}"
            )
            return Decimal("0.00")

        policy = account.policy

        # Check if employee meets minimum service requirement
        if empleado.fecha_alta:
            dias_servicio = (self.periodo_fin - empleado.fecha_alta).days
            if dias_servicio < policy.min_service_days:
                log.debug(
                    f"Employee {empleado.codigo_empleado} has not met minimum service days "
                    f"({dias_servicio} < {policy.min_service_days})"
                )
                return Decimal("0.00")

        # Calculate accrual amount based on policy
        accrual_amount = self._calcular_acumulacion(empleado, account, nomina_empleado)

        if accrual_amount <= 0:
            return Decimal("0.00")

        # Check max balance limit
        if policy.max_balance:
            if account.current_balance + accrual_amount > policy.max_balance:
                # Cap at max balance
                accrual_amount = policy.max_balance - account.current_balance
                if accrual_amount <= 0:
                    log.debug(
                        f"Employee {empleado.codigo_empleado} has reached max vacation balance "
                        f"({account.current_balance} >= {policy.max_balance})"
                    )
                    return Decimal("0.00")

        # Create ledger entry for accrual
        ledger_entry = VacationLedger(
            account_id=account.id,
            empleado_id=empleado.id,
            fecha=self.periodo_fin,
            entry_type=VacationLedgerType.ACCRUAL,
            quantity=accrual_amount,
            source="payroll",
            reference_id=nomina_empleado.id,
            reference_type="nomina_empleado",
            observaciones=f"Acumulación automática en nómina del {self.periodo_inicio} al {self.periodo_fin}",
            creado_por=usuario,
        )

        # Update account balance
        account.current_balance = account.current_balance + accrual_amount
        account.last_accrual_date = self.periodo_fin
        account.modificado_por = usuario

        ledger_entry.balance_after = account.current_balance

        db.session.add(ledger_entry)
        db.session.flush()

        log.info(
            f"Accrued {accrual_amount} {policy.unit_type} vacation for employee "
            f"{empleado.codigo_empleado} (new balance: {account.current_balance})"
        )

        return accrual_amount

    def _calcular_acumulacion(
        self, empleado: Empleado, account: VacationAccount, nomina_empleado: NominaEmpleado
    ) -> Decimal:
        """Calculate vacation accrual amount based on policy.

        Args:
            empleado: The employee
            account: The vacation account
            nomina_empleado: The payroll record

        Returns:
            Amount to accrue
        """
        policy = account.policy

        if policy.accrual_method == AccrualMethod.PERIODIC:
            return self._calcular_acumulacion_periodica(policy)
        elif policy.accrual_method == AccrualMethod.PROPORTIONAL:
            return self._calcular_acumulacion_proporcional(empleado, policy, nomina_empleado)
        elif policy.accrual_method == AccrualMethod.SENIORITY:
            return self._calcular_acumulacion_antiguedad(empleado, policy)
        else:
            log.warning(f"Unknown accrual method: {policy.accrual_method}")
            return Decimal("0.00")

    def _calcular_acumulacion_periodica(self, policy: VacationPolicy) -> Decimal:
        """Calculate periodic accrual (fixed amount per period).

        Args:
            policy: The vacation policy

        Returns:
            Accrual amount
        """
        # For periodic accrual, the rate is the amount per configured frequency
        # If frequency matches payroll period, use the rate directly
        # Otherwise, prorate based on actual days in period

        dias_periodo = (self.periodo_fin - self.periodo_inicio).days + 1

        # Get configuration for vacation calculations
        config = self._obtener_config_calculos()

        # Determine expected days for frequency using configuration
        if policy.accrual_frequency == AccrualFrequency.MONTHLY:
            dias_esperados = config.dias_mes_vacaciones
        elif policy.accrual_frequency == AccrualFrequency.BIWEEKLY:
            dias_esperados = config.dias_quincena
        elif policy.accrual_frequency == AccrualFrequency.ANNUAL:
            dias_esperados = config.dias_anio_vacaciones
        else:
            dias_esperados = config.dias_mes_vacaciones

        # Prorate if period doesn't match frequency
        if dias_periodo == dias_esperados:
            return policy.accrual_rate
        else:
            # Prorate based on days
            return (policy.accrual_rate * Decimal(dias_periodo) / Decimal(dias_esperados)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

    def _calcular_acumulacion_proporcional(
        self, empleado: Empleado, policy: VacationPolicy, nomina_empleado: NominaEmpleado
    ) -> Decimal:
        """Calculate proportional accrual (based on worked days/hours).

        Args:
            empleado: The employee
            policy: The vacation policy
            nomina_empleado: The payroll record

        Returns:
            Accrual amount
        """
        # For proportional accrual, calculate based on actual worked days/hours
        # This requires tracking in the payroll record

        dias_periodo = (self.periodo_fin - self.periodo_inicio).days + 1

        if policy.accrual_basis == "days_worked":
            # Assume full days worked for now (could be enhanced to track absences)
            dias_trabajados = Decimal(dias_periodo)
            return (policy.accrual_rate * dias_trabajados).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        elif policy.accrual_basis == "hours_worked":
            # Calculate based on hours (would need hours tracking in payroll)
            # For now, estimate based on standard hours from configuration
            config = self._obtener_config_calculos()
            horas_estandar = Decimal(str(config.horas_jornada_diaria)) * Decimal(dias_periodo)
            return (policy.accrual_rate * horas_estandar).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        else:
            return Decimal("0.00")

    def _calcular_acumulacion_antiguedad(self, empleado: Empleado, policy: VacationPolicy) -> Decimal:
        """Calculate seniority-based accrual (tiered by years of service).

        Args:
            empleado: The employee
            policy: The vacation policy

        Returns:
            Accrual amount
        """
        if not empleado.fecha_alta or not policy.seniority_tiers:
            return Decimal("0.00")

        # Get configuration for seniority calculations
        config = self._obtener_config_calculos()

        # Calculate years of service
        # Use configured days per year, with leap year consideration if enabled
        dias_anio = Decimal(str(config.dias_anio_antiguedad))
        if config.considerar_bisiesto_vacaciones:
            # Use 365.25 to account for leap years
            dias_anio = Decimal("365.25")
        anos_servicio = (self.periodo_fin - empleado.fecha_alta).days / float(dias_anio)

        # Find applicable tier
        rate = Decimal("0.00")
        for tier in sorted(policy.seniority_tiers, key=lambda t: t.get("years", 0), reverse=True):
            if anos_servicio >= tier.get("years", 0):
                rate = Decimal(str(tier.get("rate", 0)))
                break

        if rate == 0:
            return Decimal("0.00")

        # For seniority, rate is typically annual, so prorate for period
        if policy.accrual_frequency == AccrualFrequency.ANNUAL:
            dias_periodo = (self.periodo_fin - self.periodo_inicio).days + 1
            dias_anio = Decimal(str(config.dias_anio_vacaciones))
            return (rate * Decimal(dias_periodo) / dias_anio).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        else:
            # If frequency is monthly/biweekly, divide rate accordingly
            meses_anio = Decimal(str(config.meses_anio_financiero))
            return (rate / meses_anio).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    def procesar_novedades_vacaciones(
        self, empleado: Empleado, novedades: dict | list, usuario: str | None = None
    ) -> Decimal:
        """Process vacation novelties (leave taken) during payroll execution.

        This method processes vacation leave novelties that have been approved
        and creates ledger entries to reduce the vacation balance.

        Args:
            empleado: The employee
            novedades: Dictionary or list of novelties to process
            usuario: Username executing the payroll

        Returns:
            Total vacation days/hours used
        """
        from coati_payroll.model import db, VacationNovelty, VacationLedger, NominaNovedad

        total_usado = Decimal("0.00")

        # Query vacation-related novedades for this employee in this period
        nomina_novedades = (
            db.session.execute(
                db.select(NominaNovedad).filter(
                    NominaNovedad.empleado_id == empleado.id,
                    NominaNovedad.es_descanso_vacaciones.is_(True),
                    NominaNovedad.fecha_novedad >= self.periodo_inicio,
                    NominaNovedad.fecha_novedad <= self.periodo_fin,
                )
            )
            .scalars()
            .all()
        )

        for nomina_novedad in nomina_novedades:
            # Get the associated vacation novelty
            if not nomina_novedad.vacation_novelty_id:
                continue

            vac_novelty = db.session.get(VacationNovelty, nomina_novedad.vacation_novelty_id)

            if not vac_novelty or vac_novelty.estado != "aprobado":
                continue

            # Skip if already processed (has ledger entry)
            if vac_novelty.ledger_entry_id:
                continue

            account = vac_novelty.account

            # Create ledger entry for usage
            ledger_entry = VacationLedger(
                account_id=account.id,
                empleado_id=empleado.id,
                fecha=self.periodo_fin,
                entry_type=VacationLedgerType.USAGE,
                quantity=-abs(vac_novelty.units),  # Negative for usage
                source="novelty",
                reference_id=vac_novelty.id,
                reference_type="vacation_novelty",
                observaciones=f"Vacaciones del {vac_novelty.start_date} al {vac_novelty.end_date}",
                creado_por=usuario,
            )

            # Update account balance
            account.current_balance = account.current_balance - abs(vac_novelty.units)
            account.modificado_por = usuario

            ledger_entry.balance_after = account.current_balance

            # Link ledger entry to novelty
            vac_novelty.ledger_entry_id = ledger_entry.id
            vac_novelty.estado = "disfrutado"

            db.session.add(ledger_entry)
            db.session.flush()

            total_usado = total_usado + abs(vac_novelty.units)

            log.info(
                f"Processed vacation usage of {abs(vac_novelty.units)} for employee "
                f"{empleado.codigo_empleado} (new balance: {account.current_balance})"
            )

        return total_usado
