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
"""Tests for exchange rate CRUD operations."""

from datetime import date
import pytest


class TestExchangeRateCRUD:
    """Tests for exchange rate CRUD routes."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app):
        """Set up test data for exchange rate tests."""
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

            nio = Moneda()
            nio.codigo = "NIO"
            nio.nombre = "Cordoba"
            nio.activo = True
            db.session.add(nio)

            db.session.commit()

    def test_exchange_rate_new_get_shows_form(self, authenticated_client):
        """Test that new exchange rate GET request shows the form."""
        response = authenticated_client.get("/exchange_rate/new")
        assert response.status_code == 200
        assert b"Nuevo Tipo de Cambio" in response.data or b"form" in response.data.lower()

    def test_exchange_rate_new_post_creates_rate(self, authenticated_client, app):
        """Test creating a new exchange rate."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            # Get currency IDs
            usd = db.session.execute(
                db.select(Moneda).filter_by(codigo="USD")
            ).scalar_one()
            nio = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one()
            usd_id = usd.id
            nio_id = nio.id

        response = authenticated_client.post(
            "/exchange_rate/new",
            data={
                "fecha": "2024-01-01",
                "moneda_origen_id": usd_id,
                "moneda_destino_id": nio_id,
                "tasa": "36.5",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            from coati_payroll.model import TipoCambio, db

            rate = db.session.execute(
                db.select(TipoCambio).filter_by(moneda_origen_id=usd_id)
            ).scalar_one_or_none()
            assert rate is not None
            # Decimal may have many trailing zeros
            assert float(rate.tasa) == 36.5

    def test_exchange_rate_edit_get_shows_form(self, authenticated_client, app):
        """Test that edit exchange rate GET request shows the form with data."""
        from coati_payroll.model import Moneda, TipoCambio, db

        with app.app_context():
            # Get currencies
            usd = db.session.execute(
                db.select(Moneda).filter_by(codigo="USD")
            ).scalar_one()
            nio = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one()

            # Create a test exchange rate
            rate = TipoCambio()
            rate.fecha = date(2024, 1, 1)
            rate.moneda_origen_id = usd.id
            rate.moneda_destino_id = nio.id
            rate.tasa = 36.5
            db.session.add(rate)
            db.session.commit()
            rate_id = rate.id

        response = authenticated_client.get(f"/exchange_rate/edit/{rate_id}")
        assert response.status_code == 200

    def test_exchange_rate_edit_post_updates_rate(self, authenticated_client, app):
        """Test updating an existing exchange rate."""
        from coati_payroll.model import Moneda, TipoCambio, db

        with app.app_context():
            # Get currencies
            usd = db.session.execute(
                db.select(Moneda).filter_by(codigo="USD")
            ).scalar_one()
            nio = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one()

            # Create a test exchange rate
            rate = TipoCambio()
            rate.fecha = date(2024, 1, 1)
            rate.moneda_origen_id = usd.id
            rate.moneda_destino_id = nio.id
            rate.tasa = 36.5
            db.session.add(rate)
            db.session.commit()
            rate_id = rate.id

        with app.app_context():
            # Get fresh IDs within the context
            usd = db.session.execute(
                db.select(Moneda).filter_by(codigo="USD")
            ).scalar_one()
            nio = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one()
            usd_id = usd.id
            nio_id = nio.id

        response = authenticated_client.post(
            f"/exchange_rate/edit/{rate_id}",
            data={
                "fecha": "2024-01-02",
                "moneda_origen_id": usd_id,
                "moneda_destino_id": nio_id,
                "tasa": "37.0",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            rate = db.session.get(TipoCambio, rate_id)
            assert rate.fecha == date(2024, 1, 2)
            assert float(rate.tasa) == 37.0

    def test_exchange_rate_edit_nonexistent_redirects(self, authenticated_client):
        """Test that editing a non-existent exchange rate redirects."""
        response = authenticated_client.get(
            "/exchange_rate/edit/NONEXISTENT", follow_redirects=True
        )
        assert response.status_code == 200

    def test_exchange_rate_delete_removes_rate(self, authenticated_client, app):
        """Test deleting an exchange rate."""
        from coati_payroll.model import Moneda, TipoCambio, db

        with app.app_context():
            # Get currencies
            usd = db.session.execute(
                db.select(Moneda).filter_by(codigo="USD")
            ).scalar_one()
            nio = db.session.execute(
                db.select(Moneda).filter_by(codigo="NIO")
            ).scalar_one()

            # Create a test exchange rate
            rate = TipoCambio()
            rate.fecha = date(2024, 1, 1)
            rate.moneda_origen_id = usd.id
            rate.moneda_destino_id = nio.id
            rate.tasa = 36.5
            db.session.add(rate)
            db.session.commit()
            rate_id = rate.id

        response = authenticated_client.post(
            f"/exchange_rate/delete/{rate_id}", follow_redirects=True
        )
        assert response.status_code == 200

        with app.app_context():
            rate = db.session.get(TipoCambio, rate_id)
            assert rate is None

    def test_exchange_rate_delete_nonexistent_redirects(self, authenticated_client):
        """Test that deleting a non-existent exchange rate redirects."""
        response = authenticated_client.post(
            "/exchange_rate/delete/NONEXISTENT", follow_redirects=True
        )
        assert response.status_code == 200
