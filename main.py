"""Punto de entrada para probar el asistente desde la terminal."""

import sys

from cliente import consultar_modelo


PREGUNTA_EJEMPLO = (
    "¿A qué distancia está el centro de la Vía Láctea del Sistema Solar? "
    "Responde en 25 palabras."
)


def main():
    pregunta = " ".join(sys.argv[1:]).strip() or PREGUNTA_EJEMPLO
    try:
        print(consultar_modelo(pregunta))
    except (ValueError, RuntimeError) as error:
        print(f"No pude obtener la respuesta: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
