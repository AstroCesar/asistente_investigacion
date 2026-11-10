# Límites de autonomía del agente de investigación

Este documento describe el agente que tengo ahora en [agente_con_herramientas.py](../agente_con_herramientas.py). Tiene un glosario pequeño, una cuenta de minutos y dos herramientas para probar qué pasa cuando puede guardar o borrar una nota local. La memoria le permite seguir una conversación, pero no le da permiso para borrar por su cuenta.

## Herramientas y nivel de riesgo

- `consultar_glosario`: riesgo bajo. Lee definiciones que están escritas en el código. Puede no encontrar un término o dar una respuesta incompleta, pero no cambia ningún dato.
- `calcular_tiempo_observacion`: riesgo bajo. Multiplica la cantidad de tomas por los minutos de cada una. Una entrada equivocada daría una cuenta equivocada, pero la herramienta no controla el telescopio ni modifica nada.
- `guardar_nota_observacion`: riesgo medio. Agrega una nota a `notas_agente.json`. Si la nota está mal, todavía se puede corregir o borrar.
- `eliminar_nota_observacion`: riesgo alto. Borra definitivamente una nota de ese archivo. Si se equivoca de ID, se pierde el contenido guardado.

## Herramientas que requieren aprobación humana

`eliminar_nota_observacion` pide aprobación antes de borrar. En la consola muestra el título y el ID de la nota. Si respondo `n`, no respondo a tiempo o no hay consola interactiva, la nota queda guardada. La decisión y el momento se agregan a `registro_aprobaciones` durante esa ejecución.

No pido aprobación para leer el glosario, calcular o guardar una nota de prueba. Las primeras ocho trazas son de las pruebas con glosario y calculadora. Después corrí el ensayo con Gemini: guardó la nota `57886b3e`, intentó borrarla y respondí `n`. La nota siguió en el archivo. Así quedaron trazas de los tres niveles de riesgo, aunque en la de riesgo alto el borrado fue rechazado.

## Revisión de trazas

Las consultas de prueba se guardan en [trazas_agente.jsonl](../trazas_agente.jsonl). Cada línea tiene la pregunta, la sesión, la herramienta elegida, sus argumentos, lo que devolvió y la respuesta final. Para las notas revisaré además si el borrado fue aprobado o rechazado.

Por ahora revisaré las trazas después de cada cambio en el agente. Si más adelante hay muchas consultas, revisaré una muestra pequeña una vez por semana. Me fijaré sobre todo en llamadas repetidas a la misma herramienta con argumentos parecidos y en respuestas que afirmen algo que la herramienta no entregó.

Ya vimos por qué esto importa: en una prueba, el agente mandó `transito` sin tilde. El glosario no lo encontró y Gemini dio una definición por su cuenta. Ajusté la búsqueda para aceptar las dos formas. Al revisar la traza, quiero poder distinguir una respuesta respaldada por el glosario de una respuesta que el modelo completó solo.

## Qué hacer ante un comportamiento inesperado

1. Si una herramienta empieza a responder mal, la saco temporalmente de la lista `herramientas`.
2. Reviso la línea de la traza para ver la pregunta, los argumentos que recibió y lo que respondió. Comparo eso con la respuesta final.
3. Si eligió la herramienta equivocada, ajusto su descripción. Si la cuenta o la definición está mal, corrijo esa función. Si la respuesta agregó algo sin respaldo, reviso el prompt.
4. Repito la misma pregunta en una sesión nueva y miro la traza antes de volver a usar la herramienta.
