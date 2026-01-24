#!/usr/bin/env python3
"""
Validación de ejemplos de cálculo de IR en Nicaragua.

Este script valida 4 ejemplos de cálculo de IR que han sido previamente
validados por un contador. Utiliza el método ejecutar_test_nomina_nicaragua
para ejecutar las nóminas y verificar que los cálculos coinciden exactamente.

Ejemplos validados:
- Ejemplo 1: Salario alto constante (C$ 87,898.32 mensual)
- Ejemplo 2: Salario bajo con ingreso ocasional en mes 3
- Ejemplo 3: Salario variable (aumento en mes 3)
- Ejemplo 4: Salario bajo, exento hasta mes 3, ingreso ocasional en mes 11
"""

from typing import Dict, Any

# Ejemplo 1: Salario alto constante
EJEMPLO_1 = {
    "employee": {
        "codigo": "EMP-EJ1",
        "nombre": "Ejemplo",
        "apellido": "Uno",
        "identificacion": "001-000000-0001A",
        "salario_base": 87898.32,
    },
    "fiscal_year_start": "2025-01-01",
    "months": [
        {
            "month": 1,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 2,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 3,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 4,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 5,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 6,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 7,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 8,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 9,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 10,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 11,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
        {
            "month": 12,
            "salario_ordinario": 87898.32,
            "salario_ocasional": 0.00,
            "expected_inss": 6152.88,
            "expected_ir": 18898.63,
        },
    ],
}

# Ejemplo 2: Salario bajo con ingreso ocasional en mes 3
EJEMPLO_2 = {
    "employee": {
        "codigo": "EMP-EJ2",
        "nombre": "Ejemplo",
        "apellido": "Dos",
        "identificacion": "001-000000-0002A",
        "salario_base": 10000.00,
    },
    "fiscal_year_start": "2025-01-01",
    "months": [
        {
            "month": 1,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 2,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 3,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 3000.00,
            "expected_inss": 910.00,
            "expected_ir": 563.50,
        },
        {
            "month": 4,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 5,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 6,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 7,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 8,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 9,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 10,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 11,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 12,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
    ],
}

# Ejemplo 3: Salario variable (aumento en mes 3)
EJEMPLO_3 = {
    "employee": {
        "codigo": "EMP-EJ3",
        "nombre": "Ejemplo",
        "apellido": "Tres",
        "identificacion": "001-000000-0003A",
        "salario_base": 10000.00,
    },
    "fiscal_year_start": "2025-01-01",
    "months": [
        {
            "month": 1,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 2,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 3,
            "salario_ordinario": 13000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 910.00,
            "expected_ir": 563.50,
        },
        {
            "month": 4,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 5,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 6,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 7,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 8,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 9,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 10,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 11,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
        {
            "month": 12,
            "salario_ordinario": 10000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 700.00,
            "expected_ir": 145.00,
        },
    ],
}

# Ejemplo 4: Salario bajo, exento hasta mes 3, ingreso ocasional en mes 11
EJEMPLO_4 = {
    "employee": {
        "codigo": "EMP-EJ4",
        "nombre": "Ejemplo",
        "apellido": "Cuatro",
        "identificacion": "001-000000-0004A",
        "salario_base": 8000.00,
    },
    "fiscal_year_start": "2025-01-01",
    "months": [
        {
            "month": 1,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 2,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 3,
            "salario_ordinario": 11000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 770.00,
            "expected_ir": 16.50,
        },
        {
            "month": 4,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 5,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 6,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 7,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 8,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 9,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 10,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
        {
            "month": 11,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 3000.00,
            "expected_inss": 770.00,
            "expected_ir": 0.00,
        },
        {
            "month": 12,
            "salario_ordinario": 8000.00,
            "salario_ocasional": 0.00,
            "expected_inss": 560.00,
            "expected_ir": 0.00,
        },
    ],
}


def ejecutar_validaciones(db_session, app, verbose: bool = True) -> Dict[str, Any]:
    """
    Ejecuta las 4 validaciones de ejemplos de IR en Nicaragua.

    Args:
        db_session: SQLAlchemy database session
        app: Flask application context
        verbose: Si True, muestra información detallada

    Returns:
        Diccionario con resultados de todas las validaciones
    """
    from coati_payroll.utils.locales.nicaragua import ejecutar_test_nomina_nicaragua

    resultados = {
        "ejemplo_1": None,
        "ejemplo_2": None,
        "ejemplo_3": None,
        "ejemplo_4": None,
        "todos_exitosos": True,
        "errores_totales": [],
    }

    ejemplos = [
        ("Ejemplo 1: Salario Alto Constante", "ejemplo_1", EJEMPLO_1),
        ("Ejemplo 2: Salario Bajo con Ingreso Ocasional", "ejemplo_2", EJEMPLO_2),
        ("Ejemplo 3: Salario Variable", "ejemplo_3", EJEMPLO_3),
        ("Ejemplo 4: Salario Bajo Exento con Ingreso Ocasional", "ejemplo_4", EJEMPLO_4),
    ]

    for nombre, clave, datos in ejemplos:
        if verbose:
            print(f"\n{'='*80}")
            print(f"VALIDANDO: {nombre}")
            print(f"{'='*80}")

        try:
            resultado = ejecutar_test_nomina_nicaragua(
                test_data=datos,
                db_session=db_session,
                app=app,
                verbose=verbose,
            )

            resultados[clave] = resultado

            if not resultado["success"]:
                resultados["todos_exitosos"] = False
                for error in resultado["errors"]:
                    resultados["errores_totales"].append(f"{nombre}: {error}")

        except Exception as e:
            resultados[clave] = {
                "success": False,
                "errors": [f"Excepción: {str(e)}"],
            }
            resultados["todos_exitosos"] = False
            resultados["errores_totales"].append(f"{nombre}: {str(e)}")

    # Resumen final
    if verbose:
        print(f"\n{'='*80}")
        print("RESUMEN DE VALIDACIONES")
        print(f"{'='*80}")

        for nombre, clave, _ in ejemplos:
            resultado = resultados[clave]
            if resultado:
                estado = "✅ PASÓ" if resultado["success"] else "❌ FALLÓ"
                print(f"{nombre}: {estado}")
                if not resultado["success"]:
                    for error in resultado.get("errors", []):
                        print(f"  - {error}")

        print(f"\n{'='*80}")
        if resultados["todos_exitosos"]:
            print("✅ TODAS LAS VALIDACIONES PASARON EXITOSAMENTE")
        else:
            print(f"❌ {len(resultados['errores_totales'])} ERROR(ES) ENCONTRADO(S)")
        print(f"{'='*80}\n")

    return resultados


if __name__ == "__main__":
    # Este script debe ejecutarse desde el contexto de la aplicación Flask
    # Ejemplo de uso:
    # from coati_payroll import create_app
    # from coati_payroll.model import db
    #
    # app = create_app()
    # with app.app_context():
    #     ejecutar_validaciones(db.session, app, verbose=True)

    print("Este script debe ejecutarse desde el contexto de la aplicación Flask.")
    print("Ver ejemplos de uso en los comentarios del código.")
