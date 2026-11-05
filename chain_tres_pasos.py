import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


FUENTE = (
    "https://science.nasa.gov/missions/webb/"
    "nasas-webb-detects-carbon-dioxide-in-exoplanet-atmosphere/"
)

TEXTO_ENTRADA = (
    "NASA informó que el telescopio James Webb observó a WASP-39 b, un planeta "
    "fuera de nuestro Sistema Solar. Cuando el planeta pasó frente a su "
    "estrella, parte de la luz atravesó su atmósfera. El equipo estudió esa "
    "luz y encontró una señal que interpretó como evidencia de dióxido de "
    "carbono. El resultado ayuda a conocer mejor la atmósfera del planeta."
)


def construir_cadena(modelo):
    plantilla_datos = PromptTemplate.from_template(
        "Lee esta nota de astronomía y saca tres datos: qué objeto se estudió, "
        "qué señal apareció en la medición y cómo interpretó el equipo "
        "esa señal. No te quedes solo en el método usado. "
        "No agregues datos nuevos.\n\n{texto}"
    )
    paso_datos = plantilla_datos | modelo | StrOutputParser()

    plantilla_separacion = PromptTemplate.from_template(
        "Separa estos datos en dos partes. Primero, qué se observó o midió. "
        "Segundo, cómo lo interpretó el equipo. Mantén el nombre del objeto. "
        "No conviertas una interpretación en una observación directa.\n\n{datos}"
    )
    paso_separacion = plantilla_separacion | modelo | StrOutputParser()

    plantilla_ficha = PromptTemplate.from_template(
        "Escribe una ficha breve para alguien que está juntando información "
        "de astronomía. Usa tres líneas: Objeto, Evidencia e Interpretación. "
        "En Evidencia cuenta qué señal se observó en la luz. "
        "En Interpretación explica qué cree el equipo que indica esa señal. "
        "No agregues información que no esté en este texto.\n\n{separacion}"
    )
    paso_ficha = plantilla_ficha | modelo | StrOutputParser()

    return (
        paso_datos
        | (lambda datos: {"datos": datos})
        | paso_separacion
        | (lambda separacion: {"separacion": separacion})
        | paso_ficha
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model=os.getenv("MODEL_NAME"),
        api_key=os.getenv("API_KEY"),
    )
    cadena = construir_cadena(modelo)
    resultado = cadena.invoke({"texto": TEXTO_ENTRADA})
    print("Fuente del texto:", FUENTE)
    print("\nFicha:")
    print(resultado)
