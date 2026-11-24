"""Consulta el índice persistido del asistente con filtro, citas y traza segura."""

import argparse
import os
import re
import time

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from cliente import (
    MODELO_CON_TARIFA,
    PRECIO_ENTRADA_POR_TOKEN,
    PRECIO_SALIDA_POR_TOKEN,
)
from indexar_corpus import DIRECTORIO_INDICE, cargar_vectorstore, crear_embeddings
from logging_rag import (
    PLANTILLA_USUARIO,
    filtrar_documentos_sospechosos,
    logger,
    trace_id_var,
)
from estado_prompt import leer_prompt_activo
from recuperacion import formatear_contexto
from registro_prompts import huella_prompt


SIN_CONTEXTO = "No tengo información suficiente y verificada para responder esto."


def abrir_indice(directorio=DIRECTORIO_INDICE, embeddings=None):
    """Abre Chroma desde disco; consultar no vuelve a indexar documentos."""
    if not (directorio / "chroma.sqlite3").is_file():
        raise FileNotFoundError(
            f"No encuentro el índice en {directorio}. Corre primero python indexar_corpus.py."
        )
    indice = cargar_vectorstore(directorio, embeddings=embeddings)
    if indice._collection.count() == 0:
        raise ValueError("El índice está vacío. Corre primero python indexar_corpus.py.")
    return indice


def texto_respuesta(contenido) -> str:
    """Acepta contenido de Gemini como texto o bloques de texto."""
    if isinstance(contenido, str):
        return contenido.strip()
    if isinstance(contenido, list):
        return "".join(
            bloque.get("text", "") for bloque in contenido
            if isinstance(bloque, dict) and bloque.get("type") == "text"
        ).strip()
    return ""


def citar_respuesta(texto: str, citas: dict[int, str]) -> tuple[str, list[str]] | None:
    """Comprueba los números citados y muestra el archivo correspondiente."""
    # La lista de archivos la arma el servicio, no el modelo.
    if re.search(r"\bfuentes?\s*:", texto, re.IGNORECASE):
        return None
    numeros = [int(valor) for valor in re.findall(r"\[(\d+)\]", texto)]
    if not numeros or any(numero not in citas for numero in numeros):
        return None
    for cita in re.finditer(r"\[(\d+)\]\s*\(fuente: ([^)]+)\)", texto):
        if cita.group(2) != citas[int(cita.group(1))]:
            return None
    fuentes = sorted({citas[numero] for numero in numeros})
    if any(not fuente or fuente == "desconocida" for fuente in fuentes):
        return None
    detalle = "; ".join(f"[{numero}] {citas[numero]}" for numero in dict.fromkeys(numeros))
    return f"{texto.rstrip()}\nFuentes: {detalle}", fuentes


def estimar_costo(uso: dict | None, nombre_modelo: str | None) -> float | None:
    """Usa solo la tarifa histórica ya documentada para el modelo conocido."""
    if nombre_modelo != MODELO_CON_TARIFA or not uso:
        return None
    entrada, salida = uso.get("input_tokens"), uso.get("output_tokens")
    if not isinstance(entrada, int) or not isinstance(salida, int):
        return None
    return round(
        entrada * PRECIO_ENTRADA_POR_TOKEN + salida * PRECIO_SALIDA_POR_TOKEN, 8
    )


def responder(pregunta: str, indice, embeddings, modelo, *, k: int = 3,
             nombre_modelo: str | None = None) -> dict:
    if not pregunta.strip() or k < 1:
        raise ValueError("Escribe una pregunta y usa k mayor que cero.")
    from uuid import uuid4

    prompt_sistema = leer_prompt_activo()
    token = trace_id_var.set("trace-" + uuid4().hex[:8])
    auditoria = []
    uso_actual = None
    costo_actual = None
    inicio_total = time.perf_counter()

    def total_ms() -> float:
        return round((time.perf_counter() - inicio_total) * 1000, 2)

    def evento(nombre: str, **datos):
        registro = {"evento": nombre, "trace_id": trace_id_var.get(), **datos}
        auditoria.append(registro)
        logger.info(nombre.replace("_", " "), extra={"extra_data": registro})

    def abstenerse(motivo: str) -> dict:
        evento(motivo)
        evento("consulta_completada", tiempo_total_ms=total_ms())
        return {
            "respuesta": SIN_CONTEXTO, "fuentes": [],
            "trace_id": trace_id_var.get(), "auditoria": auditoria,
            "tiempos_ms": tiempos, "tokens": uso_actual,
            "costo_estimado_usd": costo_actual,
        }

    tiempos = {}
    try:
        evento(
            "consulta_recibida", pregunta_len=len(pregunta), k=k,
            prompt_huella=huella_prompt(prompt_sistema),
        )
        inicio = time.perf_counter()
        vector = embeddings.embed_query(pregunta)
        tiempos["embed_query"] = round((time.perf_counter() - inicio) * 1000, 2)

        inicio = time.perf_counter()
        recuperados = indice.similarity_search_by_vector(vector, k=k)
        tiempos["busqueda_vectorial"] = round((time.perf_counter() - inicio) * 1000, 2)
        evento("documentos_recuperados", n=len(recuperados))

        limpios, descartados = filtrar_documentos_sospechosos(recuperados)
        con_fuente = [
            d for d in limpios
            if isinstance(d.metadata.get("fuente"), str)
            and d.metadata["fuente"].strip()
            and d.metadata["fuente"].strip().lower() != "desconocida"
        ]
        evento(
            "contexto_filtrado", n_limpios=len(con_fuente),
            n_descartados=len(descartados), n_sin_fuente=len(limpios) - len(con_fuente),
        )
        if not con_fuente:
            return abstenerse("sin_contexto_confiable")

        contexto, citas = formatear_contexto(con_fuente, incluir_fuente=True)
        mensajes = [
            SystemMessage(content=prompt_sistema),
            HumanMessage(content=PLANTILLA_USUARIO.format(
                contexto=contexto, pregunta=pregunta,
            )),
        ]
        inicio = time.perf_counter()
        mensaje = modelo.invoke(mensajes)
        tiempos["generacion"] = round((time.perf_counter() - inicio) * 1000, 2)
        uso = dict(mensaje.usage_metadata) if mensaje.usage_metadata else None
        uso_actual = uso
        costo_actual = estimar_costo(uso, nombre_modelo)
        evento(
            "consumo_llm",
            input_tokens=uso.get("input_tokens") if uso else None,
            output_tokens=uso.get("output_tokens") if uso else None,
            total_tokens=uso.get("total_tokens") if uso else None,
        )
        texto = texto_respuesta(mensaje.content)
        citada = citar_respuesta(texto, citas)
        if citada is None:
            return abstenerse("respuesta_sin_cita_valida")
        respuesta, fuentes = citada
        evento("consulta_completada", tiempo_total_ms=total_ms())
        return {
            "respuesta": respuesta, "fuentes": fuentes,
            "trace_id": trace_id_var.get(), "auditoria": auditoria,
            "tiempos_ms": tiempos, "tokens": uso, "costo_estimado_usd": costo_actual,
        }
    finally:
        trace_id_var.reset(token)


def main() -> None:
    parser = argparse.ArgumentParser(description="Consulta el RAG del asistente.")
    parser.add_argument(
        "pregunta", nargs="?", default="¿Qué hace el cliente si Gemini no responde?"
    )
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument(
        "--mostrar-supervision", action="store_true",
        help="pide una decisión humana sobre el prompt antes de hacer la consulta",
    )
    args = parser.parse_args()
    load_dotenv()
    clave, nombre_modelo = os.getenv("API_KEY"), os.getenv("MODEL_NAME")
    if not clave or not nombre_modelo:
        raise SystemExit("Falta API_KEY o MODEL_NAME en .env.")
    try:
        embeddings = crear_embeddings()
        indice = abrir_indice(embeddings=embeddings)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from None
    if args.mostrar_supervision:
        from grafo_supervision import ejecutar_interactivo

        print("PASO 1: revisar el cambio de prompt")
        ejecutar_interactivo()
        print("\nPASO 2: consultar con el prompt que quedó activo")
    try:
        modelo = ChatGoogleGenerativeAI(model=nombre_modelo, api_key=clave)
        resultado = responder(
            args.pregunta, indice, embeddings, modelo,
            k=args.k, nombre_modelo=nombre_modelo,
        )
    except Exception as error:
        raise SystemExit(
            f"La consulta no terminó ({type(error).__name__}). Revisa conexión y cuota."
        ) from None
    print("respuesta final:", resultado["respuesta"])
    print("tiempos (ms):", resultado["tiempos_ms"])
    print("tokens:", resultado["tokens"])
    if resultado["costo_estimado_usd"] is not None:
        print(
            "costo estimado (tarifa documentada el 25-10-2026): "
            f"US${resultado['costo_estimado_usd']:.8f}"
        )
    print("Proceso terminado sin errores.")


if __name__ == "__main__":
    main()
