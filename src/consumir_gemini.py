import os
import requests
from dotenv import load_dotenv

load_dotenv()

def armar_peticion(pregunta):
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("Escribe una pregunta antes de continuar.")
    api_key = os.getenv("API_KEY")
    modelo = os.getenv("MODEL_NAME")
    if not api_key or not api_key.strip() or api_key.strip() == "tu_llave_aqui":
        raise ValueError("Falta configurar API_KEY en el archivo .env.")
    if not modelo or not modelo.strip():
        raise ValueError("Falta configurar MODEL_NAME en el archivo .env.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    body = {
        "contents": [
            {"parts": [{"text": pregunta}]}
        ]
    }
    headers = {"x-goog-api-key": api_key}
    return url, headers, body

def enviar_peticion(url, headers, body):
    try:
        respuesta = requests.post(url, headers=headers, json=body, timeout=90)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
        raise RuntimeError("Gemini no respondió. Inténtalo de nuevo en un momento.") from error
    try:
        respuesta.raise_for_status()
    except requests.exceptions.HTTPError as error:
        if respuesta.status_code == 503:
            raise RuntimeError(
                "Gemini está ocupado ahora. Inténtalo de nuevo en un momento."
            ) from error
        if respuesta.status_code in (400, 401, 403):
            raise RuntimeError(
                "Gemini rechazó la petición. Revisa la clave o los datos enviados."
            ) from error
        raise RuntimeError(
            f"Gemini devolvió un error HTTP {respuesta.status_code}."
        ) from error
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError as error:
        raise RuntimeError("Gemini respondió, pero no pude leer su respuesta.") from error

def extraer_texto(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as error:
        raise RuntimeError(
            "Gemini respondió, pero no encontré el texto esperado."
        ) from error

def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usageMetadata"]
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    return (tokens_entrada * precio_entrada) + (tokens_salida * precio_salida)

def obtener_dato_de_prueba(pregunta):
    url, headers, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, headers, body)
    return extraer_texto(datos)


if __name__ == "__main__":
    try:
        print(obtener_dato_de_prueba(
            "A que distancia est el centro de la via lactea del sistema solar?, en 25 palabras"
        ))
    except (ValueError, RuntimeError) as error:
        print("No pude obtener la respuesta:", error)
