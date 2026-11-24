"""Mide las consultas reales del RAG y guarda una línea JSON por consulta.

Ejecuta `python registro_rag.py` para ver los tres pasos de la actividad.
Cada ejecución hace cinco consultas y agrega cinco líneas al archivo de registros.
"""

import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI

from indexar_corpus import DIRECTORIO_INDICE, NOMBRE_COLECCION, crear_embeddings
from recuperacion import PROMPT_TEMPLATE, formatear_contexto
from registro_seguro import sanitizar_costo


ARCHIVO_REGISTROS = Path(__file__).with_name("registros_latencia_costo.jsonl")
PREGUNTAS = [
    "¿Qué hace el cliente si Gemini no responde?",
    "¿Cómo estima el cliente el costo de una respuesta?",
    "¿Qué términos de astronomía conoce el glosario?",
]


@contextmanager
def medir(tiempos, etapa):
    inicio = time.perf_counter()
    try:
        yield
    finally:
        tiempos[etapa] = time.perf_counter() - inicio


def registrar_consulta(pregunta, persist_directory=DIRECTORIO_INDICE, k=3):
    """Hace una consulta real y mide las tres etapas sin reindexar."""
    directorio = Path(persist_directory)
    if not (directorio / "chroma.sqlite3").is_file():
        raise FileNotFoundError(f"No encuentro el índice en {directorio}.")

    load_dotenv()
    modelo = os.getenv("MODEL_NAME")
    clave = os.getenv("API_KEY")
    if not modelo or not clave:
        raise SystemExit("Falta MODEL_NAME o API_KEY en el archivo .env.")

    embeddings = crear_embeddings()
    indice = Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=embeddings,
        persist_directory=str(directorio),
    )
    if indice._collection.count() == 0:
        raise ValueError("El índice está vacío.")
    chat_model = ChatGoogleGenerativeAI(model=modelo, api_key=clave)
    tiempos = {}

    with medir(tiempos, "embed_query"):
        vector = embeddings.embed_query(pregunta)
    with medir(tiempos, "busqueda_vectorial"):
        chunks = indice.similarity_search_by_vector(vector, k=k)

    contexto, _ = formatear_contexto(chunks)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    with medir(tiempos, "generacion"):
        respuesta = chat_model.invoke(prompt)

    return sanitizar_costo({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {etapa: round(segundos * 1000, 2) for etapa, segundos in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": dict(respuesta.usage_metadata) if respuesta.usage_metadata else None,
    })


def guardar_registro(registro):
    registro = sanitizar_costo(registro)
    with ARCHIVO_REGISTROS.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def main():
    if sys.argv[1:] == ["--vista-previa"]:
        print("Primero, tres preguntas distintas con k=3:")
        for numero, pregunta in enumerate(PREGUNTAS, 1):
            print(f"consulta {numero}: {len(pregunta)} caracteres")
        print("Después, la primera pregunta con k=3 y k=6.")
        print("Entre las dos pruebas se agregan cinco consultas reales al archivo.")
        return

    if sys.argv[1:] == ["--tres-consultas"]:
        plan = [(pregunta, 3) for pregunta in PREGUNTAS]
    elif sys.argv[1:] == ["--comparar-k"]:
        plan = [(PREGUNTAS[0], 3), (PREGUNTAS[0], 6)]
    elif sys.argv[1:] in ([], ["--demo-completa"]):
        lineas_antes = (
            len(ARCHIVO_REGISTROS.read_text(encoding="utf-8").splitlines())
            if ARCHIVO_REGISTROS.is_file()
            else 0
        )
        print("=" * 60)
        print("PASO 1: tres consultas distintas con k=3")
        print("=" * 60)
        primeras_consultas = []
        for pregunta in PREGUNTAS:
            registro = registrar_consulta(pregunta, k=3)
            guardar_registro(registro)
            primeras_consultas.append(registro)
        print(json.dumps(primeras_consultas, indent=2, ensure_ascii=False))

        print("\n" + "=" * 60)
        print("PASO 2: misma pregunta con k=3 y k=6")
        print("=" * 60)
        for k in (3, 6):
            registro = registrar_consulta(PREGUNTAS[0], k=k)
            guardar_registro(registro)
            tokens = registro["tokens"] or {}
            print(f"k={k} -> input_tokens: {tokens.get('input_tokens', 'n/a')}")

        print("\n" + "=" * 60)
        print("PASO 3: confirmando el archivo de registros")
        print("=" * 60)
        lineas_despues = len(ARCHIVO_REGISTROS.read_text(encoding="utf-8").splitlines())
        print(
            f"{ARCHIVO_REGISTROS.name} tiene {lineas_despues} líneas "
            f"({lineas_despues - lineas_antes} nuevas, una por consulta)."
        )
        return
    else:
        raise SystemExit(
            "Uso: python registro_rag.py [--vista-previa | --tres-consultas | --comparar-k]"
        )

    for pregunta, k in plan:
        registro = registrar_consulta(pregunta, k=k)
        guardar_registro(registro)
        print(json.dumps(registro, indent=2, ensure_ascii=False))
    print(f"Registros guardados en {ARCHIVO_REGISTROS.name}")


if __name__ == "__main__":
    main()
