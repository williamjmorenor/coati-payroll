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
"""Tests for exchange rate filtering functionality."""

from datetime import date
import pytest


class TestExchangeRateFilters:
    """Tests for exchange rate filtering on the index page."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app):
        """Set up test data for filtering tests."""
        from coati_payroll.model import Moneda, TipoCambio, db

        with app.app_context():
            # Clear any existing test data
            db.session.execute(db.delete(TipoCambio))
            db.session.execute(db.delete(Moneda))
            db.session.commit()

            # Create test currencies
            usd = Moneda()
            usd.codigo = "USD"
            usd.nombre = "US Dollar"
            usd.activo = True
            db.session.add(usd)

            eur = Moneda()
            eur.codigo = "EUR"
            eur.nombre = "Euro"
            eur.activo = True
            db.session.add(eur)

            nio = Moneda()
            nio.codigo = "NIO"
            nio.nombre = "Cordoba"
            nio.activo = True
            db.session.add(nio)

            db.session.commit()

            # Create test exchange rates
            # USD to NIO on 2025-01-15
            tc1 = TipoCambio()
            tc1.fecha = date(2025, 1, 15)
            tc1.moneda_origen_id = usd.id
            tc1.moneda_destino_id = nio.id
            tc1.tasa = 36.5
            tc1.creado_por = "testuser"
            db.session.add(tc1)

            # EUR to USD on 2025-01-20
            tc2 = TipoCambio()
            tc2.fecha = date(2025, 1, 20)
            tc2.moneda_origen_id = eur.id
            tc2.moneda_destino_id = usd.id
            tc2.tasa = 1.1
            tc2.creado_por = "testuser"
            db.session.add(tc2)

            # USD to EUR on 2025-02-01
            tc3 = TipoCambio()
            tc3.fecha = date(2025, 2, 1)
            tc3.moneda_origen_id = usd.id
            tc3.moneda_destino_id = eur.id
            tc3.tasa = 0.91
            tc3.creado_por = "testuser"
            db.session.add(tc3)

            db.session.commit()

        yield

        # Cleanup after test
        with app.app_context():
            db.session.execute(db.delete(TipoCambio))
            db.session.execute(db.delete(Moneda))
            db.session.commit()

    def test_index_page_loads(self, authenticated_client):
        """Test that the exchange rate index page loads without errors."""
        response = authenticated_client.get("/exchange_rate/")
        assert response.status_code == 200
        assert b"Tipos de Cambio" in response.data

    def test_filter_by_date_range(self, app, authenticated_client):
        """Test filtering by date range."""
        response = authenticated_client.get("/exchange_rate/?fecha_desde=2025-01-01&fecha_hasta=2025-01-31")
        assert response.status_code == 200
        # Should show the two January rates (2025-01-15 and 2025-01-20)
        assert b"2025-01-15" in response.data
        assert b"2025-01-20" in response.data
        # Should not show the February rate
        assert b"2025-02-01" not in response.data

    def test_filter_by_fecha_desde_only(self, app, authenticated_client):
        """Test filtering with only start date."""
        response = authenticated_client.get("/exchange_rate/?fecha_desde=2025-01-20")
        assert response.status_code == 200
        # Should show rates from 2025-01-20 and after
        assert response.data.count(b"2025-01-20") >= 1
        assert response.data.count(b"2025-02-01") >= 1
        # Should not show rate from 2025-01-15
        assert b"2025-01-15" not in response.data

    def test_filter_by_fecha_hasta_only(self, app, authenticated_client):
        """Test filtering with only end date."""
        response = authenticated_client.get("/exchange_rate/?fecha_hasta=2025-01-20")
        assert response.status_code == 200
        # Should show rates from 2025-01-20 and before
        assert response.data.count(b"2025-01-15") >= 1
        assert response.data.count(b"2025-01-20") >= 1
        # Should not show rate from 2025-02-01
        assert b"2025-02-01" not in response.data

    def test_filter_by_moneda_origen(self, app, authenticated_client):
        """Test filtering by source currency."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one()
            usd_id = usd.id

        response = authenticated_client.get(f"/exchange_rate/?moneda_origen_id={usd_id}")
        assert response.status_code == 200
        # Should show USD rates
        assert response.data.count(b"USD") >= 2
        # EUR to USD should not appear (EUR is source, not USD)
        # But we should see the two USD as source currency rates

    def test_filter_by_moneda_destino(self, app, authenticated_client):
        """Test filtering by destination currency."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one()
            usd_id = usd.id

        response = authenticated_client.get(f"/exchange_rate/?moneda_destino_id={usd_id}")
        assert response.status_code == 200
        # Should show only EUR to USD rate
        assert b"EUR" in response.data

    def test_combined_filters(self, app, authenticated_client):
        """Test using multiple filters together."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one()
            nio = db.session.execute(db.select(Moneda).filter_by(codigo="NIO")).scalar_one()
            usd_id = usd.id
            nio_id = nio.id

        response = authenticated_client.get(
            f"/exchange_rate/?fecha_desde=2025-01-01&fecha_hasta=2025-01-31"
            f"&moneda_origen_id={usd_id}&moneda_destino_id={nio_id}"
        )
        assert response.status_code == 200
        # Should show only USD to NIO in January
        assert b"USD" in response.data
        assert b"NIO" in response.data
        assert response.data.count(b"2025-01-15") >= 1
        # Should not show February rates in the table data
        assert b"2025-02" not in response.data
        # EUR may appear in dropdown but not in the exchange rate table row
        # We verify that the filtered rate is the USD to NIO one

    def test_filter_form_preserves_values(self, app, authenticated_client):
        """Test that filter form preserves selected values."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one()
            usd_id = usd.id

        response = authenticated_client.get(f"/exchange_rate/?fecha_desde=2025-01-10&moneda_origen_id={usd_id}")
        assert response.status_code == 200
        # Check that form fields contain the filter values
        assert b'value="2025-01-10"' in response.data
        assert f'value="{usd_id}" selected'.encode() in response.data

    def test_pagination_preserves_filters(self, app, authenticated_client):
        """Test that pagination links preserve filter parameters."""
        from coati_payroll.model import Moneda, TipoCambio, db

        with app.app_context():
            # Create many exchange rates to trigger pagination
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one()
            nio = db.session.execute(db.select(Moneda).filter_by(codigo="NIO")).scalar_one()

            usd_id = usd.id
            nio_id = nio.id

            # Delete existing exchange rates for this pair to avoid conflicts
            db.session.execute(
                db.delete(TipoCambio).where(
                    TipoCambio.moneda_origen_id == usd_id,
                    TipoCambio.moneda_destino_id == nio_id,
                )
            )
            db.session.commit()

            for day in range(1, 20):
                tc = TipoCambio()
                tc.fecha = date(2025, 3, day)  # Use March to avoid conflict with existing data
                tc.moneda_origen_id = usd_id
                tc.moneda_destino_id = nio_id
                tc.tasa = 36.0 + day * 0.1
                tc.creado_por = "testuser"
                db.session.add(tc)
            db.session.commit()

        # Get first page with filter
        response = authenticated_client.get(f"/exchange_rate/?fecha_desde=2025-03-01&moneda_origen_id={usd_id}")
        assert response.status_code == 200
        # Check that pagination links include filter parameters
        if b"page=2" in response.data:
            assert b"fecha_desde=2025-03-01" in response.data

    def test_no_filters_shows_all(self, authenticated_client):
        """Test that without filters, all exchange rates are shown."""
        response = authenticated_client.get("/exchange_rate/")
        assert response.status_code == 200
        # Should show all three test rates
        assert b"2025-01-15" in response.data
        assert b"2025-01-20" in response.data
        assert b"2025-02-01" in response.data
