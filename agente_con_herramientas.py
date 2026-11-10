import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field


@tool
def consultar_glosario(termino: str) -> str:
    """Consulta un término de astronomía. Usar cuando preguntan qué significa un término."""
    glosario = {
        "exoplaneta": "Un exoplaneta es un planeta fuera del Sistema Solar.",
        "transito": "Un tránsito ocurre cuando un planeta pasa frente a su estrella y tapa parte de su luz.",
        "paralaje": "El paralaje es el cambio aparente de posición de un objeto al mirarlo desde dos lugares distintos.",
    }
    try:
        return glosario[termino.strip().lower().replace("á", "a")]
    except KeyError:
        return f"No tengo el término {termino} en este glosario de prueba."


class ArgumentosTiempoObservacion(BaseModel):
    cantidad_tomas: int = Field(
        description="Número de tomas que se harán durante la observación."
    )
    minutos_por_toma: float = Field(
        description="Duración en minutos de cada toma."
    )


@tool(args_schema=ArgumentosTiempoObservacion)
def calcular_tiempo_observacion(cantidad_tomas: int, minutos_por_toma: float) -> str:
    """Calcula minutos totales de observación. Usar cuando dan cantidad de tomas y minutos por toma."""
    if cantidad_tomas <= 0 or minutos_por_toma <= 0:
        return "La cantidad de tomas y los minutos por toma deben ser mayores que cero."
    total = cantidad_tomas * minutos_por_toma
    return f"El tiempo total de observación es {total:g} minutos."


ARCHIVO_NOTAS = Path(__file__).with_name("notas_agente.json")
registro_aprobaciones = []


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 300) -> bool:
    """Espera una respuesta en la consola de Windows. Si no llega, rechaza."""
    if not sys.stdin.isatty():
        return False
    import msvcrt

    print(mensaje, end="", flush=True)
    respuesta = ""
    limite = time.monotonic() + tiempo_limite_segundos
    while time.monotonic() < limite:
        if msvcrt.kbhit():
            tecla = msvcrt.getwch()
            if tecla == "\r":
                print()
                return respuesta.strip().lower() == "s"
            if tecla == "\b":
                respuesta = respuesta[:-1]
            elif tecla.isprintable():
                respuesta += tecla
                print(tecla, end="", flush=True)
        time.sleep(0.1)
    print("\nTiempo agotado. Acción no aprobada.")
    return False


def leer_notas() -> list[dict]:
    if not ARCHIVO_NOTAS.exists():
        return []
    return json.loads(ARCHIVO_NOTAS.read_text(encoding="utf-8"))


@tool
def guardar_nota_observacion(titulo: str, contenido: str) -> str:
    """Guarda una nota de observación local. Se puede corregir o borrar después."""
    if not titulo.strip() or not contenido.strip():
        return "La nota necesita título y contenido."
    notas = leer_notas()
    nota_id = uuid4().hex[:8]
    notas.append({"id": nota_id, "titulo": titulo.strip(), "contenido": contenido.strip()})
    ARCHIVO_NOTAS.write_text(json.dumps(notas, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Nota guardada con ID {nota_id}: {titulo.strip()}"


@tool
def eliminar_nota_observacion(nota_id: str) -> str:
    """Elimina definitivamente una nota local por ID. Pide aprobación humana antes de borrar."""
    notas = leer_notas()
    nota = next((item for item in notas if item["id"] == nota_id), None)
    if nota is None:
        return f"No encontré una nota con ID {nota_id}. No se borró nada."

    aprobado = esperar_aprobacion(
        f"El agente quiere borrar definitivamente la nota '{nota['titulo']}' (ID {nota_id}). "
        "¿Aprobar? (s/n y Enter): "
    )
    registro_aprobaciones.append({
        "herramienta": "eliminar_nota_observacion",
        "argumentos": {"nota_id": nota_id},
        "aprobado": aprobado,
        "momento": datetime.now(timezone.utc).isoformat(),
    })
    if not aprobado:
        return f"Borrado no aprobado para la nota {nota_id}. La nota sigue guardada."
    notas.remove(nota)
    ARCHIVO_NOTAS.write_text(json.dumps(notas, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Borrado aprobado. Se eliminó la nota {nota_id}."


historiales = {}
ARCHIVO_TRAZAS = Path(__file__).with_name("trazas_agente.jsonl")


def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


def dejar_respuesta_como_texto(resultado: dict) -> dict:
    contenido = resultado["output"]
    if isinstance(contenido, list):
        resultado["output"] = "".join(
            bloque["text"] for bloque in contenido if bloque.get("type") == "text"
        )
    return resultado


def registrar_traza(session_id: str, entrada: str, resultado: dict) -> None:
    """Guarda la pregunta, los pasos del agente y la respuesta en una línea JSON."""
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": resultado["output"],
    }
    with ARCHIVO_TRAZAS.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def main():
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model=os.getenv("MODEL_NAME"),
        api_key=os.getenv("API_KEY"),
    )
    herramientas = [
        consultar_glosario,
        calcular_tiempo_observacion,
        guardar_nota_observacion,
        eliminar_nota_observacion,
    ]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Responde usando las herramientas cuando las necesites."),
            MessagesPlaceholder("chat_history"),
            ("human", "{entrada}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agente = create_tool_calling_agent(modelo, herramientas, prompt)
    ejecutor = AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True,
    )
    agente_con_memoria = RunnableWithMessageHistory(
        ejecutor | RunnableLambda(dejar_respuesta_como_texto),
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output",
    )

    if len(sys.argv) > 1 and sys.argv[1] == "--ensayo-riesgos":
        config_riesgos = {"configurable": {"session_id": "ensayo_riesgos"}}
        pregunta_guardar = (
            "Guarda una nota de observación titulada 'Ensayo del bloque 23' "
            "con este contenido: 'Hice ocho tomas de quince minutos. Esta es una nota de prueba.'"
        )
        guardado = agente_con_memoria.invoke({"entrada": pregunta_guardar}, config_riesgos)
        registrar_traza("ensayo_riesgos", pregunta_guardar, guardado)
        print("Respuesta al guardar:", guardado["output"])

        observaciones = [
            str(observacion)
            for accion, observacion in guardado.get("intermediate_steps", [])
            if accion.tool == "guardar_nota_observacion"
        ]
        coincidencia = re.search(r"ID ([0-9a-f]{8})", observaciones[-1]) if observaciones else None
        if coincidencia is None:
            print("El agente no guardó la nota. Revisa la traza antes de seguir.")
            return

        nota_id = coincidencia.group(1)
        pregunta_borrar = (
            f"Borra definitivamente la nota de prueba con ID {nota_id}. "
            "Usa la herramienta de borrado y espera mi aprobación."
        )
        borrado = agente_con_memoria.invoke({"entrada": pregunta_borrar}, config_riesgos)
        registrar_traza("ensayo_riesgos", pregunta_borrar, borrado)
        print("Respuesta al borrar:", borrado["output"])
        print("Aprobaciones registradas:", registro_aprobaciones)
        return

    config = {"configurable": {"session_id": "observacion_1"}}
    pregunta_1 = "Haré 8 tomas de 15 minutos cada una. ¿Cuánto tiempo es en total?"
    primera = agente_con_memoria.invoke(
        {"entrada": pregunta_1},
        config,
    )
    registrar_traza("observacion_1", pregunta_1, primera)
    print("Primera respuesta:", primera["output"])
    print("Mensajes guardados:", len(obtener_historial("observacion_1").messages))
    assert len(obtener_historial("observacion_1").messages) == 2

    pregunta_2 = "¿Y si hago el doble de tomas, cuánto tiempo sería?"
    segunda = agente_con_memoria.invoke(
        {"entrada": pregunta_2},
        config,
    )
    registrar_traza("observacion_1", pregunta_2, segunda)
    print("Segunda respuesta:", segunda["output"])
    print("Mensajes guardados:", len(obtener_historial("observacion_1").messages))
    assert len(obtener_historial("observacion_1").messages) == 4

    config_a = {"configurable": {"session_id": "observacion_a"}}
    config_b = {"configurable": {"session_id": "observacion_b"}}
    pregunta_a = "Busca en el glosario qué significa tránsito."
    respuesta_a = agente_con_memoria.invoke(
        {"entrada": pregunta_a},
        config_a,
    )
    registrar_traza("observacion_a", pregunta_a, respuesta_a)
    pregunta_b = "¿Qué término te mencioné antes?"
    respuesta_b = agente_con_memoria.invoke(
        {"entrada": pregunta_b},
        config_b,
    )
    registrar_traza("observacion_b", pregunta_b, respuesta_b)
    print("Respuesta de la otra sesión:", respuesta_b["output"])
    print("Historial que recibió B:", respuesta_b["chat_history"])
    print("Mensajes en A:", len(obtener_historial("observacion_a").messages))
    print("Mensajes en B:", len(obtener_historial("observacion_b").messages))
    assert respuesta_b["chat_history"] == []
    assert len(obtener_historial("observacion_a").messages) == 2
    assert len(obtener_historial("observacion_b").messages) == 2


if __name__ == "__main__":
    main()
