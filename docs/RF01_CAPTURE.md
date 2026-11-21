# Implementación RF-01 — Captura de proyectos y solicitudes

**Estado:** tablas, políticas RLS y bucket de evidencias aplicados a Supabase; endpoints y frontend incluidos en la rama de desarrollo. Pendientes las pruebas E2E locales con credenciales reales.

## Contratos de API

Autenticación: token Supabase Auth como Bearer, rol cliente.

- GET /api/v1/capture/clientes
- POST /api/v1/capture/clientes: nombre_empresa, ciudad
- GET /api/v1/capture/proyectos
- POST /api/v1/capture/proyectos: cliente_id, nombre_proyecto, area_m2, tipo_superficie, condicion, ambiente, color_requerido, fecha_requerida
- GET /api/v1/capture/solicitudes
- POST /api/v1/capture/solicitudes: proyecto_id, descripcion_libre
- GET /api/v1/capture/solicitudes/{id}/evidencias
- POST /api/v1/capture/solicitudes/{id}/evidencias: multipart archivo JPG/PNG, máximo 5 MB.

## Seguridad

- Propietario vinculado a auth.uid() y policies SELECT/INSERT.
- El cliente solo ve recursos suyos. No hay actualización arbitraria de estado.
- Evidencias en bucket privado colorlink-evidencias, ruta uid/solicitud/uuid.ext.
- Fotos registradas con metadatos; sin URL pública.
- Un cliente tiene por ahora **una sola empresa** (restricción unique), configurable en una versión futura si el backlog lo exige.
- La captura actual no incluye descarga autenticada ni previsualización de evidencias. Eso queda pendiente.

## Caso de prueba manual

1. Registrarse/iniciar sesión como cliente.
2. Crear empresa Constructora Horizonte, Medellín.
3. Crear proyecto Fachada edificio residencial, 85 m2, concreto, humedad y fisuras, exterior, gris, fecha futura.
4. Radicar descripción de al menos 10 caracteres.
5. Subir imagen JPG o PNG de menos de 5 MB.
6. Cerrar sesión e ingresar de nuevo: proyecto, solicitud y metadatos deben persistir.
7. Verificar en Supabase que se generaron registros vinculados; comprobar políticas de propietario con una segunda cuenta cliente.

El registro y persistencia de solicitudes no implica todavía procesamiento por IA ni presupuestos. No afirmar que los 15 pasos estén listos.
