#!/usr/bin/env python3
"""
Script ejecutable para validar los ejemplos de cálculo de IR en Nicaragua.

Este script puede ejecutarse directamente desde la línea de comandos para
validar que el sistema calcula correctamente el IR según los 4 ejemplos
proporcionados que han sido previamente validados por un contador.

Uso:
    python scripts/validar_ejemplos_nicaragua.py
    
O desde el directorio raíz del proyecto:
    python -m scripts.validar_ejemplos_nicaragua
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coati_payroll import create_app
from coati_payroll.model import db
from coati_payroll_plugin_nicaragua.validate_nicaragua_examples import ejecutar_validaciones


def main():
    """Función principal para ejecutar las validaciones."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("VALIDACIÓN DE EJEMPLOS DE CÁLCULO DE IR EN NICARAGUA")
        print("="*80)
        print("\nEste script valida 4 ejemplos de cálculo de IR que han sido")
        print("previamente validados por un contador.\n")
        
        resultados = ejecutar_validaciones(
            db_session=db.session,
            app=app,
            verbose=True,
        )
        
        # Retornar código de salida apropiado
        if resultados["todos_exitosos"]:
            print("\n✅ TODAS LAS VALIDACIONES PASARON EXITOSAMENTE")
            return 0
        else:
            print(f"\n❌ {len(resultados['errores_totales'])} ERROR(ES) ENCONTRADO(S)")
            for error in resultados["errores_totales"]:
                print(f"  - {error}")
            return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

