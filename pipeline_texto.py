"""Prepara texto para comparar respuestas con una referencia."""

import re

from cliente import consultar_modelo


def limpiar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        raise TypeError("limpiar_texto espera un texto")

    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def tokenizar(texto_limpio: str) -> list[str]:
    return texto_limpio.split()


def procesar_texto(texto: str) -> list[str]:
    return tokenizar(limpiar_texto(texto))


def main() -> None:
    casos = [
        (
            "¿Qué es un exoplaneta? Responde en una frase.",
            "Un exoplaneta es un planeta que orbita una estrella fuera del Sistema Solar.",
        ),
        (
            "¿Qué es el paralaje estelar? Responde en una frase.",
            "El paralaje estelar permite medir la distancia de estrellas cercanas.",
        ),
        (
            "¿Qué es una supernova? Responde en una frase.",
            "Una supernova es una explosión estelar muy brillante.",
        ),
    ]

    for numero, (pregunta, referencia) in enumerate(casos, start=1):
        respuesta = consultar_modelo(pregunta)

        ref_cruda = set(referencia.split())
        resp_cruda = set(respuesta.split())
        pct_crudo = len(ref_cruda & resp_cruda) / len(ref_cruda) if ref_cruda else 0.0

        ref_procesada = set(procesar_texto(referencia))
        resp_procesada = set(procesar_texto(respuesta))
        pct_procesado = (
            len(ref_procesada & resp_procesada) / len(ref_procesada)
            if ref_procesada else 0.0
        )

        print(f"\nCaso {numero}: {pregunta}")
        print(f"Referencia: {referencia}")
        print(f"Respuesta: {respuesta}")
        print(f"Coincidencia cruda: {pct_crudo:.1%}")
        print(f"Coincidencia procesada: {pct_procesado:.1%}")


if __name__ == "__main__":
    main()
