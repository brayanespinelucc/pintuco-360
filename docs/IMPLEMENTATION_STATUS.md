# Registro de implementación

## Fase 1: verificada por el usuario
- FastAPI arrancó localmente; documentación /docs accesible.
- Login del usuario Supabase funciona desde Streamlit.
- Migración perfiles, RLS y trigger aplicada y verificada.
- GitHub Actions de fase 1: satisfactorio.

## RF-01: captura
- Esquema SQL para clientes, proyectos, solicitudes y evidencias: **aplicado** en Supabase.
- Cuatro nuevas tablas RLS; ocho políticas de negocio y dos de Storage; bucket privado: **verificados**.
- Endpoints para empresa, proyectos, solicitudes y fotos: **código añadido**, pendientes pruebas E2E.
- Interfaz de cliente con formularios y consulta: **código añadido**, pendiente prueba local por usuario.
- Pruebas API básicas: **añadidas**, pendientes ejecución GitHub Actions.
- Reglas de negocio futuras: Gemini, cálculo, inventario, cotización y logística: **pendientes**.

Consulta docs/RF01_CAPTURE.md para flujos, limitaciones y prueba manual.
