# Estado de la implementación

## Fase 1
- FastAPI, Streamlit y login Supabase: prueba local exitosa reportada por el usuario.
- Perfil automático y RLS: comprobados en Supabase.

## RF-01
- Migraciones de clientes, proyectos, solicitudes y evidencias: aplicadas.
- El usuario confirmó que puede registrar empresa y proyecto.
- Supabase registró 1 empresa, 1 proyecto, 1 solicitud y 1 evidencia (verificación 14/11/2026).
- Pendiente: prueba E2E automatizada de aislamiento entre distintas cuentas cliente.

## RF-02
- Migración \`analisis_ia\`: aplicada a Supabase.
- Servicio Gemini y endpoints: código incorporado, pendiente conectar clave.
- Streamlit: pestaña Análisis con Gemini añadida, pendiente prueba local.
- Pruebas básicas: incorporadas, validar en GitHub Actions.
- **No hay una prueba real con Gemini completada** hasta que se configure la API key y se pulse Analizar.
- Riesgo pendiente: registros de IA propios pueden ser forjados por cliente con acceso REST y JWT. Antes de producción mover la escritura a identidad interna verificable del backend.

## RF-03 a RF-08 / etapas operativas
- Pendientes: motor técnico, inventario, excepciones, cotizaciones, logística, aplicación, calidad, analítica y orquestación.

## RF-03 — Cálculos determinísticos

- Migración `0005_rf03_technical_calculations.sql`: aplicada en Supabase; dos tablas con RLS, tres políticas.
- Catálogo: un producto únicamente demostrativo, NO oficial de Pintuco.
- Motor matemático `Decimal`, endpoints FastAPI y pestaña Streamlit: implementados en código.
- Pruebas automáticas: agregadas; estado se confirma en CI.
- Prueba real local con el usuario: **pendiente**.
- Persistencia trazable habilitada. No están implementadas aprobación técnica, inventarios ni cotizaciones.
