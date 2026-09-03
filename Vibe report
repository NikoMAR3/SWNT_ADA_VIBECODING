# Vibe Report — EcoTrack

## 1. Cómo configuré las reglas del agente

Antes de escribir una sola línea, creé un archivo `.cursorrules` en la raíz del proyecto para que Cursor tuviera contexto persistente en cada interacción, sin tener que repetir instrucciones en cada prompt. Definí ahí el stack (Python + Streamlit, por rapidez de despliegue), y reglas de estilo: código modular (separar la lógica de cálculo de CO2 de la interfaz, en archivos como `carbon_calculator.py` y `history.py`), comentarios claros en cualquier dato aproximado o ilustrativo, y dependencias mínimas.

También incluí una regla de comportamiento clave: que la IA no me devolviera el problema para corregirlo manualmente, sino que propusiera y aplicara la solución directamente cuando algo fallara. Esto cambió el flujo de trabajo por completo — pasé de revisar código línea por línea a describir síntomas y validar resultados.

Restringí explícitamente cosas que no necesitaba para un MVP: autenticación, bases de datos externas, APIs de terceros para el cálculo de carbono. Sin esas restricciones, la IA tiende a "sobre-construir" — meter infraestructura que no pedí solo porque es una buena práctica genérica.

## 2. Dificultades al delegar el código a la IA

El bug más representativo fue con `st.form`. Al escribir una actividad y hacer clic en "Calcular", la app mostraba "no reconocí ninguna actividad" incluso con texto válido como "Hoy comí carne y viajé 20 km en bus". No diagnostiqué el código yo mismo: le describí el síntoma exacto a la IA (el mensaje de error y cuándo ocurría). La IA identificó que el campo de texto y el botón no estaban dentro de un mismo `st.form`, por lo que Streamlit no garantizaba que el valor del input viajara junto con el evento de clic — el submit se disparaba con el estado anterior (vacío) del campo.

La solución fue envolver la entrada y el botón de envío en un `st.form`, para que ambos se sincronizaran en un solo ciclo de envío. Lo interesante fue el proceso: no toqué el código directamente, solo comuniqué el comportamiento observado. Esto confirmó algo que no esperaba — describir bien un síntoma es una habilidad distinta a depurar, y a veces más difícil, porque hay que resistir la tentación de "adivinar" la causa y simplemente reportar lo que se ve.

Otra dificultad menor fue calibrar cuánto detalle darle a la IA en el prompt inicial. Un prompt muy abierto generaba una app funcional pero genérica; el prompt detallado con ejemplos concretos (como el de "carne + bus") produjo un resultado mucho más cercano a lo que necesitaba desde el primer intento.

## 3. De escribir código a orquestar una visión

Se siente como un cambio de rol más que de herramienta. Dejé de pensar en sintaxis y empecé a pensar en comportamiento esperado, casos límite y experiencia de usuario — que es, en el fondo, el trabajo que más importa en un MVP. Hay una sensación de pérdida de control al no escribir cada línea, pero se compensa con velocidad: en el tiempo que me habría tomado configurar el parsing de texto a mano, ya tenía la app completa corriendo y podía enfocarme en si el "vibe" del producto tenía sentido.

Lo más incómodo fue confiar en el diagnóstico de la IA sin verificarlo línea por línea. Lo que ayudó fue tratar las reglas del `.cursorrules` como una especie de contrato: mientras la IA se mantuviera dentro de esos límites, delegar dejaba de sentirse como perder el control y empezaba a sentirse como dirigir.
