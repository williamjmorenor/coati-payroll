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
"""Repository for ConfiguracionCalculos operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from coati_payroll.model import ConfiguracionCalculos
from .base_repository import BaseRepository


class ConfigRepository(BaseRepository[ConfiguracionCalculos]):
    """Repository for ConfiguracionCalculos operations."""

    def get_by_id(self, config_id: str) -> Optional[ConfiguracionCalculos]:
        """Get configuration by ID."""
        return self.session.get(ConfiguracionCalculos, config_id)

    def get_for_empresa(self, empresa_id: Optional[str]) -> ConfiguracionCalculos:
        """Get configuration for empresa, or global default."""
        from sqlalchemy import select

        # Try company-specific configuration
        if empresa_id:
            config = (
                self.session.execute(
                    select(ConfiguracionCalculos).filter(
                        ConfiguracionCalculos.empresa_id == empresa_id,
                        ConfiguracionCalculos.activo.is_(True),
                    )
                )
                .unique()
                .scalar_one_or_none()
            )
            if config:
                return config

        # Try global default
        config = (
            self.session.execute(
                select(ConfiguracionCalculos).filter(
                    ConfiguracionCalculos.empresa_id.is_(None),
                    ConfiguracionCalculos.pais_id.is_(None),
                    ConfiguracionCalculos.activo.is_(True),
                )
            )
            .unique()
            .scalar_one_or_none()
        )

        if config:
            return config

        # Return default instance (not saved to DB)
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

    def save(self, config: ConfiguracionCalculos) -> ConfiguracionCalculos:
        """Save configuration."""
        self.session.add(config)
        return config
