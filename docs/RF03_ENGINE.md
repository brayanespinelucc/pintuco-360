# RF-03 — Motor técnico determinístico

## Implementado

- Catálogo técnico persistente en Supabase con lectura autenticada y protección RLS.
- Motor de cálculo Python con `Decimal`, independiente de Gemini.
- Compatibilidad inicial superficie/ambiente; si hay humedad, fisuras o alerta de IA se marca revisión humana.
- Persistencia de cada cálculo y sus variables originales.
- Endpoint GET `/api/v1/tecnico/catalogo`.
- Endpoint POST `/api/v1/tecnico/solicitudes/{id}/calcular`, con cuerpo `{"producto_id": "UUID"}`.
- Endpoint GET `/api/v1/tecnico/solicitudes/{id}/calculos`.
- Pestaña "Cálculo técnico" en Streamlit.

## Fórmula y ejemplo académico

Cuando el rendimiento se expresa en m² por litro **por mano**:

- Litros teóricos = área × manos ÷ rendimiento por mano.
- Litros con desperdicio = litros teóricos × (1 + desperdicio% ÷ 100).
- Envases = techo(litros con desperdicio ÷ litros por envase).
- Litros comerciales = envases × litros por envase.

Ejemplo de prueba, no ficha técnica de Pintuco:

- Área: 85,00 m².
- Rendimiento hipotético: 10 m²/L por mano.
- Manos: 2.
- Desperdicio hipotético: 15 %.
- Envase hipotético: 4 L.
- Resultado teórico: 17 L; con desperdicio: 19,55 L; 5 envases = 20 L.

## Restricciones y tareas pendientes

Los parámetros técnicos introducidos como demostración **NO son oficiales** y no deben usarse para comprar, cotizar ni aplicar pintura.

Falta cargar fichas técnicas reales verificadas, modelar sistemas de preparación y productos complementarios, múltiples presentaciones y optimización de envases, bandeja de revisión técnica y autorización final.

Los registros `calculos_materiales` tienen políticas RLS de propiedad, pero actualmente un usuario autenticado puede insertar directamente un registro con valores arbitrarios usando la API de Supabase. Antes de producción se debe encapsular la escritura en una función transaccional de confianza o un backend con acceso restrictivo, y añadir auditoría.

## Prueba en el Mac

1. Detener el Docker Compose actual con Control+C.
2. Ejecutar `git pull origin feat/base-plataforma-pintuco360`.
3. Ejecutar `docker compose up --build`.
4. Iniciar sesión en `http://localhost:8501` y entrar a "Cálculo técnico".
5. Seleccionar la solicitud de Constructora Horizonte y el producto DEMOSTRATIVO.
6. Pulsar "Calcular cantidades". Verificar los 19,55 L, cinco envases de 4 L y el bloqueo de revisión humana.
7. Recargar y comprobar el historial persistente en Supabase.
