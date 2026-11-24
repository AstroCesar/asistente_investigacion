"""Cinco fichas inventadas para probar el RAG antes de usar datos reales."""


CORPUS_PRACTICA = [
    "La ficha de una observación de práctica registra fecha, lugar, objeto elegido y equipo previsto. No contiene resultados científicos.",
    "Si el cielo está nublado durante una práctica, la ficha se marca como sesión pospuesta. No se agregan tomas ni mediciones que no se hicieron.",
    "Para ensayar la observación de un tránsito, se planifican tomas a intervalos regulares y se anota la hora de cada toma. El ejemplo no detecta planetas reales.",
    "Una toma de prueba puede incluir el tiempo de exposición y el filtro utilizado. Esos datos ayudan a comparar imágenes de la misma sesión.",
    "El resumen de práctica distingue el tiempo planificado del tiempo observado. Si la sesión se cancela, el tiempo observado queda en cero.",
]

FUENTE_PRACTICA = "corpus_practica.py"
