"""Identificadores locales para relacionar registros sin guardar el texto original."""

import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path


_CLAVE_DE_ESTA_EJECUCION = secrets.token_bytes(32)
TEXTO_OMITIDO = "[texto omitido]"


def id_opaco(texto: str, prefijo: str) -> str:
    """El mismo texto conserva su ID durante esta ejecución, no entre ejecuciones."""
    huella = hmac.new(
        _CLAVE_DE_ESTA_EJECUCION, texto.encode("utf-8"), hashlib.sha256
    ).hexdigest()[:12]
    return f"{prefijo}_{huella}"


def argumentos_sin_valores(argumentos) -> dict:
    """Conserva solo los nombres conocidos de los campos usados por el agente."""
    if not isinstance(argumentos, dict):
        return {"n_campos": 0}
    if set(argumentos) == {"campos", "n_campos"}:
        return argumentos
    permitidos = {
        "cantidad_tomas", "minutos_por_toma", "termino", "titulo", "contenido", "nota_id"
    }
    nombres = sorted(campo for campo in argumentos if campo in permitidos)
    return {"campos": nombres, "n_campos": len(argumentos)}


def _id_existente_o_nuevo(valor: str, prefijo: str) -> str:
    if re.fullmatch(rf"{prefijo}_[0-9a-f]{{12}}", valor):
        return valor
    return id_opaco(valor, prefijo)


def sanitizar_traza(registro: dict) -> dict:
    """Conserva sesión, herramientas y resultado de aprobación sin texto libre."""
    acciones = []
    for accion in registro.get("acciones", []):
        observacion = str(accion.get("observacion", ""))
        paso = {
            "herramienta": accion.get("herramienta", "desconocida"),
            "argumentos": argumentos_sin_valores(accion.get("argumentos")),
            "observacion": TEXTO_OMITIDO,
            "observacion_len": accion.get("observacion_len", len(observacion)),
        }
        if paso["herramienta"] == "eliminar_nota_observacion":
            if "aprobado" in accion:
                paso["aprobado"] = accion["aprobado"]
            elif "no aprobado" in observacion.lower():
                paso["aprobado"] = False
            elif "borrado aprobado" in observacion.lower():
                paso["aprobado"] = True
            else:
                paso["aprobado"] = None
        acciones.append(paso)
    entrada = str(registro.get("entrada", ""))
    respuesta = str(registro.get("respuesta_final", ""))
    return {
        "timestamp": registro["timestamp"],
        "session_id": _id_existente_o_nuevo(str(registro["session_id"]), "sesion"),
        "entrada": TEXTO_OMITIDO,
        "entrada_len": registro.get("entrada_len", len(entrada)),
        "acciones": acciones,
        "respuesta_final": TEXTO_OMITIDO,
        "respuesta_len": registro.get("respuesta_len", len(respuesta)),
    }


def sanitizar_costo(registro: dict) -> dict:
    """Mantiene mediciones y permite comparar k sin guardar la pregunta."""
    pregunta = str(registro["pregunta"])
    return {
        "timestamp": registro["timestamp"],
        "pregunta": _id_existente_o_nuevo(pregunta, "consulta"),
        "pregunta_len": registro.get("pregunta_len", len(pregunta)),
        "k": registro["k"],
        "tiempos_ms": registro["tiempos_ms"],
        "tiempo_total_ms": registro.get("tiempo_total_ms"),
        "tokens": registro.get("tokens"),
    }


def migrar_archivo(ruta: Path, transformar) -> int:
    registros = [
        transformar(json.loads(linea))
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text(
        "".join(json.dumps(registro, ensure_ascii=False) + "\n" for registro in registros),
        encoding="utf-8",
    )
    temporal.replace(ruta)
    return len(registros)


if __name__ == "__main__":
    carpeta = Path(__file__).parent
    n_trazas = migrar_archivo(carpeta / "trazas_agente.jsonl", sanitizar_traza)
    n_costos = migrar_archivo(carpeta / "registros_latencia_costo.jsonl", sanitizar_costo)
    print(f"Registros sin texto crudo: {n_trazas} trazas y {n_costos} consultas medidas.")
