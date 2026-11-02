# Ensayo de rate limit

## Primera tanda — 26 de octubre de 2026

Ejecuté `python -m tests.ensayo_rate_limit` desde la terminal del proyecto, con diez preguntas cortas de astronomía y sin pausas entre ellas.

- Consultas con respuesta: 10 de 10.
- Primer HTTP 429: no apareció en esta tanda.
- Reintentos y esperas: ninguno, porque todas las consultas respondieron directamente.
- Fallos definitivos: 0.
- Costo estimado total: US$0.00097480, calculado con la tarifa de pago de Gemini 3.5 Flash-Lite. No representa necesariamente un cobro en el nivel gratuito.

Esta tanda confirma que el cliente completó las diez consultas y sumó el costo de cada respuesta. Todavía no comprueba el backoff frente a un 429 real; para eso hace falta observar ese error en otro ensayo.

## Segunda tanda — 26 de octubre de 2026

Repetí el mismo comando desde la terminal del proyecto, con otras diez consultas consecutivas.

- Consultas con respuesta: 10 de 10.
- Primer HTTP 429: tampoco apareció.
- Reintentos y esperas: ninguno.
- Fallos definitivos: 0.
- Costo estimado de esta tanda: US$0.00093980 a tarifa de pago.

En las dos tandas hubo 20 respuestas exitosas y ningún 429. La suma estimada de ambas es US$0.00191460 a tarifa de pago. El acumulado que muestra el programa se reinicia en cada ejecución, por eso la segunda tanda empieza otra vez en cero.

## Límite consultado antes de continuar

El panel de Google AI Studio que consulté para el proyecto «My First Project» muestra, en el nivel gratuito, 15 solicitudes por minuto (RPM), 250 000 tokens de entrada por minuto (TPM) y 500 solicitudes por día (RPD) para Gemini 3.5 Flash-Lite. Esos son los límites mostrados por el panel para ese proyecto; conviene confirmar que la clave usada en este ensayo pertenece al mismo proyecto.

Por eso preparé el script para aceptar una cantidad de hasta 20 consultas (`python -m tests.ensayo_rate_limit 20`). Las primeras dos tandas, de diez cada una, quedan documentadas arriba sin atribuirles un 429 que no ocurrió.

## Tercera tanda — 26 de octubre de 2026

Ejecuté `python -m tests.ensayo_rate_limit 20` desde mi terminal, sin pausas entre consultas.

- Consultas iniciadas: 20, numeradas del 0 al 19.
- Primer HTTP 429: consulta 16 (la número 17); las consultas 0 a 15 habían respondido directamente.
- Esperas observadas: consulta 16, 2.0 y 4.3 s; consulta 17, 2.2 y 4.2 s; consulta 18, 2.1 y 4.3 s; consulta 19, 2.1 s.
- Resultado: 17 consultas con respuesta y 3 fallos definitivos (consultas 16, 17 y 18). La consulta 19 respondió después de un reintento.
- Costo estimado total: US$0.00156140 a tarifa de pago. El programa sumó el costo de las 17 consultas que sí devolvieron texto; no añadió costo por las tres que terminaron en `RuntimeError`.

Este ensayo sí mostró el límite real del proveedor y el backoff. Las esperas crecieron aproximadamente de 2 a 4 segundos, con una pequeña variación aleatoria. En tres consultas ese tiempo no bastó para que el límite se liberara antes de agotar los tres intentos.
