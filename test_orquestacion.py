from unittest.mock import MagicMock

from langchain_core.runnables import RunnableLambda

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_cadena_queja_segura,
    procesar_mensaje_seguro,
)


def test_cadena_queja_usa_fallback_ante_fallo_del_modelo(caplog):
    def fallar_a_proposito(datos):
        raise ConnectionError("Error de red simulado")

    cadena_queja_falsa = RunnableLambda(fallar_a_proposito)
    cadena_queja_segura = construir_cadena_queja_segura(cadena_queja_falsa)

    resultado = cadena_queja_segura.invoke({"mensaje": "Esto no funciona"})

    assert "Lamento el problema" in resultado
    assert "Se usó el respaldo" in caplog.text


def test_procesar_mensaje_seguro_no_propaga_excepciones(caplog):
    clasificacion_falsa = MagicMock(side_effect=ConnectionError("simulado"))
    cadena_falsa = construir_cadena_con_enrutamiento(clasificacion_falsa)

    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert "No pudimos procesar" in resultado
    assert "Error procesando mensaje" in caplog.text
