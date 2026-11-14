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

## RF-04 — Inventario y disponibilidad
- Bodegas, lotes y evaluaciones con RLS: migración aplicada a Supabase.
- Datos de prueba: 2 bodegas y 2 lotes académicos, 7 envases disponibles en total.
- RPC segura: función privada con comprobación de auth.uid y wrapper de invocador expuesto.
- Propuesta FEFO y derivación a producción si faltan envases: implementadas.
- API y pestaña de Streamlit: implementadas; CI y prueba local pendientes de confirmar.
- La prueba directa de RPC con un usuario autenticado pasó dentro de una transacción revertida.
- No existen reservas ni descuentos de stock, tampoco integración con inventario real de Pintuco.

## RF-05 — Bandeja de revisión humana
- SQL `0007_rf05_human_review.sql`: aplicado en Supabase, funciones de permisos y decisiones auditables.
- Interfaz del asesor y consulta del cliente: implementadas en Streamlit.
- API de bandeja, detalle y resolución: implementada en FastAPI.
- Prueba SQL de cliente denegado y asesor temporal aprobado: superada en transacciones revertidas.
- No hay revisiones reales aún; falta crear una SEGUNDA cuenta con rol especialista_tecnico para la prueba E2E.
- Correcciones de parámetros: se registran propuestas, no se aplican automáticamente.
- Los módulos RF-01 a RF-04 ya superaron pruebas manuales de usuario.

## RF-05.1 — Respuesta del cliente (versión 0.6.1)
- Migración `0008_rf05_client_response.sql` aplicada en Supabase con tabla RLS y RPC privada.
- El cliente puede responder a la última solicitud de información y pasar a `en_revision_tecnica`.
- Nueva API y formulario cliente, historial también visible para el asesor.
- Pruebas SQL transaccionales revertidas: transición de estado, bloqueo de duplicados, denegación a especialista y a otro cliente.
- La solicitud real sigue pendiente de respuesta; prueba desde Streamlit pendiente.
- No se actualizaron proyectos, cálculos ni existencias en la implementación.
