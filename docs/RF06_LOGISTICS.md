# RF-06 — Logística y despacho (MVP académico)

## Alcance de esta entrega
- Bandeja de solicitudes aprobadas, usando el cálculo asociado a la aprobación humana de RF-05.
- Reserva de envases por lotes FEFO de RF-04, basada en existencias actuales, sin posibilidad de reserva parcial.
- Operaciones: `reservada` → `preparada` → `despachada`. Cancelación antes del despacho libera reservas.
- Las reservas cambian `reservado_envases` pero NO `existencia_envases` física. El despacho disminuye ambas cantidades en la misma transacción.
- El despacho genera una referencia **simulada** `CL-DEMO-...`; no involucra transportadora ni inventario oficial.
- Registro inmutable de cada evento con actor autenticado, observaciones, fechas y estado anterior/nuevo.
- Reserva idempotente: reintentar la misma reserva activa devuelve la misma orden sin duplicar saldos; preparar/despachar/cancelar también son idempotentes para su estado ya alcanzado.
- Lock de solicitud y lotes con `FOR UPDATE` para evitar reservas concurrentes; selección FEFO por vencimiento y creación/actualización del saldo en una única transacción PostgreSQL.
- Estado de la solicitud pasa a `en_logistica` al reservar, permanece en `en_logistica` al preparar, pasa a `en_aplicacion` al despachar y regresa a `aprobada` al cancelar.
- La orden de un despacho ya realizado no puede cancelarse. Se podrá registrar la operación de campo en RF-07.

## Seguridad
- Las tablas `ordenes_logisticas`, `reservas_lotes_logistica` y `eventos_logisticos` tienen RLS activo y permisos directos revocados a usuarios de API.
- Las operaciones residen en funciones privadas `SECURITY DEFINER` y validan `auth.uid()` contra `public.profiles` (roles `logistica` o `administrador`).
- Las RPC públicas son `SECURITY INVOKER` y ejecutables únicamente por `authenticated`. La función privada se mantiene fuera del esquema Data API.
- Los clientes solo consultan órdenes asociadas a su cuenta. El especialista técnico no puede reservar ni despachar.
- Solo se pueden reservar cálculos **demostrativos** y lotes de bodegas demostrativas. No hay integración con datos oficiales.

## API FastAPI
- `GET /api/v1/logistica/bandeja` — casos aprobados para reservar (rol logística).
- `GET /api/v1/logistica/ordenes` — órdenes y eventos (logística o cliente propietario).
- `POST /api/v1/logistica/solicitudes/{id}/reservar` — `{"observaciones":"Reserva demostrativa para una orden aprobada."}`.
- `POST /api/v1/logistica/ordenes/{id}/accion` — `{"accion":"preparar","observaciones":"Se prepararon los envases del lote."}`; también `despachar`, `cancelar`.

## Primer escenario de prueba
- La solicitud de Constructora Horizonte está **aprobada** y su cálculo aprobado requiere **3 envases**.
- Los dos lotes tienen en total 7 envases disponibles de un producto académico, sin ninguna orden logística real.
- Se espera reservar 3 envases del lote académico Medellín (FEFO): inventario disponible de 7 a 4 envases. La existencia física total permanece en 9, los reservados pasan de 2 a 5.
- Al preparar no se descuentan más existencias. Al despachar, los envases físicos pasan de 9 a 6 y el reservado total vuelve de 5 a 2.
- La solicitud pasa de `aprobada` a `en_logistica` al reservar y después a `en_aplicacion` al despachar.
- Cualquier operación sobre esos lotes es exclusivamente simulada, no representa existencias comerciales ni despacho real de Pintuco.

## Crear una tercera cuenta de prueba para logística
1. No alteres el rol de cliente o especialista ya existentes.
2. En Supabase → Authentication → Users, crea un **tercer usuario** con correo y contraseña propios.
3. En Supabase → SQL Editor, ejecuta (sustituye el correo):
```sql
update public.profiles
set role='logistica'
where id=(select id from auth.users where email='CORREO_DEL_TERCER_USUARIO');
```
4. Comprueba en `public.profiles` que el tercer usuario tenga `role='logistica'`.
5. Detén Docker, ejecuta `git pull origin feat/base-plataforma-pintuco360` y `docker compose up --build`.
6. Inicia sesión con el tercer usuario en `http://localhost:8501`.
7. Verifica que aparezca **RF-06 · Logística académica** y la solicitud aprobada. Pulsa **Reservar envases**.
8. Comprueba la orden `reservada` y sus lotes, después selecciona **Preparar envases**.
9. Cuando el estado sea `preparada`, selecciona **Despachar (simulado)** y comprueba la referencia.
10. Inicia sesión como cliente: en **Seguimiento logístico** aparecerá el estado y el historial de eventos.

## Pruebas realizadas
- SQL en transacciones revertidas, con rol temporal de logística: reserva, reintento idempotente, preparación y despacho. Se verificaron saldos, eventos y rechazo a cancelar despachadas.
- SQL en transacciones revertidas: cancelación libera envases y re-reserva posterior conserva la trazabilidad.
- SQL en transacciones revertidas: inventario insuficiente impide crear reservas parciales y no deja órdenes ni eventos residuales.
- SQL en transacciones revertidas: un cliente no puede ver bandeja logística ni reservar directamente.
- Estas pruebas no modificaron la solicitud real, los roles existentes ni los saldos que ya estaban en Supabase.

## Límites y pasos siguientes
- No se crea orden de transporte real, guía de transportista, facturación ni cotización. La referencia es ficticia.
- No se admite una devolución después de despacho; esa funcionalidad requiere un flujo de reversos controlados.
- No hay integración a ERP ni WMS, ni geolocalización, ni transferencia entre bodegas.
- La actualización de stock opera sobre los registros de prueba existentes en Supabase; **la base sí se modifica al pulsar los botones** y no debe conectarse a stock productivo.
- Faltan pruebas E2E con un tercero en rol logística y análisis de concurrencia con clientes simultáneos.
- RF-07 desarrollará ejecución de campo y seguimiento de aplicación.
