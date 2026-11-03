"""Mide coincidencias de palabras entre respuestas y referencias."""

import json
from collections import Counter
from pathlib import Path

from cliente import consultar_modelo
from pipeline_texto import procesar_texto


def contar_coincidencias(
    tokens_referencia: list[str], tokens_respuesta: list[str]
) -> int:
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    return sum((conteo_referencia & conteo_respuesta).values())


def calcular_precision_cobertura_f1(
    tokens_referencia: list[str], tokens_respuesta: list[str]
) -> dict[str, float]:
    if not tokens_referencia or not tokens_respuesta:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    coincidencias = contar_coincidencias(tokens_referencia, tokens_respuesta)
    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)
    f1 = (
        2 * precision * cobertura / (precision + cobertura)
        if precision + cobertura else 0.0
    )
    return {"precision": precision, "cobertura": cobertura, "f1": f1}


def calcular_metricas(texto_referencia: str, texto_respuesta: str) -> dict[str, float]:
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    return calcular_precision_cobertura_f1(tokens_referencia, tokens_respuesta)


def resumir_metricas(resultados: list[dict]) -> dict[str, float]:
    if not resultados:
        return {"precision_promedio": 0.0, "cobertura_promedio": 0.0, "f1_promedio": 0.0}

    n = len(resultados)
    return {
        "precision_promedio": sum(r["precision"] for r in resultados) / n,
        "cobertura_promedio": sum(r["cobertura"] for r in resultados) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }


def main() -> None:
    casos = [
        (
            "¿Qué es un exoplaneta? Responde en una frase.",
            "Un exoplaneta es un planeta que orbita una estrella fuera del Sistema Solar.",
        ),
        (
            "¿Qué es el paralaje estelar? Responde en una frase.",
            "El paralaje estelar permite medir la distancia de estrellas cercanas.",
        ),
        (
            "¿Qué es una supernova? Responde en una frase.",
            "Una supernova es una explosión estelar muy brillante.",
        ),
        ("¿Qué es una estrella? Responde en una frase.", "Una estrella es una esfera de gas que emite luz y calor propios."),
        ("¿Qué es un planeta? Responde en una frase.", "Un planeta es un cuerpo celeste que orbita una estrella."),
        ("¿Cuál es el planeta más grande del Sistema Solar? Responde en una frase.", "Júpiter es el planeta más grande del Sistema Solar."),
        ("¿Cuál es el planeta más cercano al Sol? Responde en una frase.", "Mercurio es el planeta más cercano al Sol."),
        ("¿Qué es la Luna? Responde en una frase.", "La Luna es el satélite natural de la Tierra."),
        ("¿Qué es una galaxia? Responde en una frase.", "Una galaxia es un conjunto de estrellas, gas y polvo unidos por la gravedad."),
        ("¿Qué es la Vía Láctea? Responde en una frase.", "La Vía Láctea es la galaxia que contiene el Sistema Solar."),
        ("¿Qué es un cometa? Responde en una frase.", "Un cometa es un cuerpo de hielo y polvo que orbita el Sol."),
        ("¿Qué es un asteroide? Responde en una frase.", "Un asteroide es un cuerpo rocoso pequeño que orbita el Sol."),
        ("¿Qué es un eclipse solar? Responde en una frase.", "Un eclipse solar ocurre cuando la Luna se interpone entre el Sol y la Tierra."),
        ("¿Qué es un eclipse lunar? Responde en una frase.", "Un eclipse lunar ocurre cuando la Tierra proyecta su sombra sobre la Luna."),
        ("¿Qué es una nebulosa? Responde en una frase.", "Una nebulosa es una nube de gas y polvo en el espacio."),
        ("¿Qué es un agujero negro? Responde en una frase.", "Un agujero negro es una región cuya gravedad impide escapar incluso a la luz."),
        ("¿Qué es una enana blanca? Responde en una frase.", "Una enana blanca es el remanente compacto de una estrella que agotó su combustible."),
        ("¿Qué es un año luz? Responde en una frase.", "Un año luz es la distancia que recorre la luz en un año."),
        ("¿Qué es la rotación de la Tierra? Responde en una frase.", "La rotación es el giro de la Tierra sobre su propio eje."),
        ("¿Qué es la traslación de la Tierra? Responde en una frase.", "La traslación es el movimiento de la Tierra alrededor del Sol."),
    ]

    ruta_resultados = Path(__file__).with_name("resultados_metricas.json")
    resultados = json.loads(ruta_resultados.read_text(encoding="utf-8")) if ruta_resultados.exists() else []
    consultas_guardadas = {r["consulta"] for r in resultados}
    for consulta, referencia in casos:
        if consulta in consultas_guardadas:
            continue
        respuesta = consultar_modelo(consulta)
        metricas = calcular_metricas(referencia, respuesta)
        resultados.append(
            {
                "consulta": consulta,
                "referencia": referencia,
                "respuesta": respuesta,
                **metricas,
            }
        )
        ruta_resultados.write_text(
            json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(
            f"{consulta}  Precisión: {metricas['precision']:.2f}, "
            f"cobertura: {metricas['cobertura']:.2f}, F1: {metricas['f1']:.2f}"
        )

    print(f"{len(resultados)} resultados guardados en {ruta_resultados.name}")

    resumen = resumir_metricas(resultados)
    print(
        f"Promedios: precisión {resumen['precision_promedio']:.2f}, "
        f"cobertura {resumen['cobertura_promedio']:.2f}, "
        f"F1 {resumen['f1_promedio']:.2f}"
    )
    print("Casos ordenados por F1:")
    for caso in sorted(resultados, key=lambda r: r["f1"]):
        print(f"  {caso['f1']:.2f}  {caso['consulta']}")


if __name__ == "__main__":
    main()
