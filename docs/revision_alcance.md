# Revisión de la ficha

Revisor: un colega y yo (autorrevisión)
Fecha: 2026-11-27
Primera versión terminada: 2026-11-26

Primero revisé la ficha con la pauta del bloque y después la leí con un colega. Sus comentarios me ayudaron a ver qué partes podían prestarse a confusión. Revisé también que el problema tuviera una cifra marcada como estimación, que los requisitos importantes tuvieran una forma de probarse y que los cinco hitos cupieran en las 30 horas disponibles. Planifiqué 24 horas y dejé 6 para imprevistos.

- Hallazgo 1 (criterio 3): Al decir que reutilizaría Chroma, parecía que iba a usar el mismo índice con los diez textos del Gate 2. Eso mezclaría esos textos con el material que cargue el investigador.
  Decisión: aceptado. Aclaré en la ficha y el dibujo que reutilizo el código, pero comienzo con una colección y una carpeta de índice nuevas y vacías.

- Hallazgo 2 (criterio 4): La primera versión de CA-07 solo detenía y levantaba el contenedor. Esa prueba podía pasar aunque el índice no estuviera guardado en un volumen.
  Decisión: aceptado. Ahora la prueba pide reemplazar el contenedor y volver a consultar sin cargar otra vez la nota.

- Hallazgo 3 (criterios 1, 2 y 4): Al leerla con mi colega, vimos que la descripción de quién usaría la herramienta era demasiado específica, que cinco archivos eran pocos y que no quedaba bastante claro cómo distinguir una cita real de una inventada.
  Decisión: aceptado. Hablo de un investigador científico, permito agregar archivos en distintos momentos y pido comprobar cada dato en el archivo citado. También separé las tablas pequeñas en Markdown de los cálculos sobre tablas grandes, que dejo para después.

Además, aclaré cómo comprobar que un TXT vacío deja el índice intacto: CA-04 compara el contador de Chroma antes y después del rechazo. En CA-08 limité los valores de texto que pueden aparecer en los registros para que tampoco se guarden fragmentos de preguntas o documentos.

Acierto: ahora se distingue mejor lo que voy a construir en este prototipo de la aplicación más amplia que tengo en mente. Esta versión se concentra en TXT y Markdown, respuestas con fuentes, FastAPI y Docker. La carga directa de PDF, los cálculos sobre tablas grandes, otros proveedores y los modelos locales quedan para etapas posteriores.
