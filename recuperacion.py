"""Busca en el corpus guardado y arma un prompt con citas a los archivos."""

import sys
from pathlib import Path

from indexar_corpus import DIRECTORIO_INDICE, cargar_vectorstore


PROMPT_TEMPLATE = """Responde la pregunta usando solo el contexto de abajo. Cita cada dato con el número del fragmento, por ejemplo [1]. Si no hay información suficiente, dilo sin inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


def formatear_contexto(chunks_recuperados, incluir_fuente=False):
    lineas = []
    citas = {}
    for numero, doc in enumerate(chunks_recuperados, 1):
        fuente = doc.metadata.get("fuente", "desconocida")
        if incluir_fuente:
            lineas.append(f"[{numero}] (fuente: {fuente}) {doc.page_content}")
        else:
            lineas.append(f"[{numero}] {doc.page_content}")
        citas[numero] = fuente
    return "\n\n".join(lineas), citas


def construir_prompt(pregunta, persist_directory=DIRECTORIO_INDICE, k=3):
    directorio = Path(persist_directory)
    if not (directorio / "chroma.sqlite3").is_file():
        raise FileNotFoundError(f"No encuentro el índice guardado en {directorio}.")
    indice = cargar_vectorstore(directorio)
    if indice._collection.count() == 0:
        raise ValueError("El índice está vacío.")
    retriever = indice.as_retriever(search_kwargs={"k": k})
    chunks = retriever.invoke(pregunta)
    contexto, citas = formatear_contexto(chunks)
    return PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta), citas


def main():
    preguntas = [
        "¿Qué hace el cliente si Gemini tarda demasiado en responder?",
        "¿Qué términos de astronomía conoce el glosario del agente?",
    ]
    if "--probar-modelo" in sys.argv:
        preguntas = [
            preguntas[0],
            "¿Por qué brilla el Sol?",
        ]

    for pregunta in preguntas:
        prompt, citas = construir_prompt(pregunta)
        print("\nPregunta:", pregunta)
        print("Prompt:\n", prompt, sep="")
        print("Fuentes:", citas)
        if "--probar-modelo" in sys.argv:
            from cliente import consultar_modelo

            print("Respuesta del modelo:", consultar_modelo(prompt))


if __name__ == "__main__":
    main()
