# Asistente de investigación

Estoy empezando este asistente para trabajar con temas de investigación astronómica. En esta etapa hace una consulta a Gemini y prueba cuatro prompts cortos que devuelven JSON. Todavía no lee artículos ni PDF; eso vendrá más adelante.

## Ponerlo en marcha (Windows, PowerShell)

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
