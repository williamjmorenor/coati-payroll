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
"""Initial data for currencies, income concepts, and deduction concepts.

This module provides default data to be loaded during system initialization.
All data is jurisdiction-agnostic and uses Flask-Babel for translation support.
Strings are marked for translation using _() and will be translated based on
the configured language in the database.
"""

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
from coati_payroll.i18n import _l as _


# American currencies (North, Central, South America, and Caribbean)
# Currency names are marked for translation
CURRENCIES = [
    # North America
    {"codigo": "USD", "nombre": _("US Dollar"), "simbolo": "$"},
    {"codigo": "CAD", "nombre": _("Canadian Dollar"), "simbolo": "C$"},
    {"codigo": "MXN", "nombre": _("Mexican Peso"), "simbolo": "$"},
    
    # Central America
    {"codigo": "BZD", "nombre": _("Belize Dollar"), "simbolo": "BZ$"},
    {"codigo": "CRC", "nombre": _("Costa Rican Colón"), "simbolo": "₡"},
    {"codigo": "GTQ", "nombre": _("Guatemalan Quetzal"), "simbolo": "Q"},
    {"codigo": "HNL", "nombre": _("Honduran Lempira"), "simbolo": "L"},
    {"codigo": "NIO", "nombre": _("Nicaraguan Córdoba"), "simbolo": "C$"},
    {"codigo": "PAB", "nombre": _("Panamanian Balboa"), "simbolo": "B/."},
    {"codigo": "SVC", "nombre": _("Salvadoran Colón"), "simbolo": "₡"},
    
    # South America
    {"codigo": "ARS", "nombre": _("Argentine Peso"), "simbolo": "$"},
    {"codigo": "BOB", "nombre": _("Bolivian Boliviano"), "simbolo": "Bs."},
    {"codigo": "BRL", "nombre": _("Brazilian Real"), "simbolo": "R$"},
    {"codigo": "CLP", "nombre": _("Chilean Peso"), "simbolo": "$"},
    {"codigo": "COP", "nombre": _("Colombian Peso"), "simbolo": "$"},
    {"codigo": "GYD", "nombre": _("Guyanese Dollar"), "simbolo": "G$"},
    {"codigo": "PEN", "nombre": _("Peruvian Sol"), "simbolo": "S/"},
    {"codigo": "PYG", "nombre": _("Paraguayan Guaraní"), "simbolo": "₲"},
    {"codigo": "SRD", "nombre": _("Surinamese Dollar"), "simbolo": "$"},
    {"codigo": "UYU", "nombre": _("Uruguayan Peso"), "simbolo": "$"},
    {"codigo": "VES", "nombre": _("Venezuelan Bolívar"), "simbolo": "Bs."},
    
    # Caribbean
    {"codigo": "ANG", "nombre": _("Netherlands Antillean Guilder"), "simbolo": "ƒ"},
    {"codigo": "AWG", "nombre": _("Aruban Florin"), "simbolo": "ƒ"},
    {"codigo": "BBD", "nombre": _("Barbadian Dollar"), "simbolo": "$"},
    {"codigo": "BSD", "nombre": _("Bahamian Dollar"), "simbolo": "$"},
    {"codigo": "CUP", "nombre": _("Cuban Peso"), "simbolo": "$"},
    {"codigo": "DOP", "nombre": _("Dominican Peso"), "simbolo": "$"},
    {"codigo": "HTG", "nombre": _("Haitian Gourde"), "simbolo": "G"},
    {"codigo": "JMD", "nombre": _("Jamaican Dollar"), "simbolo": "J$"},
    {"codigo": "TTD", "nombre": _("Trinidad and Tobago Dollar"), "simbolo": "TT$"},
    {"codigo": "XCD", "nombre": _("East Caribbean Dollar"), "simbolo": "EC$"},
]


# Income concepts (Percepciones / Ingresos)
# These add to employee salary
# All names and descriptions are marked for translation
INCOME_CONCEPTS = [
    {
        "codigo": "HORAS_EXTRAS",
        "nombre": _("Overtime"),
        "descripcion": _("Additional hours worked beyond regular schedule")
    },
    {
        "codigo": "COMISIONES",
        "nombre": _("Commissions"),
        "descripcion": _("Sales commissions and performance-based income")
    },
    {
        "codigo": "BONOS",
        "nombre": _("Bonuses"),
        "descripcion": _("Performance or achievement bonuses")
    },
    {
        "codigo": "INCENTIVOS_METAS",
        "nombre": _("Goal Incentives"),
        "descripcion": _("Incentives for meeting specific targets or goals")
    },
    {
        "codigo": "PROPINAS",
        "nombre": _("Reported Tips"),
        "descripcion": _("Tips and gratuities reported by employee")
    },
    {
        "codigo": "ASIG_TRANSPORTE",
        "nombre": _("Transportation Allowance"),
        "descripcion": _("Fixed transportation allowance")
    },
    {
        "codigo": "ASIG_ALIMENTACION",
        "nombre": _("Food Allowance"),
        "descripcion": _("Fixed food or meal allowance")
    },
    {
        "codigo": "ASIG_VIVIENDA",
        "nombre": _("Housing Allowance"),
        "descripcion": _("Fixed housing or rent allowance")
    },
    {
        "codigo": "ANTIGUEDAD",
        "nombre": _("Seniority Bonus"),
        "descripcion": _("Additional payment based on years of service")
    },
    {
        "codigo": "VACACIONES_PAGADAS",
        "nombre": _("Paid Vacation"),
        "descripcion": _("Payment for vacation time taken")
    },
    {
        "codigo": "FERIADOS_TRABAJADOS",
        "nombre": _("Holiday Work"),
        "descripcion": _("Additional payment for working on holidays")
    },
    {
        "codigo": "PERMISOS_REMUNERADOS",
        "nombre": _("Paid Leave"),
        "descripcion": _("Payment for authorized paid leave")
    },
    {
        "codigo": "LICENCIAS_REMUNERADAS",
        "nombre": _("Paid License"),
        "descripcion": _("Payment for extended paid license periods")
    },
    {
        "codigo": "PAGOS_RETROACTIVOS",
        "nombre": _("Retroactive Payments"),
        "descripcion": _("Back payments for salary adjustments")
    },
    {
        "codigo": "AGUINALDO",
        "nombre": _("13th Month Salary"),
        "descripcion": _("Annual bonus (13th month salary)")
    },
    {
        "codigo": "GRATIFICACIONES",
        "nombre": _("Gratuities"),
        "descripcion": _("Discretionary bonuses or gratuities")
    },
    {
        "codigo": "INDEMNIZACION_SALARIAL",
        "nombre": _("Severance Pay"),
        "descripcion": _("Severance or termination compensation")
    },
]


# Deduction concepts (Deducciones)
# These subtract from employee salary
# All names and descriptions are marked for translation
DEDUCTION_CONCEPTS = [
    {
        "codigo": "ADELANTO_SALARIO",
        "nombre": _("Salary Advance"),
        "descripcion": _("Deduction for salary advance repayment (automatic from Loans/Advances module)")
    },
    {
        "codigo": "PLAN_RETIRO_VOLUNTARIO",
        "nombre": _("Voluntary Retirement Plan"),
        "descripcion": _("Voluntary retirement savings contribution")
    },
    {
        "codigo": "MEMBRESIAS_SUSCRIPCIONES",
        "nombre": _("Memberships/Subscriptions"),
        "descripcion": _("Deduction for memberships or subscription services")
    },
    {
        "codigo": "COMEDOR",
        "nombre": _("Cafeteria"),
        "descripcion": _("Company cafeteria charges")
    },
    {
        "codigo": "PRESTAMOS_INTERNOS",
        "nombre": _("Internal Loans"),
        "descripcion": _("Internal loan repayment installments")
    },
    {
        "codigo": "CREDITOS_COOPERATIVA",
        "nombre": _("Credit Union Loans"),
        "descripcion": _("Credit union or cooperative loan payments")
    },
    {
        "codigo": "INTERESES_PRESTAMOS",
        "nombre": _("Loan Interest"),
        "descripcion": _("Interest charges on loans")
    },
    {
        "codigo": "PENSION_ALIMENTICIA",
        "nombre": _("Alimony"),
        "descripcion": _("Court-ordered alimony or child support payments")
    },
    {
        "codigo": "EMBARGOS_JUDICIALES",
        "nombre": _("Court Garnishments"),
        "descripcion": _("Court-ordered wage garnishments")
    },
    {
        "codigo": "DESC_AUSENCIAS",
        "nombre": _("Unpaid Absences"),
        "descripcion": _("Deductions for unpaid absences")
    },
    {
        "codigo": "DESC_TARDANZAS",
        "nombre": _("Tardiness"),
        "descripcion": _("Deductions for late arrivals")
    },
    {
        "codigo": "PENALIZACIONES_INCUMPLIMIENTO",
        "nombre": _("Non-compliance Penalties"),
        "descripcion": _("Penalties for policy or contract violations")
    },
    {
        "codigo": "DESC_PERDIDAS_DANOS",
        "nombre": _("Losses or Damages"),
        "descripcion": _("Deductions for lost or damaged property")
    },
    {
        "codigo": "PENALIZACION_UNIFORMES",
        "nombre": _("Uniform Penalties"),
        "descripcion": _("Penalties for unreturned uniforms or equipment")
    },
    {
        "codigo": "CONSUMOS_TIENDA_CANTINA",
        "nombre": _("Store/Canteen Purchases"),
        "descripcion": _("Purchases at company store or canteen")
    },
    {
        "codigo": "DONACIONES_VOLUNTARIAS",
        "nombre": _("Voluntary Donations"),
        "descripcion": _("Voluntary charitable donations")
    },
    {
        "codigo": "APORTACIONES_ASOCIACIONES",
        "nombre": _("Association Contributions"),
        "descripcion": _("Voluntary contributions to associations")
    },
    {
        "codigo": "CUOTA_SINDICAL",
        "nombre": _("Union Dues"),
        "descripcion": _("Voluntary union membership dues")
    },
    {
        "codigo": "CORRECCION_PAGOS_EXCESO",
        "nombre": _("Overpayment Correction"),
        "descripcion": _("Correction for previous overpayments")
    },
]


def load_currencies() -> None:
    """Load American currencies into the database.
    
    Currency names are translated based on the configured language in the database.
    This function is idempotent - it will not create duplicates on repeated calls.
    """
    from coati_payroll.model import Moneda, db
    from coati_payroll.log import log
    
    currencies_loaded = 0
    for currency_data in CURRENCIES:
        # Check if currency already exists
        existing = db.session.execute(
            db.select(Moneda).filter_by(codigo=currency_data["codigo"])
        ).scalar_one_or_none()
        
        if existing is None:
            # Create new currency - nombre will be translated by _()
            # Convert lazy string to regular string for database storage
            currency = Moneda()
            currency.codigo = currency_data["codigo"]
            currency.nombre = str(currency_data["nombre"])
            currency.simbolo = currency_data["simbolo"]
            currency.activo = True
            
            db.session.add(currency)
            currencies_loaded += 1
    
    if currencies_loaded > 0:
        db.session.commit()
        log.info(f"Loaded {currencies_loaded} currencies")
    else:
        log.trace("No new currencies to load")


def load_income_concepts() -> None:
    """Load income concepts (percepciones) into the database.
    
    Concept names and descriptions are translated based on the configured
    language in the database. This function is idempotent.
    """
    from coati_payroll.model import Percepcion, db
    from coati_payroll.log import log
    
    concepts_loaded = 0
    for concept_data in INCOME_CONCEPTS:
        # Check if concept already exists
        existing = db.session.execute(
            db.select(Percepcion).filter_by(codigo=concept_data["codigo"])
        ).scalar_one_or_none()
        
        if existing is None:
            # Create new income concept - strings will be translated by _()
            # Convert lazy strings to regular strings for database storage
            concept = Percepcion()
            concept.codigo = concept_data["codigo"]
            concept.nombre = str(concept_data["nombre"])
            concept.descripcion = str(concept_data["descripcion"])
            concept.formula_tipo = "fijo"
            concept.gravable = True
            concept.recurrente = False
            concept.activo = True
            concept.editable_en_nomina = True
            
            db.session.add(concept)
            concepts_loaded += 1
    
    if concepts_loaded > 0:
        db.session.commit()
        log.info(f"Loaded {concepts_loaded} income concepts")
    else:
        log.trace("No new income concepts to load")


def load_deduction_concepts() -> None:
    """Load deduction concepts (deducciones) into the database.
    
    Concept names and descriptions are translated based on the configured
    language in the database. This function is idempotent.
    """
    from coati_payroll.model import Deduccion, db
    from coati_payroll.log import log
    
    concepts_loaded = 0
    for concept_data in DEDUCTION_CONCEPTS:
        # Check if concept already exists
        existing = db.session.execute(
            db.select(Deduccion).filter_by(codigo=concept_data["codigo"])
        ).scalar_one_or_none()
        
        if existing is None:
            # Create new deduction concept - strings will be translated by _()
            # Convert lazy strings to regular strings for database storage
            concept = Deduccion()
            concept.codigo = concept_data["codigo"]
            concept.nombre = str(concept_data["nombre"])
            concept.descripcion = str(concept_data["descripcion"])
            concept.tipo = "general"
            concept.es_impuesto = False
            concept.formula_tipo = "fijo"
            concept.antes_impuesto = False
            concept.recurrente = False
            concept.activo = True
            concept.editable_en_nomina = True
            
            db.session.add(concept)
            concepts_loaded += 1
    
    if concepts_loaded > 0:
        db.session.commit()
        log.info(f"Loaded {concepts_loaded} deduction concepts")
    else:
        log.trace("No new deduction concepts to load")


def load_initial_data() -> None:
    """Load all initial data into the database.
    
    This function loads currencies, income concepts, and deduction concepts.
    All strings are translated based on the configured language in the database.
    This function is idempotent - safe to call multiple times.
    """
    from coati_payroll.log import log
    
    log.info("Loading initial data")
    
    load_currencies()
    load_income_concepts()
    load_deduction_concepts()
    
    log.info("Initial data loading completed")
