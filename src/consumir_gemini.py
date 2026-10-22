import json
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def armar_peticion(pregunta, system_instruction=None, response_schema=None):
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("Escribe una pregunta antes de continuar.")
    if system_instruction is not None and (
        not isinstance(system_instruction, str) or not system_instruction.strip()
    ):
        raise ValueError("La instrucción de sistema debe tener texto.")
    if response_schema is not None and not isinstance(response_schema, dict):
        raise ValueError("El esquema de respuesta debe ser un diccionario.")
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
    if system_instruction is not None:
        body["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
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


def parsear_respuesta_json(texto, response_schema):
    if not isinstance(texto, str):
        raise ValueError("La respuesta del modelo no es texto.")
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError as error:
        raise ValueError("La respuesta del modelo no es JSON válido.") from error
    if not isinstance(datos, dict):
        raise ValueError("La respuesta JSON debe ser un objeto.")
    for clave in response_schema["required"]:
        if clave not in datos:
            raise ValueError(f"Falta la clave '{clave}' en la respuesta.")
        tipo = response_schema["properties"][clave]["type"]
        valor = datos[clave]
        if tipo == "STRING" and not isinstance(valor, str):
            raise ValueError(f"La clave '{clave}' debe ser texto.")
        if tipo == "NUMBER" and (
            not isinstance(valor, (int, float)) or isinstance(valor, bool)
        ):
            raise ValueError(f"La clave '{clave}' debe ser un número.")
        if tipo == "BOOLEAN" and not isinstance(valor, bool):
            raise ValueError(f"La clave '{clave}' debe ser true o false.")
    return datos

def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usageMetadata"]
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    return (tokens_entrada * precio_entrada) + (tokens_salida * precio_salida)

def obtener_dato_de_prueba(pregunta):
    url, headers, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, headers, body)
    return extraer_texto(datos)
