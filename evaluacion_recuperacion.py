"""Mide la recuperación real del corpus del asistente, sin cambiar el índice."""

import sys
from datetime import date
from pathlib import Path

from indexar_corpus import DIRECTORIO_INDICE, cargar_vectorstore


# Etiquetas hechas leyendo el corpus, antes de mirar los resultados de esta evaluación.
CASOS_EVALUACION = [
    {"pregunta": "¿Qué hace el cliente si Gemini no responde?", "ids_relevantes": {"doc0"}},
    {"pregunta": "¿Cómo cambia la espera entre reintentos?", "ids_relevantes": {"doc0"}},
    {"pregunta": "¿Qué pasa si Gemini rechaza la clave de API?", "ids_relevantes": {"doc1"}},
    {"pregunta": "¿Se vuelve a intentar una petición rechazada por la clave?", "ids_relevantes": {"doc1"}},
    {"pregunta": "¿Cómo estima el cliente el costo de una respuesta?", "ids_relevantes": {"doc2"}},
    {"pregunta": "¿El cliente suma el costo a la sesión?", "ids_relevantes": {"doc2"}},
    {"pregunta": "¿Qué términos de astronomía conoce el glosario?", "ids_relevantes": {"doc3"}},
    {"pregunta": "¿Cómo calcula el agente el tiempo de observación?", "ids_relevantes": {"doc4"}},
    {"pregunta": "¿Qué hace el glosario si no encuentra un término?", "ids_relevantes": {"doc3"}},
    {"pregunta": "¿Por qué brilla el Sol?", "ids_relevantes": set()},
]


def precision_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float:
    if not ids_recuperados:
        return 0.0
    acertados = [identificador for identificador in ids_recuperados if identificador in ids_relevantes]
    return len(acertados) / len(ids_recuperados)


def recall_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float | None:
    if not ids_relevantes:
        return None
    acertados = [identificador for identificador in ids_recuperados if identificador in ids_relevantes]
    return len(acertados) / len(ids_relevantes)


def promediar(valores) -> float:
    validos = [valor for valor in valores if valor is not None]
    return sum(validos) / len(validos) if validos else 0.0


def evaluar_recuperacion(retriever, casos, k=3):
    resultados = []
    for caso in casos:
        chunks = retriever.invoke(caso["pregunta"])
        ids_recuperados = [chunk.id for chunk in chunks][:k]
        resultados.append({
            "pregunta": caso["pregunta"],
            "precision": precision_at_k(ids_recuperados, caso["ids_relevantes"]),
            "recall": recall_at_k(ids_recuperados, caso["ids_relevantes"]),
        })
    return (
        resultados,
        promediar(resultado["precision"] for resultado in resultados),
        promediar(resultado["recall"] for resultado in resultados),
    )


def mostrar_casos():
    print("Preguntas y textos relevantes, marcados antes de evaluar:\n")
    for caso in CASOS_EVALUACION:
        print(caso["pregunta"], "->", caso["ids_relevantes"])
    print("\nLa pregunta sobre el Sol no tiene respuesta en este corpus.")


def guardar_resultados(resultados, precision_promedio, recall_promedio, k):
    nombre = "resultados_evaluacion.txt" if k == 3 else f"resultados_evaluacion_k{k}.txt"
    destino = Path(__file__).with_name(nombre)
    with destino.open("w", encoding="utf-8") as archivo:
        archivo.write(f"Fecha: {date.today()}\n")
        archivo.write(f"Configuración: k={k}, chunk_size=200, chunk_overlap=30\n\n")
        for resultado in resultados:
            recall = "n/a" if resultado["recall"] is None else f"{resultado['recall']:.2f}"
            archivo.write(f"{resultado['precision']:.2f}  {recall}  {resultado['pregunta']}\n")
        archivo.write(
            f"\npromedio -> precisión: {precision_promedio:.3f}  recall: {recall_promedio:.3f}\n"
        )
    print(f"Resultados guardados en {destino.name}")


def main():
    if sys.argv[1:] == ["--vista-previa"]:
        mostrar_casos()
        return
    if sys.argv[1:] not in ([], ["5"]):
        raise SystemExit("Uso: python evaluacion_recuperacion.py [--vista-previa | 5]")
    k = 5 if sys.argv[1:] == ["5"] else 3

    if not (DIRECTORIO_INDICE / "chroma.sqlite3").is_file():
        raise SystemExit("No encuentro el índice guardado en vectorstore/.")
    indice = cargar_vectorstore(DIRECTORIO_INDICE)
    ids_indice = set(indice.get()["ids"])
    if not ids_indice:
        raise SystemExit("El índice está vacío.")
    if any(not caso["ids_relevantes"] <= ids_indice for caso in CASOS_EVALUACION):
        raise SystemExit("Hay etiquetas que no corresponden a los IDs del índice.")

    retriever = indice.as_retriever(search_kwargs={"k": k})
    resultados, precision_promedio, recall_promedio = evaluar_recuperacion(
        retriever, CASOS_EVALUACION, k=k
    )
    print(f"Evaluación real con k={k} y {len(CASOS_EVALUACION)} preguntas:\n")
    for resultado in resultados:
        recall = "n/a" if resultado["recall"] is None else f"{resultado['recall']:.2f}"
        print(f"{resultado['precision']:.2f}  {recall}  {resultado['pregunta']}")
    print(f"\npromedio -> precisión: {precision_promedio:.3f}  recall: {recall_promedio:.3f}")
    guardar_resultados(resultados, precision_promedio, recall_promedio, k)


if __name__ == "__main__":
    main()
