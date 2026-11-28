# Ficha de Diseño Funcional

## 1. Problema de negocio

Un investigador científico reúne artículos, notas y a veces tablas para trabajar en un tema. Cuando necesita comprobar un dato, abre varios archivos, busca el pasaje y revisa de dónde salió. Si dedica unos diez minutos a cada consulta, diez preguntas le llevarían cerca de 100 minutos. Es una cuenta para planificar este prototipo; todavía no la medí con investigadores. Quiero que pueda consultar su material y recibir una respuesta en menos de dos minutos con una cita que se pueda comprobar en los archivos que cargó. Si esos archivos no respaldan la respuesta, prefiero que el sistema lo diga antes que inventar un dato o una fuente.

## 2. Requerimientos y alcance (MVP)

### Requerimientos funcionales

- RF-01: La persona carga archivos TXT o Markdown con artículos, notas o tablas pequeñas, de a uno y en distintos momentos; el sistema añade el contenido al índice del proyecto sin borrar lo anterior y conserva el nombre de cada archivo como fuente.
- RF-02: La persona hace una pregunta sobre esos archivos y recibe una respuesta que cita un archivo cargado donde realmente aparece el dato. Si los fragmentos recuperados no sostienen la respuesta, el sistema lo dice sin inventar datos ni fuentes.
- RF-03: FastAPI expone la carga de archivos y la consulta mediante `POST /documentos` y `POST /consultas`, con respuestas JSON que incluyen las fuentes.
- RF-04: Docker levanta el servicio y conserva el índice de Chroma en un volumen entre reinicios.
- RF-05: La persona puede cargar directamente archivos PDF con texto seleccionable y las citas incluyen el número de página cuando se puede extraer.
- RF-06: La persona carga una tabla grande de mediciones en un formato estructurado y consulta sus filas con filtros y cálculos que respetan unidades y datos faltantes; más adelante puede combinarla con los artículos del mismo proyecto.
- RF-07: La persona puede elegir entre varias API de modelos y configurar su propia clave para cada proveedor.
- RF-08: La persona puede usar modelos y embeddings totalmente locales, sin enviar documentos a una API externa.
- RF-09: El sistema entrena o ajusta un modelo con ejemplos etiquetados para una tarea repetida.
- RF-10: Una interfaz web ofrece cuentas separadas para varios investigadores.

### Requerimientos no funcionales

- RNF-01: Después de cargar las dos notas de prueba y ejecutar las 10 preguntas del conjunto de evaluación, los registros guardan solo eventos, identificadores, marcas de tiempo, longitudes, conteos, tiempos y consumo. No guardan texto de preguntas ni fragmentos de los archivos, nombres de archivos o claves, aunque sea de forma parcial.
- RNF-02: En un conjunto de 10 preguntas preparado con los archivos de prueba, 8 tendrán respuesta en el material y deberán citar el archivo correcto sin contradecir el pasaje; las otras 2 estarán fuera del material y deberán decir que no hay información suficiente. La revisión se hace contra los archivos originales.
- RNF-03: Una persona puede levantar el servicio desde una carpeta limpia siguiendo el README y un solo comando de Docker en menos de 15 minutos, con una clave válida y los archivos de prueba disponibles.
- RNF-04: En 10 consultas reales al corpus de prueba, al menos 9 devuelven el JSON de respuesta en menos de 120 segundos, medidos desde que se envía la pregunta hasta que llega la respuesta.

### Alcance

Imprescindible: RF-01, RF-02, RF-03, RF-04

Deseable: RF-05

Fuera de alcance: RF-06 (filtrar y calcular sobre tablas grandes necesita una consulta de datos propia), RF-07 (cada proveedor exige integración y pruebas), RF-08 (requiere modelos y embeddings locales con otro índice), RF-09 (faltan ejemplos etiquetados y una evaluación de mejora), RF-10 (cuentas e interfaz exceden el tiempo de esta versión)

Para este prototipo cuento con **30 horas**. Reservo 9 para pruebas, documentación y defensa, y 6 para imprevistos. Quedan 15 horas para construir las cuatro funciones imprescindibles, según la estimación de `presupuesto/presupuesto_alcance.py`.

Por ahora los artículos se cargarán como TXT o Markdown; subir el PDF directamente necesitaría otras 6 horas y queda para después. Una tabla pequeña en Markdown se podrá consultar como texto y citar su archivo. Filtrar filas o hacer cálculos sobre tablas grandes será otra etapa. Los archivos se podrán ir agregando al mismo índice: probaré seis cargas, aunque eso todavía no dice cómo rendirá el sistema con una colección grande.

## 3. Arquitectura de la solución

Diagrama: docs/diagrama_arquitectura.png

- Modelo: Uso Gemini para los embeddings y las respuestas porque el Gate 2 ya trabaja con esa API. La clave se lee de `.env` al arrancar y no se incluye en la imagen. Por eso, en este prototipo solo cargo material público o de prueba.
- Vector store: Reutilizo el código de Chroma del Gate 2, pero este prototipo empieza con una colección y carpeta de índice propias, vacías, para no mezclar sus notas con los diez textos de práctica anteriores. Chroma corre con el servicio; su carpeta de datos queda montada como volumen para conservar fragmentos y fuentes.
- Orquestación: Parto del flujo de `servicio_rag.py`, que ya recupera, filtra inyección, cita fuentes y registra una traza por consulta. Le agrego la carga de TXT y Markdown. La supervisión humana con LangGraph queda para cambios de riesgo, sin pedir aprobación en cada pregunta.
- Exposición: FastAPI permite probar la carga y la consulta con dos endpoints y respuestas JSON, sin construir una interfaz web ni cuentas en esta versión.
- Empaquetado: Docker reúne FastAPI y la orquestación para repetir el arranque en otra máquina. El volumen deja el índice fuera de la capa del contenedor, así se conserva aunque el contenedor se reemplace.

El diagrama muestra la arquitectura que vamos a construir durante el Módulo 3. El Gate 2 ya tiene recuperación, citas y controles sobre un corpus fijo; la carga de TXT o Markdown, FastAPI y Docker aún no están implementados. Para esta demostración usaremos material público o de prueba, porque el modelo y los embeddings actuales llaman a Gemini. Los archivos privados que no deban salir del entorno del investigador quedan para una versión local posterior.

## 4. Criterios de aceptación

Cada prueba parte de un índice vacío, separado del corpus del Gate 2, salvo cuando el criterio indica que se cargan archivos antes de consultar. Las notas simuladas están en `docs/datos_prueba/`. Para probar el contador se usa `_collection.count()` sobre esa misma colección de Chroma antes y después de la operación.

- CA-01 (RF-03): Con el índice de prueba vacío, al enviar `{"pregunta": "¿Cada cuánto se planifican las tomas?"}` a `POST /consultas`, el servicio devuelve HTTP 200 y un JSON donde `respuesta` es "No tengo información suficiente y verificada para responder esto." y `fuentes` es `[]`.
- CA-02 (RF-03): Al enviar `{"pregunta": ""}` a `POST /consultas`, el servicio devuelve HTTP 422 con un error en JSON.
- CA-03 (RF-01): Al enviar `docs/datos_prueba/plan_transito.txt` en el campo multipart `archivo` de `POST /documentos`, la respuesta HTTP 201 identifica `plan_transito.txt` como fuente y el contador de Chroma indica al menos 1 fragmento nuevo.
- CA-04 (RF-01): Al enviar un TXT vacío llamado `vacio.txt` en el campo multipart `archivo` de `POST /documentos`, el servicio devuelve HTTP 400 y `_collection.count()` conserva el mismo valor de antes del envío.
- CA-05 (RF-02): Tras cargar las dos notas de `docs/datos_prueba/`, la pregunta "¿Cada cuánto se planifican las tomas?" recibe "cada 10 minutos" y cita `plan_transito.txt`.
- CA-06 (RF-02): Tras cargar esas notas, la pregunta "¿Cuál es la masa de Júpiter?" recibe un mensaje de información insuficiente y `fuentes` queda como lista vacía.
- CA-07 (RF-04): Después de cargar `plan_transito.txt`, ejecutar `docker compose down` sin `-v` y luego `docker compose up --build` con el mismo volumen, la pregunta "¿Cada cuánto se planifican las tomas?" sigue devolviendo "cada 10 minutos" y la fuente `plan_transito.txt` sin cargar el archivo otra vez.
- CA-08 (RNF-01): Después de cargar las dos notas y ejecutar las 10 preguntas de `docs/datos_prueba/preguntas_evaluacion.md`, cada línea del registro es JSON. Sus únicos valores de texto son fecha, identificadores opacos y nombres fijos de nivel, evento o mensaje. No aparecen campos con preguntas, fragmentos, nombres de archivos ni claves; los demás valores son números o booleanos.
- CA-09 (RNF-02): Las preguntas 1 a 8 de `docs/datos_prueba/preguntas_evaluacion.md` reciben el dato indicado en la columna «Resultado esperado» y `fuentes` incluye el archivo de la columna «Fuente esperada». Al abrir ese archivo se puede comprobar el dato citado; no se aceptan fuentes inventadas ni afirmaciones que contradigan la nota.
- CA-10 (RNF-02): Las preguntas 9 y 10 de `docs/datos_prueba/preguntas_evaluacion.md` indican falta de información y devuelven `fuentes` vacía.
- CA-11 (RNF-03): Desde una carpeta limpia, con clave válida y siguiendo solo el README, una persona ejecuta `docker compose up --build`, carga una nota y obtiene una respuesta en menos de 15 minutos.
- CA-12 (RNF-04): Al medir 10 consultas reales sobre las notas de prueba, al menos 9 devuelven el JSON de respuesta antes de 120 segundos desde el envío de la pregunta.
- CA-13 (RF-01): Después de cargar cinco TXT con nombres distintos en el campo multipart `archivo`, un sexto TXT con otro nombre devuelve HTTP 201, `_collection.count()` aumenta respecto de la quinta carga y los fragmentos anteriores siguen en el índice.
- CA-14 (RF-01, RF-02): Al cargar `docs/datos_prueba/registro_sesion.md` en `POST /documentos`, el servicio devuelve HTTP 201 y conserva `registro_sesion.md` como fuente. Después, la pregunta "¿Qué filtro figura en la toma A2?" responde "rojo" y cita `registro_sesion.md`.

## 5. Plan de construcción por hitos

Horas disponibles: 30 h
Margen de imprevistos: 6 h

- H1 (4,5 h): Servicio FastAPI con rutas de carga y consulta que responden con JSON de prueba. Cubre: RF-03. Se comprueba con: CA-01, CA-02.
- H2 (3 h): Carga de TXT y Markdown de prueba y almacenamiento de sus fragmentos con nombre de fuente. Cubre: RF-01. Se comprueba con: CA-03, CA-04, CA-13, CA-14.
- H3 (3 h): Consultas sobre los archivos cargados con respuesta citada o aviso de información insuficiente. Cubre: RF-02. Se comprueba con: CA-05, CA-06, CA-14.
- H4 (4,5 h): Servicio ejecutable en contenedor que conserva el índice al reiniciar. Cubre: RF-04. Se comprueba con: CA-07.
- H5 (9 h): Pruebas con las diez preguntas, revisión de registros, README y ensayo de la defensa. Cubre: RNF-01, RNF-02, RNF-03, RNF-04. Se comprueba con: CA-08, CA-09, CA-10, CA-11, CA-12.
