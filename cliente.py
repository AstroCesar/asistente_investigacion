"""Punto de entrada para consultar a Gemini con reintentos controlados."""

from cliente_reintento import con_reintento
from src.consumir_gemini import (
    armar_peticion,
    calcular_costo,
    enviar_peticion,
    extraer_texto,
)


# Tarifa estándar publicada para Gemini 3.5 Flash-Lite, consultada el 25-10-2026.
# https://ai.google.dev/gemini-api/docs/pricing
MODELO_CON_TARIFA = "gemini-3.5-flash-lite"
PRECIO_ENTRADA_POR_TOKEN = 0.30 / 1_000_000
PRECIO_SALIDA_POR_TOKEN = 2.50 / 1_000_000
costo_total_sesion = 0.0


def registrar_costo(respuesta: dict) -> float | None:
    global costo_total_sesion

    if respuesta.get("modelVersion") != MODELO_CON_TARIFA:
        print("Costo no estimado: no hay una tarifa registrada para este modelo.")
        return None

    uso = respuesta.get("usageMetadata")
    if not isinstance(uso, dict) or not {
        "promptTokenCount", "candidatesTokenCount"
    }.issubset(uso):
        print("Costo no estimado: Gemini no informó los tokens necesarios.")
        return None

    costo = calcular_costo(
        respuesta, PRECIO_ENTRADA_POR_TOKEN, PRECIO_SALIDA_POR_TOKEN
    )
    costo_total_sesion += costo
    tokens_salida = uso["candidatesTokenCount"] + uso.get("thoughtsTokenCount", 0)
    print(
        f"Tokens: {uso['promptTokenCount']} de entrada y {tokens_salida} de salida "
        f"(incluido razonamiento). Costo estimado a tarifa de pago: "
        f"US${costo:.8f} (sesión: US${costo_total_sesion:.8f})."
    )
    return costo


def consultar_modelo(pregunta: str, system_instruction: str | None = None) -> str:
    url, headers, body = armar_peticion(pregunta, system_instruction)
    try:
        datos = con_reintento(lambda: enviar_peticion(url, headers, body))
    except TimeoutError as error:
        raise RuntimeError(
            "Gemini no respondió tras varios intentos. Intenta más tarde."
        ) from error
    texto = extraer_texto(datos)
    registrar_costo(datos)
    return texto
