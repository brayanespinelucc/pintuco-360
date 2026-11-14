# RF-02 — Clasificación con Google Gemini

## Alcance

La etapa 3 de la imagen y el RF-02 del SRS de COLORLINK incluyen convertir las entradas no estructuradas (texto e imágenes) a una clasificación JSON. **La IA NO calcula pintura, rendimientos, precios, presupuestos ni existencias.**

### Implementado en código
- POST \`/api/v1/ia/solicitudes/{id}/analizar\` (consentimiento explícito obligatorio).
- GET \`/api/v1/ia/solicitudes/{id}/analisis\`.
- Aislamiento de propiedad y permisos mediante JWT + RLS para \`public.analisis_ia\`.
- Descarga temporal de hasta dos fotos del bucket privado con el JWT del propietario.
- Solicitud a Google Gemini API \`generateContent\`, con respuesta JSON controlada y validación mediante Pydantic.
- Detección conservadora de necesidad de revisión humana con patologías como humedad y fisuras.
- Persistencia de cada clasificación como registro inmutable con fecha, modelo y número de imágenes.
- Interfaz de ejecución y visualización en Streamlit.

### Para activar
1. Abre https://aistudio.google.com/apikey y crea una clave para Gemini (no la compartas en chat o GitHub).
2. En el archivo \`.env\` **local**, configura \`GEMINI_API_KEY=<tu_clave>\` y \`GEMINI_MODEL=gemini-2.5-flash\`.
3. Ejecuta \`git pull origin feat/base-plataforma-pintuco360\` y \`docker compose up --build\`.
4. Abre \`http://localhost:8501\`, inicia sesión y selecciona **Análisis con Gemini**.
5. Selecciona una solicitud, autoriza el envío y analiza. Revisa el JSON guardado.

### Límites
- No hay integración real probada hasta que se configure la clave y se ejecute el flujo.
- Requiere conectividad a Gemini y una cuota disponible. El proveedor puede cobrar según tu plan.
- No se evalúa clínicamente ni técnicamente la validez de las observaciones del modelo; requieren inspección especializada cuando aplique.
- No se cambia el estado de la solicitud automáticamente: la orquestación de etapas, aprobación, motor técnico y auditoría integral están pendientes.
- La inserción de análisis está limitada por RLS, pero no queda protegida contra un titular de token que inserte directamente filas propias fuera del backend. Endurecer la procedencia de los informes mediante una credencial de servidor o RPC interna antes de uso productivo.
- Hasta dos imágenes JPG/PNG por análisis (5MB cada una), siguiendo los límites de entrada inline.
- Al enviar información a Gemini, los datos se transmiten a un tercero: se exige consentimiento explícito en la interfaz.

## Referencias
- https://ai.google.dev/gemini-api/docs/generate-content/image-understanding
- https://ai.google.dev/gemini-api/docs/migrate-to-interactions
