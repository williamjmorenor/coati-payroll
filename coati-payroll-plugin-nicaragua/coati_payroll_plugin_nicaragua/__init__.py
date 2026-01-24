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
"""
Plugin de Coati Payroll para Nicaragua.

Este plugin implementa las reglas de nómina específicas para Nicaragua,
incluyendo INSS (7%) e IR (Impuesto sobre la Renta) progresivo con método acumulado.

El plugin proporciona:
- Utilidades para cálculos de IR e INSS nicaragüenses
- Scripts de validación
- Documentación técnica específica de Nicaragua
- Tests de integración
"""

from flask import Blueprint, render_template

__version__ = "1.0.0"

# ============================================================================
# BLUEPRINT (OBLIGATORIO)
# ============================================================================

bp = Blueprint(
    "plugin_nicaragua",
    __name__,
    url_prefix="/nicaragua",
    template_folder="templates",
    static_folder="static"
)


@bp.route("/")
def index():
    """Página principal del plugin de Nicaragua."""
    return render_template("nicaragua/index.html")


@bp.route("/documentacion")
def documentacion():
    """Documentación específica de Nicaragua."""
    return render_template("nicaragua/documentacion.html")


def register_blueprints(app):
    """
    Función obligatoria que registra los blueprints del plugin.
    
    Args:
        app: Instancia de Flask
    """
    app.register_blueprint(bp)


# ============================================================================
# ENTRADA DE MENÚ (OBLIGATORIO)
# ============================================================================

def get_menu_entry():
    """
    Devuelve la entrada del menú para este plugin.
    
    Returns:
        dict: Diccionario con 'label', 'icon' y 'url'
    """
    return {
        "label": "Nicaragua",
        "icon": "bi bi-flag-fill",
        "url": "/nicaragua/",
    }


# ============================================================================
# COMANDO INIT (OBLIGATORIO)
# ============================================================================

def init():
    """
    Inicializa el plugin: carga catálogos base para Nicaragua.
    
    Esta función se ejecuta cuando el administrador ejecuta:
        payrollctl plugins nicaragua init
    
    Debe ser idempotente: ejecutarla varias veces no debe duplicar datos.
    
    Crea:
    - Deducciones: INSS (7%), IR (progresivo)
    - Tipos de planilla: Mensual Nicaragua
    - Reglas de cálculo: IR progresivo con método acumulado
    """
    from coati_payroll.model import (
        db,
        Deduccion,
        TipoPlanilla,
        ReglaCalculo,
    )
    from coati_payroll.log import log
    
    # Función auxiliar para upsert
    def _upsert_by_codigo(Model, codigo: str, **kwargs):
        existing = db.session.execute(
            db.select(Model).filter_by(codigo=codigo)
        ).scalar_one_or_none()
        
        if existing is None:
            existing = Model()
            existing.codigo = codigo
            db.session.add(existing)
        
        for k, v in kwargs.items():
            setattr(existing, k, v)
        
        return existing
    
    log.info("Inicializando plugin de Nicaragua...")
    
    # 1) Deducciones
    _upsert_by_codigo(
        Deduccion,
        "INSS",
        nombre="INSS",
        descripcion="Instituto Nicaragüense de Seguridad Social (7%)",
        formula_tipo="porcentaje",
        prioridad=1,
        activo=True,
    )
    
    _upsert_by_codigo(
        Deduccion,
        "IR",
        nombre="IR",
        descripcion="Impuesto sobre la Renta (progresivo con método acumulado)",
        formula_tipo="tabla_impuestos",
        prioridad=2,
        activo=True,
    )
    
    # 2) Tipos de planilla
    _upsert_by_codigo(
        TipoPlanilla,
        "MENSUAL_NI",
        nombre="Mensual (Nicaragua)",
        descripcion="Planilla mensual según legislación nicaragüense",
        activo=True,
    )
    
    # 3) Regla de cálculo para IR (ejemplo con esquema JSON básico)
    # Nota: El implementador debe configurar los valores exactos según la legislación vigente
    _upsert_by_codigo(
        ReglaCalculo,
        "IR_NICARAGUA",
        nombre="IR Nicaragua - Progresivo",
        descripcion="Cálculo de IR progresivo con método acumulado para Nicaragua",
        tipo_regla="deduccion",
        activo=True,
        # El esquema JSON completo debe ser configurado por el implementador
        # Este es solo un ejemplo de estructura
        esquema_json={
            "name": "IR Nicaragua",
            "description": "Cálculo de Impuesto sobre la Renta para Nicaragua",
            "steps": [
                {
                    "type": "comment",
                    "value": "Configurar según legislación nicaragüense vigente"
                }
            ]
        }
    )
    
    db.session.commit()
    log.info("Plugin de Nicaragua inicializado correctamente")


# ============================================================================
# COMANDO UPDATE (OBLIGATORIO)
# ============================================================================

def update():
    """
    Actualiza el plugin: aplica cambios de versión o actualizaciones de catálogo.
    
    Esta función se ejecuta cuando el administrador ejecuta:
        payrollctl plugins nicaragua update
    """
    from coati_payroll.model import db
    from coati_payroll.log import log
    
    log.info("Actualizando plugin de Nicaragua...")
    
    # Aquí se pueden aplicar actualizaciones incrementales
    # Por ejemplo, actualizar descripciones, agregar nuevos conceptos, etc.
    
    db.session.commit()
    log.info("Plugin de Nicaragua actualizado correctamente")
