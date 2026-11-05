from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from chain_tres_pasos import construir_cadena


def test_la_salida_de_cada_paso_llega_al_siguiente():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="WASP-39 b. Luz de la estrella durante el tránsito. CO2."),
        AIMessage(content="Observación: señal en el espectro. Interpretación: CO2."),
        AIMessage(
            content="Objeto: WASP-39 b\nEvidencia: señal en el espectro\n"
            "Interpretación: dióxido de carbono"
        ),
    ]

    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"texto": "Nota de astronomía para probar la cadena."})

    assert modelo_falso.call_count == 3
    assert "Luz de la estrella" in modelo_falso.call_args_list[1].args[0].to_string()
    assert "Observación: señal" in modelo_falso.call_args_list[2].args[0].to_string()
    assert "Interpretación: dióxido de carbono" in resultado
