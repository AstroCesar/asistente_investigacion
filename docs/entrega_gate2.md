# Gate 2: revisión antes de entregar

Fecha: 24 de noviembre de 2026. Este es el estado del prototipo local; no lo presento como un servicio desplegado.

## Corrida real de punta a punta

Corrí `python indexar_corpus.py` con el índice de Chroma que ya estaba en disco: **5 fragmentos nuevos, 0 actualizados y 5 sin cambios**. Ahora hay 10 fragmentos. Los cinco nuevos son fichas inventadas de práctica, marcadas como tales en `corpus_practica.py`; no son observaciones reales. Luego aprobé en consola la versión propuesta del prompt con `python grafo_supervision.py` y corrí `python servicio_rag.py "¿Qué hace el cliente si Gemini no responde?"` con Gemini. La respuesta fue:

> Si Gemini no responde o devuelve un error temporal, el cliente hace hasta tres intentos, esperando cada vez más tiempo entre ellos y añadiendo una pequeña variación en el tiempo [1].
>
> Fuentes: [1] cliente_reintento.py

Revisé esa cita contra `cliente_reintento.py`: `con_reintento` usa 3 intentos por defecto, aumenta la espera entre fallos y agrega una variación pequeña. La fuente coincide con lo que respondió el modelo.

En esta corrida con los diez fragmentos, los eventos `consulta_recibida`, `documentos_recuperados`, `contexto_filtrado`, `consumo_llm` y `consulta_completada` compartieron `trace-5ab7e2cf`. Mostraron longitudes, conteos y consumo, sin copiar el texto de la pregunta ni de los documentos. El prompt usado tuvo la huella aprobada `d075246d4ba1`. En una instalación nueva, la versión anterior queda activa hasta que alguien apruebe la propuesta.

| Dato de esta consulta | Valor |
| --- | ---: |
| Embedding de la pregunta | 932,54 ms |
| Búsqueda vectorial | 4,15 ms |
| Generación | 11740,98 ms |
| Tiempo total medido | 12680,16 ms |
| Tokens de entrada / salida | 252 / 36 |
| Costo estimado con la tarifa documentada el 25-10-2026 | US$0,00016560 |

Es una corrida real, no una simulación. El costo es una **estimación con la tarifa que teníamos documentada**, no una factura ni una tarifa que se actualice sola. Los números de tiempo y tokens describen esta consulta; no los tomo como promedio del sistema. El archivo `registros_latencia_costo.jsonl` conserva las cinco corridas reales de la actividad del Bloque 28.

## Cuatro condiciones obligatorias

1. **Pipeline de punta a punta: sí.** El índice persistido se reutilizó y la consulta recuperó, filtró y generó una respuesta real. `test_gate2.py` también prueba altas y cambios incrementales en un índice temporal.
2. **Respuesta con fuente: sí en la corrida real.** El número `[1]` apunta a `cliente_reintento.py` y comprobé el contenido. El servicio rechaza citas ausentes o que no correspondan a los fragmentos recuperados. Si no tiene contexto confiable, se abstiene en vez de inventar una fuente.
3. **Logs sin contenido crudo sensible: sí.** La traza de esta consulta solo muestra metadatos. La prueba de privacidad agrega un correo ficticio y texto privado de prueba para verificar que no aparezcan en los logs. También convertí los registros de los Bloques 23 y 28: conservan herramientas, decisiones, tiempos y tokens, pero no el texto de las preguntas ni las respuestas. Sus scripts ya escriben en ese formato. Las versiones previas de esas pruebas quedaron en una copia local de respaldo, fuera de la entrega.
4. **Supervisión humana ejecutable: sí.** El borrado de notas, que la matriz clasifica como riesgo ALTO, pasa por un grafo con `interrupt()` y `Command(resume=...)`. Las pruebas comprueban pausa, aprobación y rechazo; el borrado solo se ejecuta si la persona aprueba. `python grafo_supervision.py` también pausa una propuesta de prompt y espera una decisión `s/n`. Si se aprueba, guarda localmente la huella de la nueva versión y el RAG la usa en la próxima consulta; si se rechaza, conserva la anterior. El ensayo automático usa archivos temporales y no cambia la configuración local. No hay despliegue a producción.

## Mi estimación de la rúbrica

Son puntajes de revisión propia, no la nota del curso. Uso los pesos que trae la actividad.

| Dimensión | Peso | Mi estimación | Motivo |
| --- | ---: | ---: | --- |
| Pipeline RAG funcional | 25 % | 90 | Índice persistido, cinco altas incrementales sin recalcular las cinco anteriores y una consulta real completa. |
| Recuperación y citación | 15 % | 90 | Medí 15 preguntas: las 14 que tienen respuesta recuperaron su fragmento. La precisión@3 de 0,311 es el máximo posible con un relevante por pregunta y una pregunta sin respuesta; el recall@3 fue 1,000. Revisé una cita contra el archivo. |
| Costo y latencia | 10 % | 85 | Hay medición por etapa, cinco corridas anteriores y esta corrida real documentada; todavía es una muestra chica. |
| Personalización | 15 % | 85 | `decision_personalizacion.md` aplica el método al clasificador propio y explica el empate. La elección de PEFT depende también del análisis de 20 respuestas, porque el método terminó en empate. El Gate pide justificar la decisión, no entrenar el modelo. |
| Observabilidad | 15 % | 90 | El servicio correlaciona eventos con `trace_id`, registra consumo por consulta y no copia texto libre en los logs. También convertí los dos archivos de registros anteriores. |
| Seguridad y gobernanza | 20 % | 85 | Filtro de inyección, versiones de prompt, grafo de aprobación y cinco riesgos propios. El filtro por patrones reduce el riesgo, pero no cubre cualquier ataque. |

Hice la cuenta con la función de la guía y comprobé las cuatro condiciones por separado:

```python
def promedio_ponderado(puntajes, pesos):
    return sum(puntajes[d] * pesos[d] for d in pesos)

pesos = {
    "pipeline_funcional": 0.25, "recuperacion_citacion": 0.15,
    "costo_latencia": 0.10, "personalizacion": 0.15,
    "observabilidad": 0.15, "seguridad_gobernanza": 0.20,
}
mi_puntaje = {
    "pipeline_funcional": 90, "recuperacion_citacion": 90,
    "costo_latencia": 85, "personalizacion": 85,
    "observabilidad": 90, "seguridad_gobernanza": 85,
}
no_compensables = {
    "pipeline_corre_de_punta_a_punta": True,
    "respuestas_citan_fuente": True,
    "logs_sin_contenido_crudo": True,
    "supervision_humana_funciona": True,
}
print(promedio_ponderado(mi_puntaje, pesos))  # 87.75
print(all(no_compensables.values()))         # True
```

**Promedio ponderado estimado: 87,75/100.** Los cuatro requisitos obligatorios dieron `True` en esta revisión. Esta nueva estimación se basa en el corpus ampliado y en las pruebas que pide el Gate; no descuento puntos por no tener usuarios reales, porque esta actividad evalúa un prototipo. Es mi estimación, no la nota del curso. La entrega sigue preparada en Git, sin commit ni push.

## Último chequeo local

Después de la aprobación y la consulta real, pasaron **28 pruebas** del proyecto. `python verificar_entorno.py` encontró la clave, el modelo y el índice sin imprimir valores secretos. Con los archivos actuales preparados para Git hice otra copia limpia en `D:\Proyectos\Curso_Skillnest_IA\_gate2_clean_final_249980b2`: no incluí `.env`, `vectorstore/` ni `prompt_activo.json`. Creé un entorno Python nuevo, instalé `requirements.txt`, corrí `pip check` sin dependencias rotas y repetí las **28 pruebas**: pasaron.

Al principio, esa copia todavía tenía la clave de ejemplo. Google la rechazó y Chroma dejó una colección vacía; corregí `verificar_entorno.py` para que detecte el valor de ejemplo y cuente los fragmentos reales. Después de configurar la clave en la copia, `python indexar_corpus.py` guardó **10 nuevos**, `python verificar_entorno.py` encontró **10 fragmentos** y la consulta real terminó sin errores. Sus eventos compartieron `trace-e86701f1`, usó **244 tokens de entrada y 31 de salida** y respondió con `[1] cliente_reintento.py`. La huella fue `717e37e31b73`, la versión anterior: la aprobación del prompt en el proyecto principal no se copió a esta instalación. No copié la clave del proyecto principal ni subí el archivo `.env` de la prueba.

Repetí la instalación desde cero en `D:\Proyectos\Curso_Skillnest_IA\_gate2_limpia_20261124_182206`. `pip check` no encontró dependencias rotas, pasaron las **28 pruebas**, se indexaron **10 fragmentos nuevos** y el verificador contó **10**. La consulta real terminó sin errores, con la cita `[1] cliente_reintento.py`; los eventos compartieron `trace-d6bf4579`, registraron **244 tokens de entrada y 31 de salida** y usaron la versión anterior del prompt, como corresponde a una copia nueva sin aprobación local.

Después añadí `python servicio_rag.py --mostrar-supervision` para enseñar la aprobación humana y la consulta en la misma corrida. Probé con `s` y `n` usando un modelo y un índice de prueba: ambas decisiones llegaron al prompt usado por el servicio y ambas consultas terminaron con fuente. Con ese cambio, pasaron **30 pruebas**.

También corrí esta opción dos veces con Gemini en la segunda instalación limpia. La primera vez respondí `s`: el grafo informó aprobación y la consulta terminó con la cita `[1] cliente_reintento.py`, usando la huella `d075246d4ba1` y la traza `trace-b459cd78`. La segunda vez respondí `n`: el grafo informó rechazo, mantuvo la misma huella y la consulta terminó con la misma fuente y la traza nueva `trace-6967818b`. En ambas hubo 252 tokens de entrada y 33 de salida. **La huella propuesta ya estaba activa antes de estas dos corridas**, según la primera línea de la consola; por eso esta prueba confirma las ramas de aprobación y rechazo y la consulta integrada, pero no demuestra un cambio de huella provocado por esa aprobación concreta. El cambio de huella tras aprobar ya se había comprobado antes en el proyecto principal, y las pruebas automatizadas comprueban ambos caminos desde un estado inicial separado.
