# Contrato Social del Proyecto

*Motor de Cálculo de Planillas Agnostico a la Juridicción*

## Propósito del proyecto

Este proyecto existe para proveer un motor genérico, predecible y extensible para el cálculo de planillas, agnóstico a la jurisdicción,
que permita a organizaciones e implementadores definir sus propias reglas de nómina sin necesidad de modificar el código fuente del motor.

**El proyecto no pretende:**

 - Imponer interpretaciones legales.
 - Sustituir conocimiento profesional.
 - Garantizar cumplimiento normativo.

**Qué promete el proyecto a sus usuarios**

El proyecto promete, *de buena fe*, que el motor:

 - Ejecutará cálculos de forma predecible y reproducible.
 - Permanecerá agnóstico a la jurisdicción.
 - No incorporará reglas legales hardcodeadas.
 - Mantendrá una separación estricta entre:
     * Motor de cálculo.
     * Configuración de reglas.
     * Orquestación de nómina.
 - Permitirá que cualquier cambio legal o de política se realice mediante configuración, no mediante cambios de código.
 - Proveerá trazabilidad técnica suficiente para auditar cálculos.

## Alcance funcional declarado

El proyecto declara explícitamente que el motor, por defecto, solo hace lo siguiente:

 - Calcula el salario base del empleado según el período definido en la planilla.
 - Aplica cuotas de anticipos salariales cuando estas existen, consumiéndolas desde un módulo externo.

Todo otro concepto de nómina:

 - Percepciones
 - Deducciones
 - Prestaciones
 - Impuestos
 - Topes
 - Tramos
 - Exenciones

Existe únicamente si el implementador lo define por configuración.

## Valores por defecto

El proyecto puede ofrecer valores por defecto sanos (por ejemplo, meses de 30 días) con el único objetivo de
facilitar la adopción inicial.

El proyecto declara que:

 - Los valores por defecto no representan reglas legales.
 - Son completamente configurables.
 - No deben asumirse como correctos para ninguna jurisdicción específica.

## Sobre la responsabilidad del implementador

El proyecto declara, de forma abierta y honesta, que el uso correcto del motor exige competencia técnica.

Se espera que el implementador:

 - Tenga un conocimiento razonable de cómo se calcula una nómina.
 - Comprenda el marco legal aplicable a la jurisdicción que configura.
 - Sea capaz de calcular manualmente una nómina completa para al menos un empleado.
 - Compare los resultados manuales con los resultados del sistema.
 - Identifique errores de configuración por su cuenta.

El proyecto no pretende proteger al implementador de errores derivados de una configuración incorrecta.

## Filosofía del proyecto respecto a errores

El proyecto distingue claramente entre:

 - Errores de configuración, que son responsabilidad del implementador.
 - Errores del motor, que son responsabilidad del proyecto.

Cuando un implementador identifique un posible error del motor se espera, bajo un principio de buena voluntad, que:

  - El error sea reportado.
  - Se provea un contexto apropiado para reproducir el error.

El proyecto puede revisar, analizar y validar el reporte.

Sin embargo:

 - No existe obligación de respuesta.
 - No existe compromiso de corrección.
 - No existe garantía de tiempos.

Las correcciones se realizan cuando es razonablemente posible y cuando se alinean con los objetivos del proyecto.

Es posible que al implementar el sistema en una juridicción especifica se encuentre que el motor de nomina tiene limitaciones
tecnicas que dificultan la implementación, estas limitaciones no se consideran un error pues cada juridicción o incluso entidad
tiene reglas distintas para los calculos asociados a una nomina. Estas limitaciones seran atendidas como un solicitud de una nueva
caracterista, sin embargo, no se implementaran cambios en el motor de nomina que rompan el contrato social de mantener un producto
completamente agnostico a la juridicción donde se implementa.

El sistema se compromete a brindar la base para implementar un sistema de nominas flexible con calculos basados en configuración no
programación.

## Licencia y libertad del software

El proyecto se distribuye bajo la Licencia Apache, Versión 2.0.

En coherencia con dicha licencia, el proyecto afirma que:

 - El software se entrega “tal como está” (AS IS).
 - No se ofrecen garantías de utilidad para un fin particular.
 - No se garantizan resultados correctos ni cumplimiento legal.

El proyecto valora y promueve:

 - El uso libre.
 - La modificación.
 - La redistribución.
 - La integración en otros sistemas.

Siempre respetando los términos de la licencia.

## Rol de BMO Soluciones, S.A.

BMO Soluciones, S.A.:

 - Publica y mantiene el proyecto bajo principios de software libre.
 - No asume responsabilidad por el uso del motor en producción.
 - No garantiza resultados correctos ni conformidad legal.
 - Actúa como steward del proyecto, no como proveedor de servicios.

## Compromiso con la honestidad técnica

Este proyecto se compromete a:

 - No ocultar limitaciones.
 - No presentar el motor como un sistema “listo para cumplir leyes”.
 - No prometer más de lo que el motor puede cumplir.
 - Mantener documentación clara sobre su alcance real.

## Declaración final.

Este proyecto existe para servir a implementadores competentes que necesitan un motor de cálculo de planillas flexible y honesto.
No pretende reemplazar el criterio profesional, conocimiento legal ni responsabilidad humana.
La libertad que ofrece el motor implica, necesariamente, responsabilidad por parte de quien lo usa.

