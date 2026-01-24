"""
Tests para validar los ejemplos de cálculo de IR en Nicaragua.

Estos tests utilizan el método ejecutar_test_nomina_nicaragua para validar
que el sistema calcula correctamente el IR según los 4 ejemplos proporcionados
que han sido previamente validados por un contador.
"""

import pytest
from decimal import Decimal

from coati_payroll_plugin_nicaragua.validate_nicaragua_examples import (
    ejecutar_validaciones,
    EJEMPLO_1,
    EJEMPLO_2,
    EJEMPLO_3,
    EJEMPLO_4,
)
from coati_payroll_plugin_nicaragua.nicaragua import ejecutar_test_nomina_nicaragua


class TestEjemplosNicaraguaIR:
    """Tests para validar los ejemplos de cálculo de IR en Nicaragua."""

    @pytest.mark.validation
    def test_ejemplo_1_salario_alto_constante(self, db_session, app):
        """Valida Ejemplo 1: Salario alto constante (C$ 87,898.32 mensual)."""
        resultado = ejecutar_test_nomina_nicaragua(
            test_data=EJEMPLO_1,
            db_session=db_session,
            app=app,
            verbose=False,
        )

        assert resultado["success"], f"Ejemplo 1 falló: {resultado['errors']}"

        # Validar que todos los meses tienen el IR esperado
        for month_result in resultado["results"]:
            assert month_result["ir_match"], (
                f"Mes {month_result['month']}: IR esperado {month_result['expected_ir']}, "
                f"actual {month_result['actual_ir']}"
            )
            assert month_result["inss_match"], (
                f"Mes {month_result['month']}: INSS esperado {month_result['expected_inss']}, "
                f"actual {month_result['actual_inss']}"
            )

        # Validar totales acumulados
        acumulado = resultado["accumulated"]
        assert acumulado is not None, "No se encontraron valores acumulados"

        # IR total esperado: 226,783.58 (18,898.63 × 12)
        ir_total_esperado = Decimal("226783.58")
        ir_total_actual = Decimal(str(acumulado["impuesto_retenido_acumulado"]))
        diferencia = abs(ir_total_actual - ir_total_esperado)
        assert diferencia < Decimal("1.00"), (
            f"IR total acumulado no coincide: esperado {ir_total_esperado}, "
            f"actual {ir_total_actual}, diferencia {diferencia}"
        )

    @pytest.mark.validation
    def test_ejemplo_2_salario_bajo_con_ingreso_ocasional(self, db_session, app):
        """Valida Ejemplo 2: Salario bajo con ingreso ocasional en mes 3."""
        resultado = ejecutar_test_nomina_nicaragua(
            test_data=EJEMPLO_2,
            db_session=db_session,
            app=app,
            verbose=False,
        )

        assert resultado["success"], f"Ejemplo 2 falló: {resultado['errors']}"

        # Validar que todos los meses tienen el IR esperado
        for month_result in resultado["results"]:
            assert month_result["ir_match"], (
                f"Mes {month_result['month']}: IR esperado {month_result['expected_ir']}, "
                f"actual {month_result['actual_ir']}"
            )
            assert month_result["inss_match"], (
                f"Mes {month_result['month']}: INSS esperado {month_result['expected_inss']}, "
                f"actual {month_result['actual_inss']}"
            )

        # Validar totales acumulados
        acumulado = resultado["accumulated"]
        assert acumulado is not None, "No se encontraron valores acumulados"

        # IR total esperado: 2,158.50 (145.00 × 2 + 563.50 + 145.00 × 9)
        ir_total_esperado = Decimal("2158.50")
        ir_total_actual = Decimal(str(acumulado["impuesto_retenido_acumulado"]))
        diferencia = abs(ir_total_actual - ir_total_esperado)
        assert diferencia < Decimal("1.00"), (
            f"IR total acumulado no coincide: esperado {ir_total_esperado}, "
            f"actual {ir_total_actual}, diferencia {diferencia}"
        )

    @pytest.mark.validation
    def test_ejemplo_3_salario_variable(self, db_session, app):
        """Valida Ejemplo 3: Salario variable (aumento en mes 3)."""
        resultado = ejecutar_test_nomina_nicaragua(
            test_data=EJEMPLO_3,
            db_session=db_session,
            app=app,
            verbose=False,
        )

        assert resultado["success"], f"Ejemplo 3 falló: {resultado['errors']}"

        # Validar que todos los meses tienen el IR esperado
        for month_result in resultado["results"]:
            assert month_result["ir_match"], (
                f"Mes {month_result['month']}: IR esperado {month_result['expected_ir']}, "
                f"actual {month_result['actual_ir']}"
            )
            assert month_result["inss_match"], (
                f"Mes {month_result['month']}: INSS esperado {month_result['expected_inss']}, "
                f"actual {month_result['actual_inss']}"
            )

        # Validar totales acumulados
        acumulado = resultado["accumulated"]
        assert acumulado is not None, "No se encontraron valores acumulados"

        # IR total esperado: 2,158.50
        ir_total_esperado = Decimal("2158.50")
        ir_total_actual = Decimal(str(acumulado["impuesto_retenido_acumulado"]))
        diferencia = abs(ir_total_actual - ir_total_esperado)
        assert diferencia < Decimal("1.00"), (
            f"IR total acumulado no coincide: esperado {ir_total_esperado}, "
            f"actual {ir_total_actual}, diferencia {diferencia}"
        )

    @pytest.mark.validation
    def test_ejemplo_4_salario_bajo_exento(self, db_session, app):
        """Valida Ejemplo 4: Salario bajo, exento hasta mes 3, ingreso ocasional en mes 11."""
        resultado = ejecutar_test_nomina_nicaragua(
            test_data=EJEMPLO_4,
            db_session=db_session,
            app=app,
            verbose=False,
        )

        assert resultado["success"], f"Ejemplo 4 falló: {resultado['errors']}"

        # Validar que todos los meses tienen el IR esperado
        for month_result in resultado["results"]:
            assert month_result["ir_match"], (
                f"Mes {month_result['month']}: IR esperado {month_result['expected_ir']}, "
                f"actual {month_result['actual_ir']}"
            )
            assert month_result["inss_match"], (
                f"Mes {month_result['month']}: INSS esperado {month_result['expected_inss']}, "
                f"actual {month_result['actual_inss']}"
            )

        # Validar totales acumulados
        acumulado = resultado["accumulated"]
        assert acumulado is not None, "No se encontraron valores acumulados"

        # IR total esperado: 16.50
        ir_total_esperado = Decimal("16.50")
        ir_total_actual = Decimal(str(acumulado["impuesto_retenido_acumulado"]))
        diferencia = abs(ir_total_actual - ir_total_esperado)
        assert diferencia < Decimal("1.00"), (
            f"IR total acumulado no coincide: esperado {ir_total_esperado}, "
            f"actual {ir_total_actual}, diferencia {diferencia}"
        )

    @pytest.mark.validation
    def test_todos_los_ejemplos(self, db_session, app):
        """
        Ejecuta todas las validaciones y verifica que todas pasen.

        NOTA: Este test ejecuta los 4 ejemplos en secuencia dentro de la misma
        sesión de base de datos. Cada ejemplo individual ya está validado por
        separado en los otros tests. Este test verifica que la función
        ejecutar_validaciones funciona correctamente.
        """
        resultados = ejecutar_validaciones(
            db_session=db_session,
            app=app,
            verbose=False,
        )

        assert resultados["todos_exitosos"], f"Algunos ejemplos fallaron: {resultados['errores_totales']}"
