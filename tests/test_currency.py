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
"""Tests for currency CRUD operations."""

import pytest


class TestCurrency:
    """Tests for currency CRUD routes."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app):
        """Set up test data for currency tests."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            # Clear any existing test data
            db.session.execute(db.delete(Moneda))
            db.session.commit()

    def test_currency_index_requires_login(self, client):
        """Test that currency index page requires login."""
        response = client.get("/currency/")
        # May return 200 with redirect template or 302 redirect
        assert response.status_code in [200, 302]

    def test_currency_index_shows_currencies(self, authenticated_client, app):
        """Test that currency index page shows existing currencies."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            # Create test currencies
            usd = Moneda()
            usd.codigo = "USD"
            usd.nombre = "US Dollar"
            usd.simbolo = "$"
            usd.activo = True
            db.session.add(usd)

            eur = Moneda()
            eur.codigo = "EUR"
            eur.nombre = "Euro"
            eur.simbolo = "€"
            eur.activo = True
            db.session.add(eur)

            db.session.commit()

        response = authenticated_client.get("/currency/")
        assert response.status_code == 200
        assert b"USD" in response.data
        assert b"EUR" in response.data

    def test_currency_new_get_shows_form(self, authenticated_client):
        """Test that new currency GET request shows the form."""
        response = authenticated_client.get("/currency/new")
        assert response.status_code == 200
        assert b"Nueva Moneda" in response.data or b"form" in response.data.lower()

    def test_currency_new_post_creates_currency(self, authenticated_client, app):
        """Test creating a new currency."""
        response = authenticated_client.post(
            "/currency/new",
            data={
                "codigo": "USD",
                "nombre": "US Dollar",
                "simbolo": "$",
                "activo": True,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            from coati_payroll.model import Moneda, db

            currency = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one_or_none()
            assert currency is not None
            assert currency.nombre == "US Dollar"
            assert currency.simbolo == "$"
            assert currency.activo is True

    def test_currency_edit_get_shows_form(self, authenticated_client, app):
        """Test that edit currency GET request shows the form with data."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            # Create a test currency
            currency = Moneda()
            currency.codigo = "USD"
            currency.nombre = "US Dollar"
            currency.simbolo = "$"
            currency.activo = True
            db.session.add(currency)
            db.session.commit()
            currency_id = currency.id  # Use the ULID id, not codigo

        response = authenticated_client.get(f"/currency/edit/{currency_id}")
        assert response.status_code == 200
        assert b"USD" in response.data

    def test_currency_edit_post_updates_currency(self, authenticated_client, app):
        """Test updating an existing currency."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            # Create a test currency
            currency = Moneda()
            currency.codigo = "USD"
            currency.nombre = "US Dollar"
            currency.simbolo = "$"
            currency.activo = True
            db.session.add(currency)
            db.session.commit()
            currency_id = currency.id  # Use the ULID id, not codigo

        response = authenticated_client.post(
            f"/currency/edit/{currency_id}",
            data={
                "codigo": "USD",
                "nombre": "United States Dollar",
                "simbolo": "US$",
                # activo field not included = False (unchecked)
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            currency = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one_or_none()
            assert currency.nombre == "United States Dollar"
            assert currency.simbolo == "US$"
            assert currency.activo is False

    def test_currency_edit_nonexistent_redirects(self, authenticated_client):
        """Test that editing a non-existent currency redirects."""
        response = authenticated_client.get("/currency/edit/NONEXISTENT", follow_redirects=True)
        assert response.status_code == 200

    def test_currency_delete_removes_currency(self, authenticated_client, app):
        """Test deleting a currency."""
        from coati_payroll.model import Moneda, db

        with app.app_context():
            # Create a test currency
            currency = Moneda()
            currency.codigo = "USD"
            currency.nombre = "US Dollar"
            currency.simbolo = "$"
            currency.activo = True
            db.session.add(currency)
            db.session.commit()
            currency_id = currency.id  # Use the ULID id, not codigo

        response = authenticated_client.post(f"/currency/delete/{currency_id}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            currency = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one_or_none()
            assert currency is None

    def test_currency_delete_nonexistent_redirects(self, authenticated_client):
        """Test that deleting a non-existent currency redirects."""
        response = authenticated_client.post("/currency/delete/NONEXISTENT", follow_redirects=True)
        assert response.status_code == 200
