# Límites de la métrica de evaluación

## Qué mide

Comparo las palabras de la respuesta con una frase que escribí como referencia. Antes paso todo a minúsculas y quito la puntuación. La precisión, la cobertura y el F1 cuentan las palabras que coinciden, incluso si se repiten. Esto me dice cuánto se parecen los textos, pero no si la explicación de astronomía está bien.

## Modos de falla conocidos

En paralaje salió **0,32**. La respuesta explica bien la idea, pero es mucho más larga que mi referencia y por eso comparte menos palabras de las que esperaba.

En supernova salió **0,36**. La respuesta usa «luminosa» donde la referencia dice «brillante», y el programa no entiende que se parecen. Al leerla encontré otra cosa: habla de estrellas masivas como si todas las supernovas fueran así, pero también existen las de tipo Ia.

En galaxias salió **0,63**. La idea principal está bien, pero dice que las galaxias tienen miles de millones de estrellas. Eso no sirve para todas, porque algunas galaxias enanas tienen menos. En rotación salió **0,48** y apareció «24 horas». Es una aproximación útil para el día solar, pero una vuelta respecto de las estrellas dura un poco menos.

## Muestra revisada

El **3 de noviembre de 2026** revisé **10 de las 20 respuestas** de [resultados_metricas.json](../resultados_metricas.json). Elegí las 5 con F1 más bajo y las 5 con F1 más alto. En [revision_manual.json](../revision_manual.json) dejé una nota para cada una, mirando si era correcta, si estaba completa y si se contradecía. En los puntajes altos de esta muestra no encontré una respuesta equivocada. Tampoco salió un caso donde una negación cambiara el sentido, así que eso queda sin probar.

Entre las cinco con F1 bajo estaba paralaje (**0,32**). Gemini habló del «cambio de posición» de una estrella y explicó para qué sirve, pero con una respuesta mucho más larga que mi referencia. En supernova (**0,36**) dijo que una estrella masiva muere en una explosión. Eso describe un tipo de supernova, pero deja fuera otros. En agujero negro (**0,40**) acertó al decir que ni la luz puede escapar. Su F1 bajó por lo extensa que fue la explicación. En rotación de la Tierra (**0,48**) relacionó el giro con el día y la noche, pero presentó las 24 horas como duración de una vuelta. En planeta (**0,49**) agregó la forma casi esférica y «limpiar» la órbita, sin aclarar que ese criterio formal corresponde a los planetas del Sistema Solar.

Entre las cinco con F1 alto estaba galaxia (**0,63**). Gemini mencionó estrellas, gas, polvo y gravedad, como en la referencia, pero dijo «miles de millones de estrellas» como si fuera así para todas las galaxias. En año luz (**0,72**) explicó que es una distancia y agregó unos 9,46 billones de kilómetros, un dato aproximado correcto. En Luna (**0,95**) dijo «único satélite natural de la Tierra». La palabra «único» no cambia la respuesta. En las dos preguntas más directas, planeta más grande (**1,00**) y planeta más cercano al Sol (**1,00**), respondió Júpiter y Mercurio. Ahí el puntaje perfecto sí coincidió con lo que vi al leerlas.

## Recomendación de uso

Uso el F1 para ordenar las respuestas de astronomía y ver cuáles necesito leer primero. Si Gemini agrega una cifra o afirma algo más amplio que mi referencia, reviso ese dato a mano. Eso pasó con la rotación de la Tierra y con las galaxias. También miro algunas respuestas con F1 alto, porque el número solo no me asegura que todo esté bien.
