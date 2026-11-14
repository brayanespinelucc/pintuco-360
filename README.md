# Pintuco 360

Plataforma académica de gestión de solicitudes de recubrimientos, asesoría técnica, cotizaciones, inventario, logística, aplicación y calidad. **No es un portal oficial de Pintuco.**

## Estado actual

**Fase 1: base técnica inicial.** Esta rama incluye una API FastAPI con endpoint de salud y autenticación contra Supabase Auth, una pantalla de ingreso Streamlit y un esquema de perfiles con roles. **No están implementados todavía los 15 procesos del negocio** ni la integración con Gemini, n8n o inventarios. Consulta [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md).

## Tecnologías

- Python, FastAPI y Streamlit.
- Supabase Auth + PostgreSQL (requiere crear un proyecto y ejecutar la migración).
- Próximas integraciones: Gemini, n8n Community y Metabase.
- Docker Compose para ejecución local.

## Inicio rápido (Docker)

1. Copia el ejemplo: \`cp .env.example .env\`.
2. Crea un proyecto Supabase y coloca \`SUPABASE_URL\` y \`SUPABASE_ANON_KEY\` en \`.env\` (la clave **anon/publishable**, nunca \`service_role\`).
3. Ejecuta [database/migrations/0001_profiles.sql](database/migrations/0001_profiles.sql) en el editor SQL de Supabase.
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
- [Estado de implementación](docs/IMPLEMENTATION_STATUS.md)

**Seguridad:** No subas secretos ni datos reales de clientes a Git. Las claves se configuran mediante variables de entorno.
