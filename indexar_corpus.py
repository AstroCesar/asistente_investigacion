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
DIRECTORIO_INDICE = Path(__file__).with_name("vectorstore")
NOMBRE_COLECCION = "asistente_investigacion"


def preparar_chunks():
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
    return splitter.create_documents(CORPUS)


def main():
    chunks = preparar_chunks()
    print(f"Corpus: {len(CORPUS)} documentos. Después del corte: {len(chunks)} chunks.")
    for numero, chunk in enumerate(chunks, 1):
        print(f"{numero}. ({len(chunk.page_content)} caracteres) {chunk.page_content}")

    if "--vista-previa" in sys.argv:
        print("Vista previa: todavía no se calcularon embeddings.")
        return

    load_dotenv()
    clave = os.getenv("API_KEY")
    if not clave:
        raise SystemExit("Falta API_KEY en el archivo .env.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=clave,
    )
    try:
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=NOMBRE_COLECCION,
            persist_directory=str(DIRECTORIO_INDICE),
        )
    except Exception as error:
        print("No pude indexar el corpus:", type(error).__name__)
        print("Detalle técnico:", error)
        raise SystemExit(1)
    print(f"Indexados {len(chunks)} chunks en {DIRECTORIO_INDICE.name}/")


if __name__ == "__main__":
    main()
