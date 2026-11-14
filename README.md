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
