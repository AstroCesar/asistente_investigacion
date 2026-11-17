from indexar_corpus import DIRECTORIO_INDICE, cargar_vectorstore


indice = cargar_vectorstore(DIRECTORIO_INDICE)
print("Chunks recuperados al abrir el índice guardado:", indice._collection.count())
