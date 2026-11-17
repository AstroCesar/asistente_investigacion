import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


CORPUS = [
    "El cliente hace hasta tres intentos si Gemini no responde o devuelve un error temporal. Entre intentos espera cada vez más, con una pequeña variación en el tiempo.",
    "Si Gemini rechaza la clave o la petición, el cliente avisa con un ValueError. No vuelve a intentar la misma solicitud porque así no se arregla el problema.",
    "Después de una respuesta, el cliente lee usageMetadata y estima el costo con los tokens de entrada y salida, si tiene la tarifa de ese modelo. También suma el costo a la sesión.",
    "El agente tiene un glosario corto de astronomía. Por ahora conoce exoplaneta, tránsito y paralaje. Si no encuentra un término, lo dice.",
    "El agente calcula el tiempo de observación multiplicando la cantidad de tomas por los minutos de cada una. Esa cuenta no controla el telescopio ni guarda datos científicos.",
]
METADATAS = [
    {"fuente": "cliente_reintento.py"},
    {"fuente": "src/consumir_gemini.py"},
    {"fuente": "cliente.py"},
    {"fuente": "agente_con_herramientas.py"},
    {"fuente": "agente_con_herramientas.py"},
]
IDS = [f"doc{i}" for i in range(len(CORPUS))]
DIRECTORIO_INDICE = Path(__file__).with_name("vectorstore")
NOMBRE_COLECCION = "asistente_investigacion"


def preparar_chunks(corpus, chunk_size=200, chunk_overlap=30, metadatas=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.create_documents(corpus, metadatas=metadatas)


def crear_embeddings():
    load_dotenv()
    clave = os.getenv("API_KEY")
    if not clave:
        raise SystemExit("Falta API_KEY en el archivo .env.")
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=clave,
    )


def indexar_corpus(
    corpus, persist_directory, chunk_size=200, chunk_overlap=30,
    metadatas=None, ids=None,
):
    """Parte los textos, genera sus embeddings y guarda el índice en disco."""
    chunks = preparar_chunks(corpus, chunk_size, chunk_overlap, metadatas)
    if ids is not None and len(ids) != len(chunks):
        raise ValueError("Debe haber un ID por cada chunk, no solo por documento.")
    embeddings = crear_embeddings()
    try:
        indice = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            ids=ids,
            collection_name=NOMBRE_COLECCION,
            persist_directory=str(persist_directory),
        )
    except Exception as error:
        print("No pude indexar el corpus:", type(error).__name__)
        print("Detalle técnico:", error)
        raise SystemExit(1)
    print(f"Indexados {len(chunks)} chunks en {Path(persist_directory).name}/")
    return indice


def cargar_vectorstore(persist_directory):
    """Abre el índice guardado sin volver a calcular los embeddings."""
    return Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=crear_embeddings(),
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
