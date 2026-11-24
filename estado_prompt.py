"""Guarda qué versión aprobada usa el RAG local entre ejecuciones."""

import json
import os
import tempfile
from pathlib import Path

from registro_prompts import (
    INSTRUCCION_ANTERIOR,
    INSTRUCCION_PROPUESTA,
    huella_prompt,
)


ARCHIVO_ESTADO_PROMPT = Path(__file__).with_name("prompt_activo.json")
VERSIONES = {
    huella_prompt(INSTRUCCION_ANTERIOR): INSTRUCCION_ANTERIOR,
    huella_prompt(INSTRUCCION_PROPUESTA): INSTRUCCION_PROPUESTA,
}
HUELLA_INICIAL = huella_prompt(INSTRUCCION_ANTERIOR)
HUELLA_PROPUESTA = huella_prompt(INSTRUCCION_PROPUESTA)


def leer_prompt_activo(archivo: Path = ARCHIVO_ESTADO_PROMPT) -> str:
    """Sin archivo de estado, el servicio usa la versión anterior."""
    if not archivo.exists():
        return INSTRUCCION_ANTERIOR
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    huella = datos.get("huella")
    if huella not in VERSIONES:
        raise ValueError("La versión activa del prompt no está en el registro.")
    return VERSIONES[huella]


def activar_prompt(huella: str, archivo: Path = ARCHIVO_ESTADO_PROMPT) -> None:
    """Persiste solo una versión conocida, después de pasar por el grafo."""
    if huella not in VERSIONES:
        raise ValueError("No se puede activar una versión de prompt desconocida.")
    descriptor, temporal = tempfile.mkstemp(
        prefix=".prompt-", suffix=".tmp", dir=archivo.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as salida:
            json.dump({"huella": huella}, salida, ensure_ascii=False)
        os.replace(temporal, archivo)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)
