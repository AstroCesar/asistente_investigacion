"""Prueba cada prompt tres veces y guarda cuántas respuestas fueron válidas."""

import json
import os
import time
from datetime import date
from pathlib import Path

from prompts.banco import BANCO_DE_PROMPTS
from src.consumir_gemini import (
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    parsear_respuesta_json,
)


def main():
    registro = {
        "fecha": date.today().isoformat(),
        "modelo": os.getenv("MODEL_NAME"),
        "resultados": {},
    }

    for prompt in BANCO_DE_PROMPTS:
        exitos = 0
        intentos = 3
        print(f"\n{prompt['nombre']}:")

        for numero in range(1, intentos + 1):
            try:
                url, headers, body = armar_peticion(
                    prompt["ejemplo_usuario"],
                    prompt["system_instruction"],
                    prompt["response_schema"],
                )
                respuesta = enviar_peticion(url, headers, body)
                texto = extraer_texto(respuesta)
                datos = parsear_respuesta_json(texto, prompt["response_schema"])
                if not all(
                    clave in datos for clave in prompt["claves_esperadas"]
                ):
                    raise ValueError("Falta una clave esperada en la respuesta.")
                for clave, esperado in prompt.get("valores_esperados", {}).items():
                    if datos[clave] != esperado:
                        raise ValueError(
                            f"La clave '{clave}' tiene un valor distinto al esperado."
                        )
                exitos += 1
                print(f"  intento {numero}: válido {datos}")
            except (ValueError, RuntimeError) as error:
                print(f"  intento {numero}: falló ({error})")

            if numero < intentos:
                time.sleep(1)

        fallos = intentos - exitos
        registro["resultados"][prompt["nombre"]] = {
            "exitos": exitos,
            "fallos": fallos,
            "intentos": intentos,
        }
        print(f"  resultado: {exitos}/{intentos} respuestas válidas")

    ruta = Path(__file__).with_name("registro_resultados.json")
    ruta.write_text(
        json.dumps(registro, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nRegistro guardado en {ruta}")


if __name__ == "__main__":
    main()
