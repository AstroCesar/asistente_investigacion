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

Abre el archivo `.env` y reemplaza `tu_llave_aqui` por tu propia clave de Gemini. `MODEL_NAME` ya trae el modelo usado en las pruebas. Guarda el archivo y ejecuta:

```powershell
python main.py
```

Sin argumentos, `main.py` usa una pregunta de ejemplo. También puedes escribir una pregunta propia:

```powershell
python main.py "¿Qué es un exoplaneta?"
```

`main.py` toma la pregunta y muestra la respuesta en la terminal. La parte que arma la petición, habla con Gemini y lee lo que devuelve está en `src/consumir_gemini.py`. Así, si más adelante cambio la forma de hacer preguntas, no tengo que mezclar eso con la conexión a la API.

Deberías ver una respuesta de Gemini en la terminal. Si aparece un mensaje de error, revisa la clave, el acceso a internet y el nombre del modelo en `.env`.

`.env` y `.venv` son locales y están excluidos de Git. No subas tu clave al repositorio.

## Banco de prompts

Los cuatro prompts están en `prompts/banco.py`. El resultado de la prueba de consistencia está en `prompts/registro_resultados.json`. Para repetir las pruebas con tu propia clave:

```powershell
python -m prompts.test_consistencia
```

Ese último comando hace doce peticiones reales a Gemini y actualiza el registro de resultados.

## Ensayo de instalación limpia

El 22 de octubre de 2026 cloné este repositorio desde GitHub en otra carpeta (`prueba-gate1`). Creé un entorno virtual nuevo, instalé lo indicado en `requirements.txt` y configuré la clave en un `.env` local. El script recibió una respuesta de Gemini y terminó sin errores. También comprobé que Git solo registra `.env.example`, no la clave real.

Antes del ensayo faltaba este README. Lo agregué para que otra persona tenga los pasos sin depender de cómo tengo configurado mi computador.

Repetí la prueba en otro computador con Windows 10 y Python 3.13.15. El programa también recibió una respuesta de Gemini. Ahí PowerShell bloqueó la activación del entorno; usé el cambio temporal indicado arriba. No faltaron dependencias.
