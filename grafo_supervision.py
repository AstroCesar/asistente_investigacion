"""Pausa una activación simulada de prompt hasta recibir aprobación o rechazo."""

import uuid
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


# Huella de la propuesta mostrada por `python registro_prompts.py`.
HUELLA_PROPUESTA = "d075246d4ba1"


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


def proponer(estado: EstadoDespliegue) -> dict:
    print("nodo: proponer huella", estado["huella_nueva"])
    return {}


def supervisar(estado: EstadoDespliegue) -> dict:
    decision = interrupt({
        "motivo": "aprobar una nueva versión del prompt RAG antes de activarla",
        "huella_propuesta": estado["huella_nueva"],
    })
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue) -> dict:
    # Esta práctica no tiene despliegue real; solo muestra qué rama se ejecutaría.
    if estado["aprobado"]:
        print("nodo: aplicar -> versión", estado["huella_nueva"], "activada solo en la simulación")
    else:
        print("nodo: aplicar -> rechazo; el prompt anterior se mantiene")
    return {}


def crear_grafo():
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


def main() -> None:
    app = crear_grafo()
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

    config_rechazo = nueva_config()
    print("\n" + "=" * 60)
    print("PASO 3: otra solicitud, rechazada con Command(resume=False)")
    print("=" * 60)
    pausado_2 = app.invoke(
        {"huella_nueva": HUELLA_PROPUESTA, "aprobado": False}, config=config_rechazo,
    )
    assert "__interrupt__" in pausado_2
    rechazado = resolver(app, config_rechazo, HUELLA_PROPUESTA, False)
    print("estado final:", rechazado)
    assert rechazado["aprobado"] is False
    assert app.get_state(config_rechazo).values["aprobado"] is False
    assert config_aprobacion != config_rechazo
    print("Prueba terminada: no se activó ningún prompt real.")


if __name__ == "__main__":
    main()
