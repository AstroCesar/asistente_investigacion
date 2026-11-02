"""Pruebas del cliente sin hacer llamadas reales a Gemini."""

from unittest.mock import Mock, patch

import pytest
from requests.exceptions import HTTPError

import cliente
from cliente_reintento import con_reintento
from src.consumir_gemini import enviar_peticion


@pytest.fixture(autouse=True)
def reiniciar_costo(monkeypatch):
    monkeypatch.setattr(cliente, "costo_total_sesion", 0.0)


def respuesta_con_tokens():
    return {
        "modelVersion": "gemini-3.5-flash-lite",
        "candidates": [{"content": {"parts": [{"text": "Hola"}]}}],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 20,
            "thoughtsTokenCount": 5,
        },
    }


def test_enviar_peticion_credencial_invalida():
    for codigo in (401, 403):
        respuesta = Mock(status_code=codigo)
        respuesta.raise_for_status.side_effect = HTTPError(f"HTTP {codigo}")

        with patch("src.consumir_gemini.requests.post", return_value=respuesta) as post:
            with pytest.raises(ValueError, match="credencial"):
                enviar_peticion("https://ejemplo.test", {}, {})

        post.assert_called_once()


def test_limite_de_uso_se_trata_como_error_temporal():
    respuesta = Mock(status_code=429)
    respuesta.raise_for_status.side_effect = HTTPError("429 Too Many Requests")

    with patch("src.consumir_gemini.requests.post", return_value=respuesta) as post:
        with pytest.raises(TimeoutError, match="HTTP 429"):
            enviar_peticion("https://ejemplo.test", {}, {})

    post.assert_called_once()


def test_respuesta_correcta_devuelve_el_json():
    datos = {"candidates": [{"content": {"parts": [{"text": "Hola"}]}}]}
    respuesta = Mock(status_code=200)
    respuesta.json.return_value = datos

    with patch("src.consumir_gemini.requests.post", return_value=respuesta) as post:
        resultado = enviar_peticion("https://ejemplo.test", {}, {})

    assert resultado == datos
    post.assert_called_once()


def test_peticion_invalida_400_lanza_value_error():
    respuesta = Mock(status_code=400)
    respuesta.raise_for_status.side_effect = HTTPError("400 Bad Request")

    with patch("src.consumir_gemini.requests.post", return_value=respuesta):
        with pytest.raises(ValueError, match="rechazó la petición"):
            enviar_peticion("https://ejemplo.test", {}, {})


def test_error_503_se_trata_como_temporal():
    respuesta = Mock(status_code=503)
    respuesta.raise_for_status.side_effect = HTTPError("503 Unavailable")

    with patch("src.consumir_gemini.requests.post", return_value=respuesta):
        with pytest.raises(TimeoutError, match="problema temporal"):
            enviar_peticion("https://ejemplo.test", {}, {})


def test_con_reintento_reintenta_un_timeout():
    intentos = 0

    def falla_una_vez():
        nonlocal intentos
        intentos += 1
        if intentos == 1:
            raise TimeoutError("temporal")
        return "ok"

    with patch("cliente_reintento.time.sleep") as dormir:
        assert con_reintento(falla_una_vez) == "ok"

    assert intentos == 2
    dormir.assert_called_once()


def test_con_reintento_agota_intentos_y_propaga_error():
    error = TimeoutError("temporal")
    funcion = Mock(side_effect=error)

    with (
        patch("cliente_reintento.time.sleep") as dormir,
        patch("cliente_reintento.random.uniform", side_effect=[0.2, 0.4]),
    ):
        with pytest.raises(TimeoutError) as capturado:
            con_reintento(funcion, intentos=3)

    assert capturado.value is error
    assert funcion.call_count == 3
    assert dormir.call_count == 2
    esperas = [llamada.args[0] for llamada in dormir.call_args_list]
    assert esperas == pytest.approx([2.2, 4.4])


def test_con_reintento_no_reintenta_value_error():
    funcion = Mock(side_effect=ValueError("credencial inválida"))

    with patch("cliente_reintento.time.sleep") as dormir:
        with pytest.raises(ValueError, match="credencial inválida"):
            con_reintento(funcion)

    funcion.assert_called_once()
    dormir.assert_not_called()


def test_registrar_costo_acumula_dos_consultas():
    datos = respuesta_con_tokens()

    assert cliente.registrar_costo(datos) == pytest.approx(0.0000655)
    assert cliente.registrar_costo(datos) == pytest.approx(0.0000655)
    assert cliente.costo_total_sesion == pytest.approx(0.000131)


def test_consultar_modelo_reintenta_y_registra_costo():
    datos = respuesta_con_tokens()

    with (
        patch("cliente.armar_peticion", return_value=("url", {}, {})) as armar,
        patch("cliente.enviar_peticion", side_effect=[TimeoutError("temporal"), datos]) as enviar,
        patch("cliente_reintento.time.sleep") as dormir,
    ):
        texto = cliente.consultar_modelo("Pregunta", "Instrucción")

    assert texto == "Hola"
    armar.assert_called_once_with("Pregunta", "Instrucción")
    assert enviar.call_count == 2
    dormir.assert_called_once()
    assert cliente.costo_total_sesion == pytest.approx(0.0000655)


def test_consultar_modelo_error_final_no_registra_costo():
    with (
        patch("cliente.armar_peticion", return_value=("url", {}, {})),
        patch("cliente.enviar_peticion", side_effect=TimeoutError("temporal")) as enviar,
        patch("cliente_reintento.time.sleep") as dormir,
        patch("cliente.registrar_costo") as costo,
    ):
        with pytest.raises(RuntimeError, match="varios intentos"):
            cliente.consultar_modelo("Pregunta")

    assert enviar.call_count == 3
    assert dormir.call_count == 2
    costo.assert_not_called()


def test_consultar_modelo_propaga_value_error_sin_reintentar():
    error = ValueError("credencial inválida")

    with (
        patch("cliente.armar_peticion", return_value=("url", {}, {})),
        patch("cliente.enviar_peticion", side_effect=error) as enviar,
        patch("cliente_reintento.time.sleep") as dormir,
        patch("cliente.registrar_costo") as costo,
    ):
        with pytest.raises(ValueError) as capturado:
            cliente.consultar_modelo("Pregunta")

    assert capturado.value is error
    enviar.assert_called_once()
    dormir.assert_not_called()
    costo.assert_not_called()
