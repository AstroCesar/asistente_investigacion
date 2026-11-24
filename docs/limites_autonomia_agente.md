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

Las consultas de prueba se guardan en [trazas_agente.jsonl](../trazas_agente.jsonl). Para Gate 2 dejé las trazas sin texto libre: cada línea conserva la fecha, un identificador de sesión, la herramienta, los nombres de sus argumentos, las longitudes y, si hubo un intento de borrado, si fue aprobado. Las preguntas, los valores de los argumentos, las observaciones y las respuestas no quedan escritos en ese archivo. Guardé una copia local de las trazas anteriores antes de convertirlas.

Por ahora revisaré las trazas después de cada cambio en el agente. Si más adelante hay muchas consultas, revisaré una muestra pequeña una vez por semana. Me fijaré sobre todo en herramientas repetidas y en decisiones de borrado. Para revisar el contenido de una respuesta tendré que reproducir la consulta en local, porque la traza ya no guarda ese texto.

Ya vimos por qué esto importa: en una prueba, el agente mandó `transito` sin tilde. El glosario no lo encontró y Gemini dio una definición por su cuenta. Ajusté la búsqueda para aceptar las dos formas. Si vuelve a pasar, compararé la salida del glosario y la respuesta durante una prueba local, sin copiar esos textos al registro.

## Qué hacer ante un comportamiento inesperado

1. Si una herramienta empieza a responder mal, la saco temporalmente de la lista `herramientas`.
2. Reviso la traza para identificar la sesión, la herramienta y si hubo aprobación. Después reproduzco la consulta en una prueba local para comparar argumentos, observación y respuesta.
3. Si eligió la herramienta equivocada, ajusto su descripción. Si la cuenta o la definición está mal, corrijo esa función. Si la respuesta agregó algo sin respaldo, reviso el prompt.
4. Repito la misma pregunta en una sesión nueva y miro la traza antes de volver a usar la herramienta.
