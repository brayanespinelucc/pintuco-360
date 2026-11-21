# RF-07 — Ejecución y seguimiento de la aplicación en campo

## Implementación (versión 0.8.0)
Este módulo corresponde exclusivamente a un **MVP académico** sobre proyectos ficticios. No confirma que se hayan pintado superficies o se hayan ejecutado obras reales.

- **Asignación:** logística asigna una solicitud en `en_aplicacion`, que debe tener orden logística `despachada`, a una cuenta con rol `aplicador`.
- **Inicio:** el aplicador inicia el trabajo asignado. Se registra usuario, fecha y observaciones.
- **Avances:** porcentajes enteros acumulados entre 1 % y 99 %, estrictamente crecientes; no se permiten retrocesos.
- **Incidencias:** observaciones asociadas al trabajo sin alterar porcentaje.
- **Fotografías:** JPG o PNG de hasta 5 MB, máximo diez por trabajo. Se guardan en el bucket **privado** `colorlink-campo`, vinculadas a la bitácora y accesibles solo para roles autorizados.
- **Finalización:** disponible tras registrar al menos un avance; establece 100 %, mueve la aplicación a `pendiente_calidad` y la solicitud a `en_calidad` para revisión humana en RF-08.
- **Cliente:** seguimiento de sus propios trabajos, avances, bitácora, incidencias y fotografías, sin permisos de escritura.
- **Logística:** seguimiento del campo después de la asignación; no puede registrar avances en nombre del aplicador.

## Esquema y estados
`solicitudes.estado`: `en_aplicacion` → `en_calidad`.
`aplicaciones_campo.estado`: `asignada` → `en_ejecucion` → `pendiente_calidad`.
`bitacora_campo`: eventos `asignacion`, `inicio`, `avance`, `incidencia`, `evidencia`, `finalizacion` con autor y marca temporal.
La asignación de cada solicitud/orden es única y los eventos solo pueden registrarse mientras el estado lo permite. No se reabre una ejecución finalizada automáticamente.

## Seguridad
- Tablas `public.aplicaciones_campo` y `public.bitacora_campo` con RLS habilitado y permisos directos al Data API revocados.
- RPC públicas `SECURITY INVOKER` solo `authenticated`; funciones en `private` con `SECURITY DEFINER`, `search_path=''`, comprobación explícita de `auth.uid()` y rol en `public.profiles`.
- El aplicador solo puede modificar aplicaciones donde figura como asignado. El cliente solo recibe información de solicitudes propias.
- Bucket `colorlink-campo` privado. Política de Storage que verifica la carpeta usuario/aplicación y el rol en la base de datos, también para lecturas y eliminaciones. Las imágenes se descargan a través de FastAPI y las reglas de Storage usando el JWT del usuario; no hay URLs públicas permanentes.
- El backend verifica tipo real de imagen, tamaño y longitud de las observaciones, y elimina el objeto recién subido si la inscripción en bitácora falla.
- Los permisos para `calidad` se limitan a la lectura del expediente de campo en este módulo; no hay aprobación de calidad todavía.

## FastAPI
- `GET /api/v1/campo/aplicadores` — catálogo de aplicadores para logística.
- `GET /api/v1/campo/elegibles` — solicitudes despachadas por asignar.
- `GET /api/v1/campo/aplicaciones` — seguimiento según rol y propiedad.
- `POST /api/v1/campo/solicitudes/{id}/asignar` — `{"aplicador_id":"UUID","observaciones":"..."}` (logística).
- `POST /api/v1/campo/aplicaciones/{id}/eventos` — `{ "tipo":"inicio|avance|incidencia|finalizacion", "avance_pct":35, "observaciones":"..." }` (solo aplicador; `avance_pct` debe ser `null` excepto para `avance`).
- `POST /api/v1/campo/aplicaciones/{id}/evidencias` — multipart `archivo` + campo de formulario `observaciones`.
- `GET /api/v1/campo/aplicaciones/{id}/evidencias/{evento_id}/imagen` — imagen privada para cliente dueño, aplicador asignado o rol autorizado.

## Cómo probar el RF-07
### 1. Crear cuarta cuenta — aplicador
1. Abre Supabase Dashboard → **Authentication → Users** y crea una CUARTA cuenta de prueba con correo distinto.
2. En **SQL Editor** ejecuta, sustituyendo el correo:
```sql
update public.profiles
set role = 'aplicador'
where id = (select id from auth.users where email = 'CORREO_DEL_CUARTO_USUARIO');
```
3. Verifica que exista el perfil de la cuarta cuenta con rol `aplicador`; NO alteres las tres cuentas actuales (`cliente`, `especialista_tecnico`, `logistica`).

### 2. Sincronizar la app
```bash
git pull origin feat/base-plataforma-pintuco360
docker compose down
docker compose up --build
```
Abre http://localhost:8501 y verifica que el encabezado indique `Interfaz 0.8.0`.

### 3. Asignación
- Inicia sesión con **logistica**, ve al final de la pantalla y busca **RF-07 · Asignación de trabajos de campo**.
- Debe aparecer la solicitud de Constructora Horizonte que quedó en estado `en_aplicacion` con el despacho `CL-DEMO-...`.
- Elige la nueva cuenta de aplicador; escribe observaciones y pulsa **Asignar al aplicador**.
- Estado esperado del trabajo: `asignada`, avance `0 %`. Esto no modifica inventario ni despacho.

### 4. Ejecución
- Cierra sesión e inicia como **aplicador**. Aparecerá **RF-07 · Ejecución y seguimiento en campo**.
- Pulsa **Registrar inicio**. Nuevo estado: `en_ejecucion`.
- Selecciona **Registrar avance** y registra por ejemplo `35 %` con una descripción.
- Opcional: registra una incidencia sobre humedad y adjunta una fotografía JPG/PNG con texto explicativo.
- Para terminar, selecciona **Finalizar y enviar a calidad**. El progreso quedará `100 %` y la solicitud pasará a `en_calidad`.
- En esta primera prueba es preferible **confirmar primero la asignación y el inicio** antes de ejecutar la finalización, para comprobar cada transición.

### 5. Cliente
- Con la cuenta **cliente**, abre la pestaña **Aplicación en campo**.
- Verifica el aplicador, porcentaje, eventos, incidencia y fotos. Solo puede consultar; no registrar ni modificar.

## Pruebas automáticas y SQL
- SQL transaccional `ROLLBACK`: asignación con rol logística, rechazo de finalización prematura, inicio, avance creciente, rechazo de retroceso, incidencia, cierre al 100 %, cambio a calidad y seguimiento de cliente.
- SQL transaccional `ROLLBACK`: foto metadata en Storage sujeta a políticas privadas, inserción por RPC y lectura de permisos de cliente; todos los registros temporales fueron revertidos.
- Tests API y validación de roles implementados en `tests/test_field.py`, ejecutados en GitHub Actions.

## Límites
- RF-07 es un seguimiento académico, no un parte laboral ni una evidencia certificada de obra.
- No hay agenda de visitas, firma digital, tiempos facturables, geolocalización certificada, consumo real de materiales, corrección offline, ni cierre de calidad. Estos aspectos requieren desarrollos posteriores.
- El estado `en_calidad` representa remisión a RF-08, no aceptación ni finalización definitiva del proyecto.
