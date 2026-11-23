"""Prepara y valida ejemplos del asistente para el Bloque 29. No entrena nada."""

import json
from collections import Counter

from google.genai import types


ejemplos_raw: list[tuple[str, dict[str, str]]] = [
    (
        "¿Qué es un exoplaneta? Explícamelo sencillo.",
        {"intencion": "glosario", "accion_sugerida": "consultar el glosario"},
    ),
    (
        "En la nota aparece la palabra tránsito. ¿Qué significa en astronomía?",
        {"intencion": "glosario", "accion_sugerida": "consultar el glosario"},
    ),
    (
        "No entiendo qué es el paralaje. ¿Me lo puedes aclarar?",
        {"intencion": "glosario", "accion_sugerida": "consultar el glosario"},
    ),
    (
        "Estoy leyendo sobre un exoplaneta y no sé bien a qué se refiere el término.",
        {"intencion": "glosario", "accion_sugerida": "consultar el glosario"},
    ),
    (
        "Si hago 8 tomas de 15 minutos, ¿cuánto tiempo observo en total?",
        {
            "intencion": "calculo_observacion",
            "accion_sugerida": "calcular el tiempo de observación",
        },
    ),
    (
        "Voy a sacar 6 fotos de 20 minutos cada una. ¿Cuántos minutos son?",
        {
            "intencion": "calculo_observacion",
            "accion_sugerida": "calcular el tiempo de observación",
        },
    ),
    (
        "Planeo diez exposiciones de dos minutos y medio. ¿Cuánto dura todo?",
        {
            "intencion": "calculo_observacion",
            "accion_sugerida": "calcular el tiempo de observación",
        },
    ),
    (
        "Anoté cero tomas de 30 minutos. ¿Qué devuelve el cálculo?",
        {
            "intencion": "calculo_observacion",
            "accion_sugerida": "calcular el tiempo de observación",
        },
    ),
    (
        "Según la documentación, ¿qué hace el cliente si Gemini no responde?",
        {"intencion": "consulta_corpus", "accion_sugerida": "buscar en el corpus y citar la fuente"},
    ),
    (
        "¿El cliente vuelve a intentar una petición si la clave de API es inválida?",
        {"intencion": "consulta_corpus", "accion_sugerida": "buscar en el corpus y citar la fuente"},
    ),
    (
        "¿Cómo se estima el costo de una respuesta, según los textos guardados?",
        {"intencion": "consulta_corpus", "accion_sugerida": "buscar en el corpus y citar la fuente"},
    ),
    (
        "Busca dónde dice si el cálculo de observación controla el telescopio.",
        {"intencion": "consulta_corpus", "accion_sugerida": "buscar en el corpus y citar la fuente"},
    ),
]


def construir_ejemplos(datos: list[tuple[str, dict[str, str]]]) -> list[types.TuningExample]:
    return [
        types.TuningExample(text_input=texto, output=json.dumps(salida, ensure_ascii=False))
        for texto, salida in datos
    ]


def chequear_balance(datos: list[tuple[str, dict[str, str]]], clave: str) -> Counter:
    return Counter(salida[clave] for _, salida in datos)


def validar_dataset(
    examples: list[types.TuningExample], claves_esperadas: tuple[str, ...]
) -> list[str]:
    problemas = []
    vistos = set()
    for i, ejemplo in enumerate(examples):
        if not ejemplo.text_input or not ejemplo.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacío")
        if not ejemplo.output or not ejemplo.output.strip():
            problemas.append(f"ejemplo {i}: output vacío")
            continue
        if ejemplo.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ejemplo.text_input)
        try:
            salida = json.loads(ejemplo.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON válido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
    return problemas


def main():
    print("=" * 55)
    print("PASO 1: balance de mi dataset")
    print("=" * 55)
    balance = chequear_balance(ejemplos_raw, "intencion")
    for categoria, cantidad in balance.most_common():
        print(f"{categoria}: {cantidad}")

    print("\n" + "=" * 55)
    print("PASO 2: validar mi dataset")
    print("=" * 55)
    examples = construir_ejemplos(ejemplos_raw)
    claves = ("intencion", "accion_sugerida")
    problemas = validar_dataset(examples, claves)
    print(f"{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for problema in problemas:
        print(" -", problema)

    print("\n" + "=" * 55)
    print("PASO 3: rompo un ejemplo a propósito")
    print("=" * 55)
    examples_rotos = examples.copy()
    examples_rotos[3] = types.TuningExample(
        text_input=examples[3].text_input,
        output="esto no es JSON",
    )
    problemas_rotos = validar_dataset(examples_rotos, claves)
    cantidad = len(problemas_rotos)
    descripcion = "problema encontrado" if cantidad == 1 else "problemas encontrados"
    print(f"{len(examples_rotos)} ejemplos, {cantidad} {descripcion}")
    for problema in problemas_rotos:
        print(" -", problema)


if __name__ == "__main__":
    main()
