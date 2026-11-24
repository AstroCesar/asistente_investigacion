"""Revisa el entorno y el índice antes de la corrida final del Gate 2."""

import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


PAQUETES = (
    "langchain-core", "langchain-chroma", "chromadb", "langgraph",
    "langchain-google-genai", "langchain-text-splitters", "python-dotenv",
)
DIRECTORIO_INDICE = Path(__file__).with_name("vectorstore")


def main():
    problemas = []
    print("Python:", sys.version.split()[0])
    # Las versiones de requirements.txt se probaron con Python 3.14.
    if sys.version_info < (3, 12):
        problemas.append("usar Python 3.12 o superior con estas versiones fijadas")

    for paquete in PAQUETES:
        try:
            print(f"{paquete}: {version(paquete)}")
        except PackageNotFoundError:
            print(f"{paquete}: FALTA")
            problemas.append(f"instalar {paquete} desde requirements.txt")

    valor_ejemplo = None
    clave_en_archivo = None
    try:
        from dotenv import dotenv_values, load_dotenv
    except ImportError:
        aviso = "instalar python-dotenv desde requirements.txt"
        if aviso not in problemas:
            problemas.append(aviso)
    else:
        load_dotenv()
        valor_ejemplo = dotenv_values(
            Path(__file__).with_name(".env.example")
        ).get("API_KEY")
        clave_en_archivo = dotenv_values(
            Path(__file__).with_name(".env")
        ).get("API_KEY")
    for nombre in ("API_KEY", "MODEL_NAME"):
        valor = os.getenv(nombre)
        es_ejemplo = (
            nombre == "API_KEY" and bool(valor_ejemplo)
            and (valor == valor_ejemplo or clave_en_archivo == valor_ejemplo)
        )
        estado = "valor de ejemplo" if es_ejemplo else "definida" if valor else "FALTA"
        print(f"{nombre}: {estado}")
        if not valor or es_ejemplo:
            problemas.append(f"definir {nombre} en .env")

    archivo_indice = DIRECTORIO_INDICE / "chroma.sqlite3"
    cantidad = 0
    if archivo_indice.is_file() and archivo_indice.stat().st_size > 0:
        try:
            import chromadb
            from indexar_corpus import NOMBRE_COLECCION

            cantidad = chromadb.PersistentClient(
                path=str(DIRECTORIO_INDICE)
            ).get_collection(NOMBRE_COLECCION).count()
        except Exception:
            cantidad = 0
    indice_listo = cantidad > 0
    estado_indice = f"ok ({cantidad} fragmentos)" if indice_listo else "FALTA o está vacío"
    print(f"índice en {DIRECTORIO_INDICE.name}/: {estado_indice}")
    if not indice_listo:
        problemas.append("correr python indexar_corpus.py")

    if problemas:
        print("Pendiente: " + "; ".join(problemas))
        raise SystemExit(1)
    print("Entorno listo para la corrida final.")


if __name__ == "__main__":
    main()
