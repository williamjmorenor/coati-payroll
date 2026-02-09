black coati_payroll
ruff check coati_payroll
flake8 coati_payroll
pylint coati_payroll -j 0
mypy coati_payroll
pytest -n auto tests/
pytest -m validation -n auto tests/
