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

## RF-06 — Logística académica (v0.7.0)
- Migración 0009_rf06_logistics.sql aplicada a Supabase con reserva FEFO y operaciones transaccionales.
- Tablas de orden, asignación de lotes y eventos con RLS y permisos directos revocados.
- Funciones internas verifican rol logistica/administrador, solicitud aprobada y cálculo aprobado.
- Operaciones: reservar, preparar, despachar o cancelar; reintentos idempotentes; sin reservas parciales.
- Portal de logística y seguimiento del cliente implementados en Streamlit.
- Pruebas SQL temporales con ROLLBACK superadas: reserva, preparación, despacho, cancelación, re-reserva, falta de stock y permiso de cliente.
- Datos reales en Supabase permanecen sin movimientos por parte de las pruebas.
- Falta crear tercera cuenta de prueba logistica y ejecutar escenario E2E del usuario.
- El inventario y las referencias son exclusivamente demostrativos y no hay transportadora ni WMS.

## RF-07 — Ejecución en campo (v0.8.0)
- Migración `0010_rf07_field_execution.sql` aplicada a Supabase, tablas con RLS y RPC privadas verificadas.
- Logística asigna trabajos despachados a rol aplicador; este registra inicio, avance porcentual, incidencia, foto privada y finalización.
- La solicitud pasa a `en_calidad` únicamente al finalizar la aplicación con 100 %.
- Cliente consulta sus propias aplicaciones y evidencias; logística tiene vista operativa. No hay acceso directo a tablas.
- Bucket privado `colorlink-campo` para JPG/PNG de hasta 5 MB, máximo 10 fotos por aplicación.
- SQL en transacciones revertidas: roles simulados, asignación, progreso, incidencia, cierre y foto con autorización storage; confirmado.
- **Prueba E2E local pendiente:** crear cuarta cuenta con rol `aplicador`, asignar desde logística, iniciar desde aplicador.
- RF-08 — inspección y decisión humana de calidad — permanece pendiente.

## RF-08 — Control de calidad (v0.9.0)
- Migración `0011_rf08_quality.sql` aplicada a Supabase; inspecciones auditables, 5 criterios, aprobación/corrección/rechazo.
- Solo calidad/administrador emiten dictámenes; propiedad del cliente y aplicador verificada en RPC; RLS sin acceso directo.
- Un dictamen de corrección reabre el ciclo para subsanación humana sin alterar el progreso 100 % del trabajo terminado.
- Se mantiene un histórico inmutable por número de inspección; la aprobación cambia solicitud a `finalizada`, el rechazo a `rechazada`.
- La bandeja de calidad, el formulario de checklist, la bitácora fotográfica y el seguimiento de cliente están integrados en Streamlit.
- SQL con ROLLBACK verificó aprobación, rechazo, correcciones, reinspección y permisos; el caso real permanece `en_calidad`.
- Prueba de usuario pendiente: crear quinta cuenta de rol `calidad` y ejecutar el primer dictamen.
- Evaluación exclusivamente académica; no hay certificación de obra real.
