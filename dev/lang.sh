# Actualizar archivo de traducción
# Extraer nuevos textos
pybabel extract -F babel.cfg -o coati_payroll/translations/messages.pot .

# Actualizar archivos de idioma
pybabel update -i coati_payroll/translations/messages.pot -d coati_payroll/translations

# Luego edita los .po y recompila
pybabel compile -d coati_payroll/translations