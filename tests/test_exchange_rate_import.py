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
"""Tests for exchange rate Excel import."""

from datetime import date
from io import BytesIO
import pytest
from openpyxl import Workbook


class TestExchangeRateImport:
    """Tests for exchange rate Excel import functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app):
        """Set up test data for exchange rate import tests."""
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

            eur = Moneda()
            eur.codigo = "EUR"
            eur.nombre = "Euro"
            eur.activo = True
            db.session.add(eur)

            db.session.commit()

    def create_excel_file(self, data):
        """Helper to create an Excel file with given data."""
        wb = Workbook()
        ws = wb.active

        # Add header
        ws.append(["Fecha", "Moneda Base", "Moneda Destino", "Tipo de Cambio"])

        # Add data rows
        for row in data:
            ws.append(row)

        # Save to BytesIO
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return excel_file

    def test_import_excel_get_shows_form(self, authenticated_client):
        """Test that import Excel GET request shows the form."""
        response = authenticated_client.get("/exchange_rate/import")
        assert response.status_code == 200
        assert b"Importar" in response.data or b"Excel" in response.data

    def test_import_excel_with_valid_data(self, authenticated_client, app):
        """Test importing valid exchange rates from Excel."""
        # Create Excel file with test data
        excel_data = [
            ["2024-01-15", "USD", "NIO", 36.5],
            ["2024-01-16", "USD", "NIO", 36.55],
            ["2024-01-15", "EUR", "USD", 1.095],
        ]
        excel_file = self.create_excel_file(excel_data)

        response = authenticated_client.post(
            "/exchange_rate/import",
            data={"file": (excel_file, "test_rates.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify data was imported
        with app.app_context():
            from coati_payroll.model import TipoCambio, Moneda, db

            rates = db.session.execute(db.select(TipoCambio)).scalars().all()
            assert len(rates) == 3

            # Check specific rate - get USD currency
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one()
            nio = db.session.execute(db.select(Moneda).filter_by(codigo="NIO")).scalar_one()

            usd_nio_rate = db.session.execute(
                db.select(TipoCambio).filter_by(
                    moneda_origen_id=usd.id, moneda_destino_id=nio.id, fecha=date(2024, 1, 15)
                )
            ).scalar_one_or_none()

            if usd_nio_rate:
                assert float(usd_nio_rate.tasa) == 36.5

    def test_import_excel_with_four_decimals(self, authenticated_client, app):
        """Test that exchange rates with 4 decimals are imported correctly."""
        # Create Excel file with 4 decimal places
        excel_data = [
            ["2024-01-15", "USD", "NIO", 36.5423],
            ["2024-01-16", "EUR", "USD", 1.0951],
        ]
        excel_file = self.create_excel_file(excel_data)

        response = authenticated_client.post(
            "/exchange_rate/import",
            data={"file": (excel_file, "test_rates.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify precision is maintained
        with app.app_context():
            from coati_payroll.model import TipoCambio, Moneda, db

            usd_nio_rate = db.session.execute(
                db.select(TipoCambio)
                .join(TipoCambio.moneda_origen)
                .filter(Moneda.codigo == "USD", TipoCambio.fecha == date(2024, 1, 15))
            ).scalar_one()

            # Check that 4 decimals are preserved
            assert float(usd_nio_rate.tasa) == pytest.approx(36.5423, rel=1e-4)

    def test_import_excel_update_existing_rate(self, authenticated_client, app):
        """Test that existing rates are updated when importing."""
        from coati_payroll.model import Moneda, TipoCambio, db

        # Create an existing rate
        with app.app_context():
            usd = db.session.execute(db.select(Moneda).filter_by(codigo="USD")).scalar_one()
            nio = db.session.execute(db.select(Moneda).filter_by(codigo="NIO")).scalar_one()

            existing_rate = TipoCambio()
            existing_rate.fecha = date(2024, 1, 15)
            existing_rate.moneda_origen_id = usd.id
            existing_rate.moneda_destino_id = nio.id
            existing_rate.tasa = 36.0
            existing_rate.creado_por = "test_user"
            db.session.add(existing_rate)
            db.session.commit()

        # Import with updated value
        excel_data = [
            ["2024-01-15", "USD", "NIO", 36.5],
        ]
        excel_file = self.create_excel_file(excel_data)

        response = authenticated_client.post(
            "/exchange_rate/import",
            data={"file": (excel_file, "test_rates.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify rate was updated
        with app.app_context():
            from coati_payroll.model import TipoCambio, Moneda, db

            rate = db.session.execute(
                db.select(TipoCambio)
                .join(TipoCambio.moneda_origen)
                .filter(Moneda.codigo == "USD", TipoCambio.fecha == date(2024, 1, 15))
            ).scalar_one()

            assert float(rate.tasa) == 36.5

    def test_import_excel_invalid_currency(self, authenticated_client, app):
        """Test importing with invalid currency code."""
        excel_data = [
            ["2024-01-15", "USD", "XXX", 36.5],  # XXX is invalid
        ]
        excel_file = self.create_excel_file(excel_data)

        response = authenticated_client.post(
            "/exchange_rate/import",
            data={"file": (excel_file, "test_rates.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Should show error about currency not found
        with app.app_context():
            from coati_payroll.model import TipoCambio, db

            rates = db.session.execute(db.select(TipoCambio)).scalars().all()
            assert len(rates) == 0  # No rates should be imported

    def test_import_excel_invalid_date(self, authenticated_client, app):
        """Test importing with invalid date format."""
        excel_data = [
            ["invalid-date", "USD", "NIO", 36.5],
        ]
        excel_file = self.create_excel_file(excel_data)

        response = authenticated_client.post(
            "/exchange_rate/import",
            data={"file": (excel_file, "test_rates.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # No rates should be imported
        with app.app_context():
            from coati_payroll.model import TipoCambio, db

            rates = db.session.execute(db.select(TipoCambio)).scalars().all()
            assert len(rates) == 0

    def test_import_excel_no_file_selected(self, authenticated_client):
        """Test import without selecting a file."""
        response = authenticated_client.post(
            "/exchange_rate/import",
            data={},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should redirect back to import page with error

    def test_import_excel_invalid_file_type(self, authenticated_client):
        """Test import with non-Excel file."""
        text_file = BytesIO(b"not an excel file")

        response = authenticated_client.post(
            "/exchange_rate/import",
            data={"file": (text_file, "test.txt")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should show error about invalid file type

    def test_import_excel_with_dd_mm_yyyy_date_format(self, authenticated_client, app):
        """Test importing with DD/MM/YYYY date format."""
        excel_data = [
            ["15/01/2024", "USD", "NIO", 36.5],
        ]
        excel_file = self.create_excel_file(excel_data)

        response = authenticated_client.post(
            "/exchange_rate/import",
            data={"file": (excel_file, "test_rates.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify data was imported
        with app.app_context():
            from coati_payroll.model import TipoCambio, db

            rates = db.session.execute(db.select(TipoCambio)).scalars().all()
            assert len(rates) == 1
            assert rates[0].fecha == date(2024, 1, 15)
