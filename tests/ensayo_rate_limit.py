"""Ensayo manual: consultas reales seguidas para observar posibles HTTP 429."""

import socket
import sys

import cliente


PREGUNTAS = [
    "¿Qué es un exoplaneta? Responde en una frase.",
    "¿Qué es una nebulosa? Responde en una frase.",
    "¿Qué es una supernova? Responde en una frase.",
    "¿Qué es un púlsar? Responde en una frase.",
    "¿Qué es el paralaje estelar? Responde en una frase.",
    "¿Qué es una enana blanca? Responde en una frase.",
    "¿Qué es una galaxia espiral? Responde en una frase.",
    "¿Qué es el corrimiento al rojo? Responde en una frase.",
    "¿Qué es un agujero negro? Responde en una frase.",
    "¿Qué es un cúmulo globular? Responde en una frase.",
]


def main():
    try:
        cantidad = int(sys.argv[1]) if len(sys.argv) == 2 else len(PREGUNTAS)
    except ValueError:
        print("Indica una cantidad de consultas entre 1 y 20.")
        return
    if not 1 <= cantidad <= 20:
        print("Indica una cantidad de consultas entre 1 y 20.")
        return

    try:
        socket.getaddrinfo("generativelanguage.googleapis.com", 443)
    except socket.gaierror:
        print("Ensayo no iniciado: no se puede resolver la dirección de Gemini.")
        return

    exitos = 0
    fallos = 0
    for numero in range(cantidad):
        pregunta = PREGUNTAS[numero % len(PREGUNTAS)]
        try:
            respuesta = cliente.consultar_modelo(pregunta)
            exitos += 1
            print(f"Respuesta {numero}: {respuesta[:70]}...")
        except RuntimeError as error:
            fallos += 1
            print(f"Respuesta {numero} falló definitivamente: {error}")
        except ValueError as error:
            print(f"Ensayo detenido: {error}")
            break

    print(f"Consultas con respuesta: {exitos}; fallos definitivos: {fallos}.")
    print(f"Costo estimado total del ensayo: US${cliente.costo_total_sesion:.8f}")


if __name__ == "__main__":
    main()
