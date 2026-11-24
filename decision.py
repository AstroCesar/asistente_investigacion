"""Aplica el método del Bloque 30 al clasificador de nuestro asistente."""

RESPUESTAS = {
    "informacion_cambia_seguido": False,  # Las tres intenciones siguen siendo las mismas.
    "problema_de_formato_o_tono": False,  # Fallaron 2 de 20 respuestas; el umbral es 3.
    "dataset_grande_y_de_calidad": False,  # Hay 12 ejemplos, menos de 200.
    "presupuesto_limitado_o_iterar_rapido": False,  # No hay plazo de un día ni límite de 2 intentos confirmado.
    "necesita_multiples_variantes": False,  # Por ahora hay un solo clasificador.
}


def recomendar_estrategia(respuestas: dict[str, bool]) -> tuple[dict[str, int], list[str]]:
    puntos = {"RAG": 0, "Fine-tuning completo": 0, "PEFT": 0}
    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2

    maximo = max(puntos.values())
    ganadoras = [tecnica for tecnica, valor in puntos.items() if valor == maximo]
    return puntos, ganadoras


def main() -> None:
    puntos, ganadoras = recomendar_estrategia(RESPUESTAS)
    print("Puntajes de nuestro caso:", puntos)
    print("Candidatas empatadas:", ganadoras)

    # Cambio solo el criterio que más se acercó al umbral: 2 fallos de formato de 20.
    variante = RESPUESTAS.copy()
    variante["problema_de_formato_o_tono"] = True
    puntos_variante, ganadoras_variante = recomendar_estrategia(variante)
    print("Si ese criterio cambiara a True:", puntos_variante)
    print("Candidatas en ese caso:", ganadoras_variante)

if __name__ == "__main__":
    main()
