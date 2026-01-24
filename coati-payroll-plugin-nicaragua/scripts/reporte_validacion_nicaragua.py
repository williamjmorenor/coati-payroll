#!/usr/bin/env python3
"""
Reporte detallado de validación de ejemplos de IR en Nicaragua.

Este script ejecuta las validaciones y genera un reporte detallado mostrando
los valores calculados vs esperados para cada mes de cada ejemplo.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coati_payroll import create_app
from coati_payroll.model import db
from coati_payroll_plugin_nicaragua.validate_nicaragua_examples import (
    ejecutar_validaciones,
    EJEMPLO_1,
    EJEMPLO_2,
    EJEMPLO_3,
    EJEMPLO_4,
)
from coati_payroll_plugin_nicaragua.nicaragua import ejecutar_test_nomina_nicaragua


def generar_reporte_detallado(resultado, nombre_ejemplo, datos_ejemplo):
    """Genera un reporte detallado de los resultados."""
    print(f"\n{'='*80}")
    print(f"REPORTE DETALLADO: {nombre_ejemplo}")
    print(f"{'='*80}\n")
    
    if not resultado:
        print("❌ No se pudo ejecutar la validación")
        return
    
    if resultado["success"]:
        print("✅ VALIDACIÓN EXITOSA\n")
    else:
        print("❌ VALIDACIÓN FALLIDA\n")
        print("Errores encontrados:")
        for error in resultado.get("errors", []):
            print(f"  - {error}")
        print()
    
    # Mostrar resultados mes a mes
    print("Resultados Mes a Mes:")
    print("-" * 80)
    print(f"{'Mes':<6} {'Sal.Ord.':<12} {'Sal.Ocas.':<12} {'INSS Esp.':<12} {'INSS Calc.':<12} {'✓':<4} {'IR Esp.':<12} {'IR Calc.':<12} {'✓':<4}")
    print("-" * 80)
    
    for month_result in resultado.get("results", []):
        mes = month_result["month"]
        sal_ord = month_result["salario_ordinario"]
        sal_ocas = month_result["salario_ocasional"]
        inss_esp = month_result["expected_inss"]
        inss_calc = month_result["actual_inss"]
        inss_ok = "✓" if month_result["inss_match"] else "✗"
        ir_esp = month_result["expected_ir"]
        ir_calc = month_result["actual_ir"]
        ir_ok = "✓" if month_result["ir_match"] else "✗"
        
        print(f"{mes:<6} {sal_ord:>12,.2f} {sal_ocas:>12,.2f} {inss_esp:>12,.2f} {inss_calc:>12,.2f} {inss_ok:<4} {ir_esp:>12,.2f} {ir_calc:>12,.2f} {ir_ok:<4}")
    
    # Mostrar acumulados finales
    acumulado = resultado.get("accumulated")
    if acumulado:
        print("\n" + "-" * 80)
        print("Valores Acumulados Finales:")
        print(f"  Salario Bruto Acumulado: C$ {acumulado['salario_bruto_acumulado']:,.2f}")
        print(f"  INSS Acumulado: C$ {acumulado['deducciones_antes_impuesto_acumulado']:,.2f}")
        print(f"  IR Retenido Acumulado: C$ {acumulado['impuesto_retenido_acumulado']:,.2f}")
        print(f"  Períodos Procesados: {acumulado['periodos_procesados']}")
    
    # Calcular totales esperados
    total_inss_esperado = sum(m.get("expected_inss", 0) for m in datos_ejemplo["months"])
    total_ir_esperado = sum(m.get("expected_ir", 0) for m in datos_ejemplo["months"])
    
    print("\n" + "-" * 80)
    print("Totales Esperados vs Calculados:")
    if acumulado:
        print(f"  INSS Total Esperado: C$ {total_inss_esperado:,.2f}")
        print(f"  INSS Total Calculado: C$ {acumulado['deducciones_antes_impuesto_acumulado']:,.2f}")
        print(f"  IR Total Esperado: C$ {total_ir_esperado:,.2f}")
        print(f"  IR Total Calculado: C$ {acumulado['impuesto_retenido_acumulado']:,.2f}")
        
        diff_inss = abs(acumulado['deducciones_antes_impuesto_acumulado'] - total_inss_esperado)
        diff_ir = abs(acumulado['impuesto_retenido_acumulado'] - total_ir_esperado)
        print(f"\n  Diferencia INSS: C$ {diff_inss:,.2f}")
        print(f"  Diferencia IR: C$ {diff_ir:,.2f}")


def main():
    """Función principal."""
    import tempfile
    from cachelib.file import FileSystemCache
    
    session_dir = tempfile.mkdtemp()
    
    config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:?check_same_thread=False",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"check_same_thread": False}},
        "SECRET_KEY": "test-secret-key",
        "PRESERVE_CONTEXT_ON_EXCEPTION": False,
        "SESSION_TYPE": "cachelib",
        "SESSION_CACHELIB": FileSystemCache(cache_dir=session_dir, threshold=100),
    }
    
    app = create_app(config)
    
    with app.app_context():
        print("\n" + "="*80)
        print("REPORTE DE VALIDACIÓN DE EJEMPLOS DE IR EN NICARAGUA")
        print("="*80)
        
        ejemplos = [
            ("Ejemplo 1: Salario Alto Constante", EJEMPLO_1),
            ("Ejemplo 2: Salario Bajo con Ingreso Ocasional", EJEMPLO_2),
            ("Ejemplo 3: Salario Variable", EJEMPLO_3),
            ("Ejemplo 4: Salario Bajo Exento", EJEMPLO_4),
        ]
        
        resultados_totales = {}
        
        for nombre, datos in ejemplos:
            try:
                resultado = ejecutar_test_nomina_nicaragua(
                    test_data=datos,
                    db_session=db.session,
                    app=app,
                    verbose=False,
                )
                resultados_totales[nombre] = resultado
                generar_reporte_detallado(resultado, nombre, datos)
            except Exception as e:
                print(f"\n❌ Error ejecutando {nombre}: {str(e)}")
                resultados_totales[nombre] = {"success": False, "errors": [str(e)]}
        
        # Resumen final
        print("\n" + "="*80)
        print("RESUMEN FINAL")
        print("="*80)
        
        exitosos = sum(1 for r in resultados_totales.values() if r.get("success"))
        total = len(resultados_totales)
        
        for nombre, resultado in resultados_totales.items():
            estado = "✅ PASÓ" if resultado.get("success") else "❌ FALLÓ"
            print(f"{nombre}: {estado}")
            if not resultado.get("success"):
                for error in resultado.get("errors", []):
                    print(f"  - {error}")
        
        print(f"\nTotal: {exitosos}/{total} ejemplos pasaron")
        print("="*80 + "\n")
        
        return 0 if exitosos == total else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

