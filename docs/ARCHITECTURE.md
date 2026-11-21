# Arquitectura inicial

\`\`\`text
Navegador
   |
Streamlit (frontend, sin acceso a claves privadas)
   |
   | HTTPS / JSON
   v
FastAPI (validación, operaciones y autorización)
   |                    |
   |                    +--> Supabase Auth (verificación de sesión)
   |                    |
   +--------------------+--> PostgreSQL + RLS (Supabase)
   |
   +--> Gemini (futuro: clasificación supervisada)
   +--> n8n (futuro: workflows y avisos)
   +--> Almacenamiento de evidencias (futuro)
\`\`\`

## Implementado en la rama inicial
- FastAPI y endpoint de salud.
- Login delegado a Supabase Auth (contraseña no almacenada localmente).
- Verificación de token mediante Supabase Auth y consulta de perfil mediante RLS.
- Esquema de perfiles, creación automática de perfil cliente y roles controlados.
- Streamlit con inicio de sesión y vista de identidad/rol validado.
- Docker Compose y pruebas unitarias mínimas.

## Pendiente
- Políticas completas RBAC aplicadas a los módulos de negocio.
- Catálogo de productos, inventario y modelos de negocio.
- Motor técnico, cálculo, Gemini, automatizaciones, despachos, calidad, reportes.
- Pruebas de integración con credenciales reales y pruebas E2E.
