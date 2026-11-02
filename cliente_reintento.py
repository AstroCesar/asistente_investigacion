"""Reintentos ante errores temporales, con una prueba local simulada."""

import random
import time
from typing import Any, Callable


def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_base: float = 2,
    espera_maxima: float = 30,
) -> Any:
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError as error:
            if intento == intentos:
                raise
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            espera_con_jitter = min(
                espera + random.uniform(0, espera * 0.1), espera_maxima
            )
            print(
                f"Intento {intento} de {intentos} falló ({error}). "
                f"Reintentando en {espera_con_jitter:.1f}s..."
            )
            time.sleep(espera_con_jitter)


intentos_previos = 0


def enviar_peticion_simulada(cuerpo: dict) -> dict:
    global intentos_previos
    intentos_previos += 1
    if intentos_previos < 3:
        raise TimeoutError("Límite de peticiones excedido.")
    return {"contenido": "Respuesta simulada exitosa", "intento": intentos_previos}


if __name__ == "__main__":
    cuerpo = {"contents": [{"parts": [{"text": "Hola"}]}]}
    respuesta = con_reintento(lambda: enviar_peticion_simulada(cuerpo))
    print(respuesta)
