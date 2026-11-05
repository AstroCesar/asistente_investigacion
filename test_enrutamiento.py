from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
)


def crear_cadena(categoria):
    clasificador = MagicMock(return_value=categoria)
    queja = MagicMock(return_value="respuesta de queja")
    sugerencia = MagicMock(return_value="respuesta de sugerencia")
    pregunta = MagicMock(return_value="respuesta de pregunta")
    cadena = construir_cadena_con_enrutamiento(
        clasificador, queja, sugerencia, pregunta
    )
    return cadena, clasificador, queja, sugerencia, pregunta


def test_ruta_queja():
    cadena, clasificador, queja, sugerencia, pregunta = crear_cadena("queja")

    assert cadena.invoke({"mensaje": "Esto tarda mucho"}) == "respuesta de queja"
    assert clasificador.call_count == 1
    assert queja.call_args.args[0]["mensaje"] == "Esto tarda mucho"
    sugerencia.assert_not_called()
    pregunta.assert_not_called()


def test_ruta_sugerencia():
    cadena, _, queja, sugerencia, pregunta = crear_cadena("sugerencia")

    assert cadena.invoke({"mensaje": "Quiero leer PDF"}) == "respuesta de sugerencia"
    assert sugerencia.call_args.args[0]["mensaje"] == "Quiero leer PDF"
    queja.assert_not_called()
    pregunta.assert_not_called()


def test_ruta_pregunta():
    cadena, _, queja, sugerencia, pregunta = crear_cadena("pregunta")

    assert cadena.invoke({"mensaje": "¿Cómo lo uso?"}) == "respuesta de pregunta"
    assert pregunta.call_args.args[0]["mensaje"] == "¿Cómo lo uso?"
    queja.assert_not_called()
    sugerencia.assert_not_called()


def test_categoria_desconocida_va_a_pregunta():
    cadena, _, queja, sugerencia, pregunta = crear_cadena("otra")

    assert cadena.invoke({"mensaje": "¿Cómo lo uso?"}) == "respuesta de pregunta"
    assert pregunta.call_args.args[0]["mensaje"] == "¿Cómo lo uso?"
    queja.assert_not_called()
    sugerencia.assert_not_called()


def test_normaliza_la_categoria_antes_de_elegir_ruta():
    modelo_falso = MagicMock(return_value=AIMessage(content="  QUEJA \n"))

    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": "El programa falló"}
    )

    assert resultado == "queja"
