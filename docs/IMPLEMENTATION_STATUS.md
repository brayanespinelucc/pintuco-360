# Registro de avance

## Fase 1 — Base técnica inicial

| Componente | Estado | Evidencia |
|---|---|---|
| API de salud | Implementado; prueba automatizada incluida | /api/v1/health y tests/test_health.py |
| Estructura FastAPI | Implementado | backend/ |
| Frontend Streamlit | Implementado (pantalla de acceso) | frontend/app.py |
| Login Supabase | Código de integración implementado; falta prueba real de inicio de sesión | /api/v1/auth/login |
| Consulta de perfil/rol | Código implementado; falta prueba autenticada | /api/v1/auth/me |
| Tabla de perfiles / RLS | **Migración aplicada a Supabase** y consultas SQL de estructura verificadas | database/migrations/0001_profiles.sql, migración 20261114045505 |
| Función de perfil automático | Trigger creado en \`auth.users\`; función en esquema \`private\` | private.create_profile_for_new_user |
| Supabase Security Advisors | Sin avisos en la revisión inicial (2026-11-13 hora Colombia) | Inspección del proyecto |
| Desarrollo con Docker | Configuración escrita; pendiente validación en entorno Docker | compose.yaml |
| Reglas RBAC completas | Pendiente | — |
| 15 etapas operativas | Pendiente | docs/REQUIREMENTS.md |
| Integración Gemini | Pendiente | — |
| Automatización n8n | Pendiente | — |
| Pruebas E2E | Pendiente | — |

## Estado de base de datos inicial

Proyecto Supabase: \`pintuco-360\` (ID de proyecto \`btkvlpeqjccnjgsqxwix\`). Tabla \`public.profiles\` creada; RLS habilitado con política SELECT por \`auth.uid()\`. Se verificó exactamente una política SELECT, un trigger en \`auth.users\` y una función privada. No se creó ningún usuario de prueba ni se validó todavía un inicio de sesión.

## Próximos pasos
1. Obtener la URL y clave publicable desde Supabase, configurarlas solo en el archivo local \`.env\`.
2. Crear un usuario de prueba desde Authentication > Users de Supabase y probar la autenticación desde Streamlit y FastAPI.
3. Confirmar creación automática de fila en \`public.profiles\` y acceso permitido al propio perfil.
4. Incorporar Product Backlog real y criterios de aceptación por historia.
5. Diseñar esquemas de clientes, proyectos, solicitudes y adjuntos.
6. Implementar primer flujo real: capturar y consultar solicitudes con permisos por cliente.
