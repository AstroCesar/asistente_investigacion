import os
import sys
from pathlib import Path

from langchain_chroma import Chroma

from corpus_practica import CORPUS_PRACTICA, FUENTE_PRACTICA


CORPUS = [
    "El cliente hace hasta tres intentos si Gemini no responde o devuelve un error temporal. Entre intentos espera cada vez más, con una pequeña variación en el tiempo.",
    "Si Gemini rechaza la clave o la petición, el cliente avisa con un ValueError. No vuelve a intentar la misma solicitud porque así no se arregla el problema.",
    "Después de una respuesta, el cliente lee usageMetadata y estima el costo con los tokens de entrada y salida, si tiene la tarifa de ese modelo. También suma el costo a la sesión.",
    "El agente tiene un glosario corto de astronomía. Por ahora conoce exoplaneta, tránsito y paralaje. Si no encuentra un término, lo dice.",
    "El agente calcula el tiempo de observación multiplicando la cantidad de tomas por los minutos de cada una. Esa cuenta no controla el telescopio ni guarda datos científicos.",
] + CORPUS_PRACTICA
METADATAS = [
    {"fuente": "cliente_reintento.py"},
    {"fuente": "src/consumir_gemini.py"},
    {"fuente": "cliente.py"},
    {"fuente": "agente_con_herramientas.py"},
    {"fuente": "agente_con_herramientas.py"},
] + [{"fuente": FUENTE_PRACTICA} for _ in CORPUS_PRACTICA]
IDS = [f"doc{i}" for i in range(len(CORPUS))]
DIRECTORIO_INDICE = Path(__file__).with_name("vectorstore")
NOMBRE_COLECCION = "asistente_investigacion"


def preparar_chunks(corpus, chunk_size=200, chunk_overlap=30, metadatas=None):
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.create_documents(corpus, metadatas=metadatas)


def crear_embeddings():
    from dotenv import dotenv_values, load_dotenv
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    load_dotenv()
    clave = os.getenv("API_KEY")
    if not clave:
        raise SystemExit("Falta API_KEY en el archivo .env.")
    valor_ejemplo = dotenv_values(Path(__file__).with_name(".env.example")).get("API_KEY")
    clave_en_archivo = dotenv_values(Path(__file__).with_name(".env")).get("API_KEY")
    if valor_ejemplo and (clave == valor_ejemplo or clave_en_archivo == valor_ejemplo):
        raise SystemExit("API_KEY todavía tiene el valor de ejemplo. Edita .env antes de indexar.")
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=clave,
    )


def indexar_corpus(
    corpus, persist_directory, chunk_size=200, chunk_overlap=30,
    metadatas=None, ids=None, embeddings=None,
):
    """Guarda chunks nuevos o cambiados sin recalcular los que ya coinciden."""
    chunks = preparar_chunks(corpus, chunk_size, chunk_overlap, metadatas)
    if ids is None:
        ids = [f"chunk-{numero}" for numero in range(len(chunks))]
    if len(ids) != len(chunks):
        raise ValueError("Debe haber un ID por cada chunk, no solo por documento.")
    embeddings = embeddings or crear_embeddings()
    try:
        indice = Chroma(
            collection_name=NOMBRE_COLECCION,
            embedding_function=embeddings,
            persist_directory=str(persist_directory),
        )
        guardados = indice.get(ids=ids, include=["documents", "metadatas"])
        anteriores = {
            identificador: (texto, metadata or {})
            for identificador, texto, metadata in zip(
                guardados["ids"], guardados["documents"], guardados["metadatas"]
            )
        }
        ids_nuevos, chunks_nuevos = [], []
        ids_cambiados, chunks_cambiados = [], []
        for identificador, chunk in zip(ids, chunks):
            previo = anteriores.get(identificador)
            if previo is None:
                ids_nuevos.append(identificador)
                chunks_nuevos.append(chunk)
            elif previo != (chunk.page_content, chunk.metadata):
                ids_cambiados.append(identificador)
                chunks_cambiados.append(chunk)
        if chunks_nuevos:
            indice.add_documents(chunks_nuevos, ids=ids_nuevos)
        if chunks_cambiados:
            # Chroma fusiona metadatos al actualizar. Reemplazamos el registro
            # para que una clave quitada no quede guardada para siempre.
            previos = indice.get(
                ids=ids_cambiados, include=["documents", "metadatas", "embeddings"]
            )
            vectores = embeddings.embed_documents(
                [chunk.page_content for chunk in chunks_cambiados]
            )
            indice._collection.delete(ids=ids_cambiados)
            try:
                indice._collection.add(
                    ids=ids_cambiados,
                    documents=[chunk.page_content for chunk in chunks_cambiados],
                    metadatas=[chunk.metadata or None for chunk in chunks_cambiados],
                    embeddings=vectores,
                )
            except Exception:
                # Si el guardado falla, dejamos el índice como estaba.
                indice._collection.delete(ids=ids_cambiados)
                indice._collection.add(
                    ids=previos["ids"], documents=previos["documents"],
                    metadatas=previos["metadatas"],
                    embeddings=previos["embeddings"].tolist(),
                )
                raise
        nuevos, actualizados = len(chunks_nuevos), len(chunks_cambiados)
    except Exception as error:
        print("No pude indexar el corpus:", type(error).__name__)
        print("Detalle técnico:", error)
        raise SystemExit(1)
    print(
        f"Índice en {Path(persist_directory).name}/: "
        f"{nuevos} nuevos, {actualizados} actualizados, "
        f"{len(chunks) - nuevos - actualizados} sin cambios."
    )
    return indice


def cargar_vectorstore(persist_directory, embeddings=None):
    """Abre el índice guardado sin volver a calcular los embeddings."""
    return Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=embeddings or crear_embeddings(),
        persist_directory=str(persist_directory),
    )


def main():
    chunks = preparar_chunks(CORPUS, metadatas=METADATAS)
    print(f"Corpus: {len(CORPUS)} documentos. Después del corte: {len(chunks)} chunks.")
    for numero, chunk in enumerate(chunks, 1):
        print(f"{numero}. {IDS[numero - 1]} {chunk.metadata['fuente']}: {chunk.page_content}")

    if "--vista-previa" in sys.argv:
        print("Vista previa: todavía no se calcularon embeddings.")
        return

    indexar_corpus(CORPUS, DIRECTORIO_INDICE, metadatas=METADATAS, ids=IDS)


if __name__ == "__main__":
    main()
