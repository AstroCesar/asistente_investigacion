import logging
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI


logger = logging.getLogger(__name__)


def responder_queja_de_respaldo(datos):
    logger.error("Falló la respuesta a la queja. Se usó el respaldo.")
    return (
        "Lamento el problema con el asistente. Intenta repetir la consulta "
        "más tarde y guarda el mensaje de error, si aparece."
    )


respuesta_generica = RunnableLambda(responder_queja_de_respaldo)


def construir_paso_clasificacion(modelo):
    plantilla = PromptTemplate.from_template(
        "Clasifica este mensaje sobre el uso del asistente de investigación "
        "en una sola palabra: pregunta, queja o sugerencia. "
        "Responde solo con esa palabra.\n\n{mensaje}"
    )
    return plantilla | modelo | StrOutputParser() | (lambda texto: texto.strip().lower())


def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()
    rutas = RunnableBranch(
        (lambda datos: datos["categoria"] == "queja", cadena_queja),
        (lambda datos: datos["categoria"] == "sugerencia", cadena_sugerencia),
        cadena_pregunta,
    )
    return RunnablePassthrough.assign(categoria=paso_clasificacion) | rutas


def construir_cadena_queja_segura(cadena_queja):
    return cadena_queja.with_fallbacks([respuesta_generica])


def construir_enrutamiento(modelo):
    cadena_pregunta = (
        PromptTemplate.from_template(
            "Responde esta pregunta sobre el uso del asistente de forma clara. "
            "Por ahora se usa desde la terminal con python main.py y una "
            "pregunta entre comillas. Aún no lee PDF ni tiene interfaz gráfica. "
            "No inventes funciones que todavía no tiene.\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )
    cadena_queja = (
        PromptTemplate.from_template(
            "Responde a esta queja sobre el asistente. Reconoce el problema "
            "y sugiere un primer paso útil, sin prometer que ya quedó "
            "solucionado.\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )
    cadena_queja_segura = construir_cadena_queja_segura(cadena_queja)
    cadena_sugerencia = (
        PromptTemplate.from_template(
            "Agradece esta sugerencia para el asistente y explica brevemente "
            "que se puede considerar más adelante. No digas que ya está "
            "implementada ni que quedó registrada automáticamente.\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )
    return construir_cadena_con_enrutamiento(
        construir_paso_clasificacion(modelo),
        cadena_queja_segura,
        cadena_sugerencia,
        cadena_pregunta,
    )


def procesar_mensaje_seguro(cadena, mensaje):
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception as error:
        logger.error("Error procesando mensaje: %s", error)
        return "No pudimos procesar tu mensaje en este momento. Intenta más tarde."


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model=os.getenv("MODEL_NAME"), api_key=os.getenv("API_KEY")
    )
    cadena = construir_enrutamiento(modelo)
    mensajes = [
        "¿Cómo hago una pregunta al asistente desde la terminal?",
        "El asistente tarda mucho en responder cuando hago una consulta.",
        "Me gustaría que el asistente pudiera leer archivos PDF.",
    ]
    for mensaje in mensajes:
        print("\nMensaje:", mensaje)
        print("Respuesta:", procesar_mensaje_seguro(cadena, mensaje))
