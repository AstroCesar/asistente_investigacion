"""Pruebas de la limpieza de texto, sin llamadas a Gemini."""

from pipeline_texto import procesar_texto


def test_procesar_texto_normaliza_mayusculas_y_puntuacion():
    assert procesar_texto("El Cielo, es AZUL!") == ["el", "cielo", "es", "azul"]


def test_procesar_texto_solo_puntuacion_devuelve_lista_vacia():
    assert procesar_texto("¡¡¡...!!!") == []
