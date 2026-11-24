# Asistente de investigación

Mi idea es construir un asistente que me ayude con la investigación astronómica. Todavía estamos armando la base. En el primer módulo hice consultas directas a Gemini; en este ya puedo guardar textos, buscar los que tienen relación con una pregunta y responder mostrando de qué archivo salió la información.

Por ahora el corpus es chico: cinco fragmentos que explican partes del programa y cinco fichas inventadas para practicar cómo se organizaría una observación. Las fichas están en `corpus_practica.py` y no representan observaciones reales. El asistente todavía no lee artículos ni PDF ni consulta un catálogo de estrellas. Me sirve para probar el recorrido completo antes de incorporar fuentes de investigación.

## Gate 2: indexar y consultar el RAG

Estas instrucciones son para Windows PowerShell. Probé las dependencias de `requirements.txt` con Python 3.14.7. Para instalar estas versiones, usa Python 3.12 o superior.

```powershell
git clone https://github.com/AstroCesar/asistente_investigacion.git
cd asistente_investigacion
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Edita `.env` y reemplaza `tu_llave_aqui` por tu clave en `API_KEY`. `MODEL_NAME` trae el modelo usado en el proyecto. La clave no se imprime ni se sube a Git.

`verificar_entorno.py` detecta si dejaste la clave de ejemplo y cuenta los fragmentos guardados. Si aparece que falta el índice antes de indexar, está bien: todavía no lo creaste. El verificador no llama a Gemini; una clave inválida se detecta cuando el programa necesita llamar a la API para indexar o consultar.

En un clon nuevo, crea el índice una vez y luego abre el servicio:

```powershell
python indexar_corpus.py
python verificar_entorno.py
python servicio_rag.py "¿Qué hace el cliente si Gemini no responde?"
```

La primera orden usa Gemini para convertir los textos en vectores y guarda diez fragmentos en `vectorstore/`. Esa carpeta queda en tu equipo y Git no la sube. Si ya tenías los cinco textos anteriores, el indexador conserva esos registros y agrega las cinco fichas nuevas. Si vuelves a correrlo sin cambiar nada, no calcula otra vez los vectores guardados. Si editas un texto sin cambiar su lugar, o agregas uno al final, procesa los cambios. Si quitas un texto del corpus, el índice no lo borra por su cuenta. El servicio abre el índice que ya existe; en cada pregunta genera el vector de la consulta y le pide la respuesta a Gemini.

La respuesta debe traer una cita como `[1]` y una línea `Fuentes: [1] cliente_reintento.py`. El servicio aparta los fragmentos sospechosos o que no tienen fuente. Si no queda información confiable, o la respuesta viene sin una cita válida, lo dice en vez de inventar. En la consola aparecen eventos con un mismo `trace_id` para seguir cada consulta. Guardan cantidades, tiempos y tokens, pero no copian el texto de la pregunta ni de los documentos. El costo es una estimación con la tarifa que anoté el 25 de octubre de 2026, no una factura ni un precio que se actualice solo.

Para comprobar los cuatro criterios obligatorios sin gastar tokens:

```powershell
python -m pytest test_gate2.py -v
```

Las pruebas crean un índice temporal con embeddings simulados y borran solo una nota temporal del propio test. También puedes ejecutar `python ensayo_gate2.py` para ver el ensayo guiado, igualmente simulado. El borrado de una nota real es la acción de riesgo alto de este prototipo: el grafo se pausa con `interrupt()`, espera la decisión `s/n` en consola y se reanuda con `Command(resume=...)` antes de permitir el borrado. La matriz está en `matriz_riesgos.py` y las versiones de prompt en `registro_prompts.py`. No hicimos un despliegue a producción.

Para decidir si el RAG local usa la nueva versión del prompt, corre `python grafo_supervision.py`: muestra los dos textos, se detiene y espera que escribas `s` o `n`. Con `s`, guarda la huella aprobada en `prompt_activo.json` y la próxima consulta de `servicio_rag.py` usa ese texto. Con `n`, mantiene el texto que ya estuviera activo. El archivo de estado queda en tu equipo y está excluido de Git; en una instalación nueva se usa la versión anterior hasta que alguien apruebe la propuesta. Para probar las dos ramas sin cambiar tu estado local, usa `python grafo_supervision.py --ensayo`. Esto cambia el prompt del prototipo local, no despliega nada a producción.

Si quieres ver la supervisión y la consulta real en una sola corrida, usa `python servicio_rag.py --mostrar-supervision`. Primero se detiene y te pide `s` o `n`. Después hace la pregunta con el prompt que haya quedado activo y muestra su huella en `consulta_recibida`. Esta opción sí llama a Gemini. La consulta normal no pide aprobación porque no está cambiando el prompt. Si la versión propuesta ya estaba activa, responder `n` solo la deja como estaba: no vuelve a la versión anterior.

La evaluación de recuperación usa quince preguntas de este corpus. Se corre con `python evaluacion_recuperacion.py` y deja el resultado en `resultados_evaluacion.txt`. Mi decisión sobre personalización está en `decision_personalizacion.md`; el cálculo se puede repetir con `python decision.py`. Las mediciones reales de tiempo y tokens del Bloque 28 están en `registros_latencia_costo.jsonl`. `trazas_agente.jsonl` guarda los pasos del agente y las decisiones de aprobación sin guardar texto libre. El servicio muestra su propia traza en la consola. Conviene revisar juntos esos eventos y la respuesta al hacer la corrida final.

La corrida real y mi revisión de la rúbrica están en `docs/entrega_gate2.md`. Ahí distingo las mediciones reales de las pruebas simuladas y explico qué conserva cada registro.

También probé la instalación en carpetas nuevas, sin copiar `.env` ni el índice. Instalé las dependencias, corrí las pruebas e hice consultas reales a Gemini desde esas copias con una clave configurada en cada una. Después agregué `--mostrar-supervision`, probé `s` y `n`, y corrí la consulta real con esa opción. Dejé los resultados en `docs/entrega_gate2.md`.

## Lo que quiero hacer después

Este Gate 2 prueba que las piezas funcionan juntas con un corpus de práctica. Más adelante quiero usar la misma base para un asistente que me ayude a investigar: cargar fuentes astronómicas que pueda revisar, buscar información sobre estrellas u otros objetos y ver de dónde sale cada respuesta. Ahí tendré que decidir qué datos reales usar y cómo mantenerlos al día. La indexación, la búsqueda, las citas y los controles ya están en partes separadas, así que puedo cambiar el corpus y mejorar cada parte sin rehacer todo el programa. Eso todavía es trabajo pendiente, no una función que esté lista hoy.

## Primer módulo: consulta directa a Gemini (Windows, PowerShell)

Necesitas Python y Git instalados, y una clave de la API de Gemini.

```powershell
git clone https://github.com/AstroCesar/asistente_investigacion.git
cd asistente_investigacion
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Si PowerShell bloquea `Activate.ps1` con un error `PSSecurityException`, ejecuta esto en la misma terminal y vuelve a activar el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

El cambio de política dura solo mientras esté abierta esa terminal.

Abre el archivo `.env` con el editor que uses (por ejemplo, con `notepad .env` desde PowerShell) y pon tu clave de Gemini en `API_KEY`, reemplazando `tu_llave_aqui`. La otra variable, `MODEL_NAME`, ya trae el modelo usado en las pruebas. Guarda el archivo y ejecuta:

```powershell
python main.py
```

Sin argumentos, `main.py` usa una pregunta de ejemplo. También puedes escribir una pregunta propia:

```powershell
python main.py "¿Qué es un exoplaneta?"
```

Deberías ver los tokens, un costo estimado y la respuesta de Gemini en la terminal. Si aparece un mensaje de error, revisa la clave, el acceso a internet y el nombre del modelo en `.env`.

`.env` y `.venv` son locales y están excluidos de Git. No subas tu clave al repositorio.

## Cómo está organizado

`main.py` es el archivo que se ejecuta para hacer una pregunta. Llama a `cliente.py`, que organiza la consulta completa. Por dentro usa `src/consumir_gemini.py` para preparar la petición, enviarla a Gemini y extraer el texto. Si hay un problema temporal, `cliente_reintento.py` espera y vuelve a intentar; una clave inválida no se reintenta.

Para ver los reintentos sin llamar a Gemini, puedes ejecutar `python cliente_reintento.py`. Esa prueba simulada falla dos veces y responde en el tercer intento.

En el mismo módulo está `calcular_costo()`. Ahora `cliente.py` la usa después de cada respuesta exitosa: muestra el costo estimado de esa consulta y el acumulado de la sesión. La estimación usa la tarifa de pago publicada para Gemini 3.5 Flash-Lite, [consultada el 25 de octubre de 2026](https://ai.google.dev/gemini-api/docs/pricing); no significa que se haya cobrado ese importe en el nivel gratuito. El acumulado vuelve a cero cada vez que cierras el programa.

También probé otros modelos antes de elegir Gemini. La comparación de precios por tokens, tiempos y calidad de las respuestas, junto con el motivo de la elección, está en [la decisión de arquitectura](docs/decision-arquitectura.md). Esa comparación es distinta del costo estimado que ahora aparece en cada consulta.

## Banco de prompts

Los cuatro prompts están en `prompts/banco.py`. El resultado de la prueba de consistencia está en `prompts/registro_resultados.json`. Para repetir las pruebas con tu propia clave:

```powershell
python -m prompts.test_consistencia
```

Ese último comando hace doce peticiones reales a Gemini y actualiza el registro de resultados.

## Pruebas del cliente

Para revisar los errores, reintentos y costos sin llamar a Gemini:

```powershell
python -m pytest test_cliente.py -v
```

Estas pruebas simulan las respuestas de la API y las esperas; no gastan tokens.

## Ensayo de instalación limpia

El 22 de octubre de 2026 cloné este repositorio desde GitHub en otra carpeta (`prueba-gate1`). Creé un entorno virtual nuevo, instalé lo indicado en `requirements.txt` y configuré la clave en un `.env` local. El script recibió una respuesta de Gemini y terminó sin errores. También comprobé que Git solo registra `.env.example`, no la clave real.

Antes del ensayo faltaba este README. Lo agregué para que otra persona tenga los pasos sin depender de cómo tengo configurado mi computador.

Repetí la prueba en otro computador con Windows 10 y Python 3.13.15. El programa también recibió una respuesta de Gemini. Ahí PowerShell bloqueó la activación del entorno; usé el cambio temporal indicado arriba. No faltaron dependencias.

El 22 de octubre repetí el ensayo desde otro clon (`prueba-gate1-main`), esta vez ejecutando `python main.py`. Instalé las dependencias desde `requirements.txt`, configuré un `.env` local y recibí una respuesta de Gemini. Al revisar las instrucciones encontré que el comentario de `.env.example` mencionaba otros proveedores y que el README podía indicar más claramente dónde editar la clave. Aclaré ambos textos; no hubo que cambiar el código ni las dependencias.

Antes de entregar Gate 1, ejecuté de nuevo `python main.py` desde la carpeta principal. Recibí una respuesta de Gemini sobre la distancia al centro de la Vía Láctea y el programa terminó sin errores.
