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

Abre el archivo `.env` y reemplaza `tu_llave_aqui` por tu propia clave de Gemini. `MODEL_NAME` ya trae el modelo usado en las pruebas. Guarda el archivo y ejecuta:

```powershell
python src/consumir_gemini.py
```

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
