# Ensayo funcional del Gate 2

Fecha: 24 de noviembre de 2026.

Corrí `python ensayo_gate2.py` con dos fragmentos de nuestro corpus: el de los reintentos del cliente y el de la clave rechazada. Para esta prueba usé embeddings y respuestas simulados. El índice quedó en memoria; no modifiqué `vectorstore/` ni llamé a Gemini.

## Qué comprobé

- Se indexaron dos documentos. El recuperador devolvió objetos `Document` y el filtro del Bloque 31 leyó `page_content` sin errores. Ambos documentos limpios llegaron al prompt.
- El contexto enviado al modelo simulado incluyó el texto y la fuente de cada fragmento. La primera respuesta citó `cliente_reintento.py` y la segunda, `src/consumir_gemini.py`, con un número que coincidía con el fragmento recuperado. La prueba falla si falta ese fragmento en el prompt o si la cita señala otra fuente. Cada consulta tuvo un `trace_id` distinto en sus eventos. Al terminar, el valor volvió a `None`.
- En otra colección, el único documento tenía una instrucción sospechosa. El filtro lo descartó, quedó registrado `sin_contexto_confiable` y el flujo respondió que no había información suficiente. La prueba falla si intenta llamar al modelo en ese caso.
- Los logs de este ensayo guardaron conteos y longitudes, no el texto de las preguntas ni el contenido de los documentos. Para comprobar el registro de consumo pasé cifras fijas de prueba: 180 tokens de entrada y 22 de salida. El evento lleva `simulado: true`; esas cifras no son consumo real ni costo de Gemini.

## Lo que encontré

En nuestro filtro no apareció el desacople `contenido`/`page_content` del ejemplo de la guía: ya usa la interfaz real de LangChain. Sí faltaba probar el camino en que no queda ningún documento limpio. Lo agregué a este ensayo, sin presentarlo todavía como una corrección del servicio final.

En la primera revisión vimos otro problema: el prompt pedía citas como `[1]`, pero el ensayo aceptaba nombres de archivo que ya venían escritos en las respuestas simuladas, aunque el modelo no recibiera esos nombres. Corregí el ensayo para que el prompt incluya texto y fuente, y para que la cita numérica y el archivo coincidan con lo recuperado.

Este ensayo comprobó que las etapas se conectaban. La corrida posterior con el índice persistido y Gemini, junto con la revisión de los cuatro criterios obligatorios, quedó registrada en `docs/entrega_gate2.md`.
