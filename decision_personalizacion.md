# Decisión de personalización

## 1. El problema
Estamos probando un clasificador separado del agente para distinguir entre consultas al glosario, cálculos de tiempo de observación y búsquedas en el corpus, con una respuesta JSON que tenga `intencion` y `accion_sugerida` coherentes. En 20 mensajes nuevos probados con el mismo prompt, 2 respuestas tuvieron el JSON incompleto y 1 de las 18 respuestas con formato válido eligió la categoría equivocada.

## 2. Resultado del método de decisión
- RAG: 0 puntos
- Fine-tuning completo: 0 puntos
- PEFT: 0 puntos

**Empate entre: RAG, Fine-tuning completo, PEFT.**

Estas fueron mis cinco respuestas al método de la actividad:

Los fallos temporales de conexión no se contaron entre las 20 respuestas del modelo.

- `informacion_cambia_seguido`: **False**. Las tres intenciones que estamos clasificando siguen siendo las mismas; no tengo evidencia de cambios mensuales en ellas.
- `problema_de_formato_o_tono`: **False**. Hubo 2 fallos de formato en 20 respuestas (10 %). El criterio orientativo de la guía empieza en 3 de 20 (15 %). El error de categoría se registra aparte y no lo cuento como fallo de formato.
- `dataset_grande_y_de_calidad`: **False**. Tenemos 12 ejemplos etiquetados, 4 por categoría. Pasaron el validador de estructura del Bloque 29, pero eso no comprueba que todas las etiquetas sean correctas. Tampoco hicimos la revisión de 20 ejemplos al azar que propone la guía: todavía no tenemos 20. Estamos lejos de los 200 ejemplos de ese criterio.
- `presupuesto_limitado_o_iterar_rapido`: **False**. Hoy no necesitamos ver un cambio en menos de un día y no hemos fijado un límite comprobado de dos intentos de entrenamiento.
- `necesita_multiples_variantes`: **False**. Estamos preparando un solo clasificador para este asistente.

## 3. Técnica elegida y por qué
El puntaje no eligió una técnica: las tres quedaron empatadas en cero. **Si tuviéramos que personalizar este clasificador, elegiría PEFT. Hoy no iniciaría el entrenamiento; seguiría probando el prompt.** Con 2 fallos de formato de 20, todavía no alcanzamos el umbral que usamos para justificar ese trabajo, y entrenar exigiría más datos etiquetados, cómputo y tiempo de revisión.

El método no tiene una opción para «seguir sin entrenar» y tampoco puntúa el error de clasificación que vimos en una respuesta válida. La pregunta sobre cambios frecuentes de información aporta poco a este clasificador de tres intenciones fijas. La de presupuesto o rapidez queda en `False` porque no hay urgencia actual ni un límite de entrenamientos confirmado. Por eso uso el puntaje como punto de partida y explico la decisión con esos datos.

PEFT sería mi elección porque toca el comportamiento que queremos mejorar y requiere menos entrenamiento que afinar el modelo completo. RAG ya sirve para consultar información del corpus, pero no corrige por sí mismo la forma del JSON del clasificador. Esto es una decisión para este caso, no un trabajo de tuning ya realizado.

Para comprobar cuánto depende la decisión del dato más cercano al umbral, cambié solo `problema_de_formato_o_tono` de `False` a `True`. El resultado pasó a RAG: 0, fine-tuning completo: 1 y PEFT: 2. Entiendo por qué cambia, pero esa variante es una prueba de sensibilidad; no reemplaza los 2 fallos observados.

## 4. Qué necesitaría para ejecutarla
Hoy tengo **12 ejemplos etiquetados**. Para alcanzar el umbral orientativo de **200 ejemplos** que usa esta actividad al hablar de un dataset grande, faltarían **188**. Si cada uno tomara 5 minutos, como en el ejemplo de la guía, serían **940 minutos (15 horas y 40 minutos)** de etiquetado; es una estimación, no tiempo medido en nuestro proyecto. Los 200 ejemplos no son un mínimo oficial para PEFT ni una razón para entrenar ahora. Antes de preparar un adapter revisaría las etiquetas, sumaría ejemplos de las tres categorías y repetiría una prueba con mensajes nuevos. Si después de eso el problema persiste, recién tendría sentido estimar el costo y el tiempo de un trabajo de tuning.
