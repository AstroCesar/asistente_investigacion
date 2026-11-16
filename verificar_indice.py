import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from indexar_corpus import DIRECTORIO_INDICE, NOMBRE_COLECCION


load_dotenv()
clave = os.getenv("API_KEY")
if not clave:
    raise SystemExit("Falta API_KEY en el archivo .env.")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    api_key=clave,
)
indice = Chroma(
    collection_name=NOMBRE_COLECCION,
    embedding_function=embeddings,
    persist_directory=str(DIRECTORIO_INDICE),
)
print("Chunks recuperados al abrir el índice guardado:", indice._collection.count())
