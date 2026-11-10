import agente_con_herramientas as agente


def test_guardar_nota_se_puede_leer(tmp_path, monkeypatch):
    monkeypatch.setattr(agente, "ARCHIVO_NOTAS", tmp_path / "notas.json")

    respuesta = agente.guardar_nota_observacion.invoke({
        "titulo": "Ensayo",
        "contenido": "Ocho tomas de quince minutos.",
    })

    assert "Nota guardada" in respuesta
    assert agente.leer_notas()[0]["contenido"] == "Ocho tomas de quince minutos."


def test_borrar_nota_necesita_aprobacion(tmp_path, monkeypatch):
    monkeypatch.setattr(agente, "ARCHIVO_NOTAS", tmp_path / "notas.json")
    agente.guardar_nota_observacion.invoke({"titulo": "Ensayo", "contenido": "Nota de prueba"})
    nota_id = agente.leer_notas()[0]["id"]

    monkeypatch.setattr(agente, "esperar_aprobacion", lambda mensaje: False)
    rechazo = agente.eliminar_nota_observacion.invoke({"nota_id": nota_id})
    assert "no aprobado" in rechazo
    assert len(agente.leer_notas()) == 1

    monkeypatch.setattr(agente, "esperar_aprobacion", lambda mensaje: True)
    aprobado = agente.eliminar_nota_observacion.invoke({"nota_id": nota_id})
    assert "Borrado aprobado" in aprobado
    assert agente.leer_notas() == []
