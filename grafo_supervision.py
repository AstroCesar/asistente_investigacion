"""Pausa la propuesta de prompt y espera una decisión humana en consola."""

import argparse
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from estado_prompt import (
    ARCHIVO_ESTADO_PROMPT,
    HUELLA_PROPUESTA,
    activar_prompt,
    leer_prompt_activo,
)
from registro_prompts import INSTRUCCION_PROPUESTA, huella_prompt



class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


class EstadoBorrado(TypedDict):
    nota_id: str
    aprobado: bool


def crear_grafo_borrado():
    """Pausa el borrado de la nota que la matriz marca como riesgo ALTO."""
    def supervisar_borrado(estado: EstadoBorrado) -> dict:
        decision = interrupt({
            "motivo": "aprobar borrado definitivo de una nota",
            "nota_id": estado["nota_id"],
        })
        if type(decision) is not bool:
            raise TypeError("La aprobación del borrado debe ser True o False.")
        return {"aprobado": decision}

    grafo = StateGraph(EstadoBorrado)
    grafo.add_node("supervisar_borrado", supervisar_borrado)
    grafo.add_edge(START, "supervisar_borrado")
    grafo.add_edge("supervisar_borrado", END)
    return grafo.compile(checkpointer=InMemorySaver())


def resolver_borrado_con_persona(
    nota_id: str, mensaje: str, pedir_aprobacion: Callable[[str], bool],
) -> bool:
    """Reanuda el grafo con la decisión humana sobre esa nota concreta."""
    app = crear_grafo_borrado()
    config = nueva_config()
    pausado = app.invoke({"nota_id": nota_id, "aprobado": False}, config=config)
    if "__interrupt__" not in pausado:
        raise RuntimeError("El grafo no se pausó antes del borrado.")
    pendiente = pausado["__interrupt__"][0].value
    if pendiente["nota_id"] != nota_id:
        raise RuntimeError("La nota pendiente no coincide con la solicitada.")
    decision = pedir_aprobacion(mensaje)
    if type(decision) is not bool:
        raise TypeError("La decisión humana debe ser True o False.")
    final = app.invoke(Command(resume=decision), config=config)
    if final["nota_id"] != nota_id or final["aprobado"] is not decision:
        raise RuntimeError("La decisión sobre el borrado no quedó registrada.")
    return decision


def proponer(estado: EstadoDespliegue) -> dict:
    print("nodo: proponer huella", estado["huella_nueva"])
    return {}


def supervisar(estado: EstadoDespliegue) -> dict:
    decision = interrupt({
        "motivo": "aprobar una nueva versión del prompt RAG antes de activarla",
        "huella_propuesta": estado["huella_nueva"],
    })
    if type(decision) is not bool:
        raise TypeError("La aprobación del prompt debe ser True o False.")
    return {"aprobado": decision}


def crear_grafo(archivo_estado: Path = ARCHIVO_ESTADO_PROMPT):
    def aplicar(estado: EstadoDespliegue) -> dict:
        if estado["aprobado"] is True:
            activar_prompt(estado["huella_nueva"], archivo_estado)
            print("nodo: aplicar -> versión", estado["huella_nueva"], "activa en el RAG local")
        else:
            print("nodo: aplicar -> rechazo; el prompt activo se mantiene")
        return {}

    grafo = StateGraph(EstadoDespliegue)
    grafo.add_node("proponer", proponer)
    grafo.add_node("supervisar", supervisar)
    grafo.add_node("aplicar", aplicar)
    grafo.add_edge(START, "proponer")
    grafo.add_edge("proponer", "supervisar")
    grafo.add_edge("supervisar", "aplicar")
    grafo.add_edge("aplicar", END)
    return grafo.compile(checkpointer=InMemorySaver())


def nueva_config() -> dict:
    return {"configurable": {"thread_id": "prompt-" + uuid.uuid4().hex[:8]}}


def resolver(app, config: dict, huella_revisada: str, aprobado: bool) -> dict:
    if type(aprobado) is not bool:
        raise TypeError("la decisión debe ser True o False")
    snapshot = app.get_state(config)
    if not snapshot.next or not snapshot.interrupts:
        raise ValueError("no hay una aprobación pendiente para este thread_id")
    pendiente = snapshot.interrupts[0].value
    if pendiente["huella_propuesta"] != huella_revisada:
        raise ValueError("la huella pendiente no coincide con la revisada")
    return app.invoke(Command(resume=aprobado), config=config)


def ejecutar_interactivo(archivo_estado: Path = ARCHIVO_ESTADO_PROMPT) -> dict:
    """La persona decide si el grafo sigue por aprobación o rechazo."""
    app = crear_grafo(archivo_estado)
    config = nueva_config()
    activo_antes = leer_prompt_activo(archivo_estado)
    print("Prompt activo ahora:", activo_antes)
    print("Prompt propuesto:", INSTRUCCION_PROPUESTA)
    pausado = app.invoke(
        {"huella_nueva": HUELLA_PROPUESTA, "aprobado": False}, config=config,
    )
    if "__interrupt__" not in pausado:
        raise RuntimeError("El grafo no se pausó antes de pedir la decisión.")
    pendiente = app.get_state(config).interrupts[0].value
    print("Propuesta pendiente:", pendiente)
    print("La decisión cambiará solo el prompt del RAG local, no hará un despliegue.")
    while True:
        try:
            respuesta = input("¿Apruebas usar el prompt propuesto en el RAG local? (s/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            respuesta = "n"
        if respuesta in {"s", "n"}:
            break
        print("Escribe s o n.")
    final = resolver(app, config, HUELLA_PROPUESTA, respuesta == "s")
    print("Decisión registrada:", "aprobada" if final["aprobado"] else "rechazada")
    print("Huella activa ahora:", huella_prompt(leer_prompt_activo(archivo_estado)))
    return final


def ejecutar_ensayo() -> None:
    with TemporaryDirectory() as temporal:
        archivo_aprobacion = Path(temporal) / "aprobacion.json"
        archivo_rechazo = Path(temporal) / "rechazo.json"
        _ensayar_ramas(archivo_aprobacion, archivo_rechazo)


def _ensayar_ramas(archivo_aprobacion: Path, archivo_rechazo: Path) -> None:
    app = crear_grafo(archivo_aprobacion)
    config_aprobacion = nueva_config()

    print("=" * 60)
    print("PASO 1: propuesta pausada antes de aplicar nada")
    print("=" * 60)
    pausado = app.invoke(
        {"huella_nueva": HUELLA_PROPUESTA, "aprobado": False}, config=config_aprobacion,
    )
    snapshot = app.get_state(config_aprobacion)
    assert "__interrupt__" in pausado
    assert snapshot.next == ("supervisar",)
    print("interrupción detectada:", "__interrupt__" in pausado)
    print("pendiente:", snapshot.interrupts[0].value)

    print("\n" + "=" * 60)
    print("PASO 2: simular aprobación con Command(resume=True)")
    print("=" * 60)
    aprobado = resolver(app, config_aprobacion, HUELLA_PROPUESTA, True)
    print("estado final:", aprobado)
    assert aprobado["aprobado"] is True
    assert app.get_state(config_aprobacion).values["aprobado"] is True
    assert huella_prompt(leer_prompt_activo(archivo_aprobacion)) == HUELLA_PROPUESTA

    app_rechazo = crear_grafo(archivo_rechazo)
    config_rechazo = nueva_config()
    print("\n" + "=" * 60)
    print("PASO 3: otra solicitud, rechazada con Command(resume=False)")
    print("=" * 60)
    pausado_2 = app_rechazo.invoke(
        {"huella_nueva": HUELLA_PROPUESTA, "aprobado": False}, config=config_rechazo,
    )
    assert "__interrupt__" in pausado_2
    rechazado = resolver(app_rechazo, config_rechazo, HUELLA_PROPUESTA, False)
    print("estado final:", rechazado)
    assert rechazado["aprobado"] is False
    assert app_rechazo.get_state(config_rechazo).values["aprobado"] is False
    assert not archivo_rechazo.exists()
    assert config_aprobacion != config_rechazo
    print("Prueba terminada: la aprobación cambió solo un estado temporal.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba la supervisión de una versión de prompt.")
    parser.add_argument(
        "--ensayo", action="store_true",
        help="recorre aprobación y rechazo automáticamente, sin pedir una decisión",
    )
    args = parser.parse_args()
    if args.ensayo:
        ejecutar_ensayo()
    else:
        ejecutar_interactivo()


if __name__ == "__main__":
    main()
