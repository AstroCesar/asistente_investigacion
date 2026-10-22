"""Cuatro tareas breves para probar respuestas JSON del asistente."""

BANCO_DE_PROMPTS = [
    {
        "nombre": "resumir_observacion",
        "system_instruction": (
            "Resume la observación en una frase breve y señala su principal "
            "limitación en otra. Responde solo con un JSON que tenga las claves "
            "'resumen' y 'limitacion'. No agregues información ni presentes como "
            "confirmado algo que el texto describe como posible."
        ),
        "ejemplo_usuario": (
            "Un equipo observó la atmósfera de un exoplaneta durante varios "
            "tránsitos. Encontró una señal que podría corresponder a vapor de "
            "agua, pero los datos tienen mucho ruido y todavía no permiten "
            "confirmarlo."
        ),
        "claves_esperadas": ["resumen", "limitacion"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "resumen": {"type": "STRING"},
                "limitacion": {"type": "STRING"},
            },
            "required": ["resumen", "limitacion"],
        },
    },
    {
        "nombre": "extraer_distancia",
        "system_instruction": (
            "Extrae la distancia indicada en la frase. Responde solo con un JSON "
            "con 'valor' como número y 'unidad' como texto breve."
        ),
        "ejemplo_usuario": "Una estrella está a 12 años luz de la Tierra.",
        "claves_esperadas": ["valor", "unidad"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "valor": {"type": "NUMBER"},
                "unidad": {"type": "STRING"},
            },
            "required": ["valor", "unidad"],
        },
    },
    {
        "nombre": "detectar_certeza",
        "system_instruction": (
            "Indica si la frase presenta el hallazgo como 'confirmado' o 'posible'. "
            "Responde solo con un JSON que tenga la clave 'estado'. "
            "No decidas si el hallazgo es verdadero: clasifica cómo está redactado."
        ),
        "ejemplo_usuario": "Los datos sugieren que podría haber agua en ese planeta.",
        "claves_esperadas": ["estado"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {"estado": {"type": "STRING"}},
            "required": ["estado"],
        },
    },
    {
        "nombre": "comparar_transitos",
        "system_instruction": (
            "Calcula cuántos días pasan entre los tránsitos indicados y "
            "comprueba si todos los intervalos son iguales. Responde solo "
            "con un JSON: 'intervalo_dias' debe ser un número y "
            "'regulares' debe ser true o false. Usa solo las fechas dadas."
        ),
        "ejemplo_usuario": (
            "Caso ficticio: se observaron tránsitos del mismo exoplaneta "
            "en los días 2, 7 y 12. ¿Cuántos días hay entre tránsitos? "
            "¿Son regulares los intervalos?"
        ),
        "claves_esperadas": ["intervalo_dias", "regulares"],
        "valores_esperados": {"intervalo_dias": 5, "regulares": True},
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "intervalo_dias": {"type": "NUMBER"},
                "regulares": {"type": "BOOLEAN"},
            },
            "required": ["intervalo_dias", "regulares"],
        },
    },
]
