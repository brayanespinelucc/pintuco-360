# Pintuco 360

Plataforma académica de gestión de solicitudes de recubrimientos, asesoría técnica, cotizaciones, inventario, logística, aplicación y calidad. **No es un portal oficial de Pintuco.**

## Estado actual

**Fase 3: RF-02 Clasificación con Gemini.** La aplicación incluye autenticación Supabase, captura de empresas/proyectos/solicitudes, carga privada de imágenes y módulo de clasificación cualitativa con Gemini. La integración Gemini **requiere clave de API local y todavía no ha sido probada contra Google**. **Los demás procesos de la cadena operativa siguen pendientes** (motor técnico, inventario, cotización, logística, calidad y analítica). Consulta [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md). Consulta [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md).

## Tecnologías

- Python, FastAPI y Streamlit.
- Supabase Auth + PostgreSQL (requiere crear un proyecto y ejecutar la migración).
- Próximas integraciones: Gemini, n8n Community y Metabase.
- Docker Compose para ejecución local.

## Inicio rápido (Docker)

1. Copia el ejemplo: \`cp .env.example .env\`.
2. Crea un proyecto Supabase y coloca \`SUPABASE_URL\` y \`SUPABASE_ANON_KEY\` en \`.env\` (la clave **anon/publishable**, nunca \`service_role\`).
3. Las migraciones [0001_profiles.sql](database/migrations/0001_profiles.sql), [0002_rf01_capture.sql](database/migrations/0002_rf01_capture.sql) y [0003_storage_delete_cleanup.sql](database/migrations/0003_storage_delete_cleanup.sql), además de [0004_rf02_ai.sql](database/migrations/0004_rf02_ai.sql) **ya están aplicadas al proyecto Supabase vinculado**. En una instancia nueva, deben aplicarse en este orden una sola vez.
4. Ejecuta \`docker compose up --build\`.
5. Visita \`http://localhost:8501\` (portal) y \`http://localhost:8000/docs\` (API).
6. Crea usuarios de prueba con Supabase Auth. El perfil se crea automáticamente con rol \`cliente\`. Para asignar un rol distinto utiliza el editor SQL con un administrador.

La API puede arrancar sin Supabase configurado para consultar \`/api/v1/health\`, pero el login responderá 503 hasta que configures Supabase.

## Desarrollo local (sin Docker)

\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r frontend/requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn backend.app.main:app --reload --port 8000
# En otra terminal, con el mismo entorno virtual:
streamlit run frontend/app.py
\`\`\`

## Pruebas

\`\`\`bash
pytest -q
python -m compileall -q backend frontend
\`\`\`

## Documentación

- [Instrucciones para el agente de desarrollo](PROMPT_MAESTRO.md)
- [Arquitectura inicial](docs/ARCHITECTURE.md)
- [15 etapas obligatorias](docs/REQUIREMENTS.md)
- [RF-01: formulario y pruebas manuales](docs/RF01_CAPTURE.md)
- [RF-02: integración Gemini y configuración](docs/RF02_GEMINI.md)
- [Estado de implementación](docs/IMPLEMENTATION_STATUS.md)

**Seguridad:** No subas secretos ni datos reales de clientes a Git. Las claves se configuran mediante variables de entorno.

## Activación de Gemini (RF-02)

1. Genera una API key en https://aistudio.google.com/apikey y habilita el proyecto de Google correspondiente.
2. Coloca `GEMINI_API_KEY=...` en el archivo local `.env` sin subirlo al repositorio.
3. Ejecuta `docker compose up --build` y abre `http://localhost:8501`.
4. En la pestaña **Análisis con Gemini**, selecciona tu solicitud, confirma el envío y consulta el JSON persistido.

Las pruebas automatizadas usan dobles de prueba y **no prueban una llamada real a la API de Google**.

**Si Gemini devuelve HTTP 404:** verifica que tu `.env` **local** contenga `GEMINI_MODEL=gemini-3.5-flash-lite` (no basta cambiar `.env.example`), reinicia Docker y vuelve a ejecutar el análisis. Algunas claves recientes no tienen acceso a Gemini 2.5.

## RF-03 — Motor de cálculo

Ya existe la pestaña **Cálculo técnico**, con resultados persistentes y prueba académica de 85 m². El catálogo de ejemplo NO contiene productos ni parámetros oficiales de Pintuco. Consulta [docs/RF03_ENGINE.md](docs/RF03_ENGINE.md).

## RF-04: Disponibilidad de inventario

Ya existe la pestaña Inventario / Disponibilidad: consulta lotes en Supabase, propone cantidades por bodega y etiqueta faltantes para producción. La propuesta NO reserva existencias. Los stocks semilla son académicos, no oficiales de Pintuco. Consulta [docs/RF04_INVENTORY.md](docs/RF04_INVENTORY.md) para el procedimiento de prueba.

## RF-05 — Revisión humana por especialista

El asesor/especialista puede examinar información de la solicitud, Gemini, el motor técnico y los lotes propuestos; aprobar, rechazar o solicitar información/correcciones. Cada decisión queda auditada. La cuenta cliente únicamente consulta sus propias decisiones. **Para probar los permisos hace falta un segundo usuario con rol especialista_tecnico**; no conviertas la cuenta cliente actual. Consulta [docs/RF05_REVIEW.md](docs/RF05_REVIEW.md) para el alta del asesor, SQL de rol y prueba paso a paso. La aprobación no reserva inventario.

## RF-05.1 — Respuesta del cliente
En la pestaña **Revisión técnica**, el cliente puede contestar la solicitud de información del especialista.
La respuesta se almacena y devuelve el caso a `en_revision_tecnica` sin reescribir los datos ni cálculos anteriores.
El especialista puede leer el historial y resolver el caso. [Guía RF-05.1](docs/RF05_REVIEW.md).

## RF-06 — Logística académica

Módulo de operaciones para una cuenta con rol `logistica`: bandeja de solicitudes aprobadas, reserva FEFO de lotes, preparación, despacho simulado, cancelación y auditoría. El cliente ve sus órdenes en **Seguimiento logístico**. El despacho descuenta únicamente envases del catálogo DEMOSTRATIVO guardados en el Supabase académico; no implica movimientos físicos ni uso de existencias reales. Véase [docs/RF06_LOGISTICS.md](docs/RF06_LOGISTICS.md) para crear la tercera cuenta de logística y probarlo.

## RF-07 — Ejecución en campo

El área logística asigna solicitudes despachadas a un usuario `aplicador`; este registra inicio, avances, incidencias, fotografías privadas y finalización al 100 %. La solicitud pasa a `en_calidad` y queda pendiente de RF-08. El cliente consulta únicamente sus propios trabajos en **Aplicación en campo**. Datos y actividades son **académicos y simulados**. [Guía de RF-07](docs/RF07_FIELD_EXECUTION.md).

## RF-08 — Control de calidad académico

Inspector `calidad` revisa las actividades, incidencias y fotografías de RF-07, completa un checklist de cinco criterios y decide **aprobar**, **solicitar corrección** o **rechazar**; dictámenes auditables e inmutables. Ante correcciones, el aplicador puede aportar evidencia y presentar subsanación sin eliminar el dictamen anterior. El cliente consulta el historial en **Control de calidad**. Solo representa una evaluación académica, no certificación oficial. [Guía de RF-08](docs/RF08_QUALITY.md).
