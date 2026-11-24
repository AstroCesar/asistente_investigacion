"""Ordena riesgos concretos del prototipo actual del asistente."""


def puntaje_riesgo(probabilidad: int, impacto: int) -> int:
    return probabilidad * impacto


def categoria_riesgo(puntaje: int) -> str:
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad: int, impacto: int) -> bool:
    actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto),
        (probabilidad - 1, impacto),
        (probabilidad, impacto + 1),
        (probabilidad, impacto - 1),
    ]
    return any(
        categoria_riesgo(puntaje_riesgo(p, i)) != actual
        for p, i in vecinos
        if 1 <= p <= 5 and 1 <= i <= 5
    )


MIS_RIESGOS = [
    {
        # El agente puede pedir este borrado; hay aprobación, pero una equivocación perdería la nota.
        "riesgo": "Borrar por error una nota de observación local",
        "probabilidad": 2, "impacto": 5,
        "mitigacion": "Aprobación en consola antes de eliminar_nota_observacion (Bloque 23)",
    },
    {
        # El corpus actual es fijo, por eso la probabilidad es menor que en uno abierto a usuarios.
        "riesgo": "Instrucciones falsas dentro de un documento recuperado",
        "probabilidad": 2, "impacto": 4,
        "mitigacion": "Filtro, roles y contexto delimitado probados en logging_rag.py (Bloque 31); aún no conectados al recuperador real",
    },
    {
        # Hoy las preguntas son de prueba; registro_rag.py y las trazas viejas guardan texto completo.
        "riesgo": "Guardar una pregunta con datos personales en trazas antiguas",
        "probabilidad": 2, "impacto": 4,
        "mitigacion": "El logger nuevo guarda longitud y conteos (Bloque 31); falta cambiar los registros antiguos que aún guardan la pregunta",
    },
    {
        # Ya probamos una pregunta fuera del corpus; el prompt puede fallar en otras.
        "riesgo": "Responder un dato astronómico que el corpus no respalda",
        "probabilidad": 2, "impacto": 3,
        "mitigacion": "Prompt con citas y orden de admitir información insuficiente, probado con una pregunta fuera del corpus (Bloque 26)",
    },
    {
        # El índice persiste, pero no se actualiza solo cuando cambia el corpus del código.
        "riesgo": "Consultar un índice que no incluye un cambio reciente del corpus",
        "probabilidad": 3, "impacto": 2,
        "mitigacion": "Reindexación manual con indexar_corpus.py y verificación al reabrirlo (Bloque 24); no hay actualización automática",
    },
]

# La única fila alta de este prototipo ya tiene un control humano en el código.
PUNTOS_SUPERVISION = {
    "Borrar por error una nota de observación local": (
        "esperar_aprobacion en agente_con_herramientas.py pide s/n antes de borrar "
        "y rechaza si no hay respuesta (Bloque 23)"
    ),
}


def main() -> None:
    riesgos = [dict(riesgo) for riesgo in MIS_RIESGOS]
    for riesgo in riesgos:
        assert 1 <= riesgo["probabilidad"] <= 5 and 1 <= riesgo["impacto"] <= 5
        assert riesgo["mitigacion"]
        riesgo["puntaje"] = puntaje_riesgo(riesgo["probabilidad"], riesgo["impacto"])
        riesgo["categoria"] = categoria_riesgo(riesgo["puntaje"])
        riesgo["al_limite"] = esta_en_el_limite(riesgo["probabilidad"], riesgo["impacto"])

    print("PASO 3: matriz de riesgos del prototipo actual")
    for riesgo in sorted(riesgos, key=lambda r: -r["puntaje"]):
        marca = "[AL LIMITE]" if riesgo["al_limite"] else ""
        print(f"{riesgo['categoria']:8} ({riesgo['puntaje']:2}) - {riesgo['riesgo']} {marca}")
        print("  mitigación:", riesgo["mitigacion"])
        if riesgo["categoria"] in {"ALTO", "CRITICO"}:
            supervision = PUNTOS_SUPERVISION.get(riesgo["riesgo"])
            assert supervision, f"falta supervisión para: {riesgo['riesgo']}"
            print("  supervisión:", supervision)
        if riesgo["al_limite"]:
            print("  revisar la estimación con otra persona")

    assert len(riesgos) >= 5
    assert any(r["categoria"] in {"ALTO", "CRITICO"} for r in riesgos)


if __name__ == "__main__":
    main()
