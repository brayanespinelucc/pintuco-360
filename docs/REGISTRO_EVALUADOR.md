# Registro autónomo y modo evaluador por roles

## Objetivo

Un visitante puede crear su propia cuenta desde **Crear cuenta**, junto a **Iniciar sesión**. El backend llama a Supabase Auth por medio de su clave pública; no se crean usuarios manualmente. Todos los registros nuevos obtienen **Cliente** mediante el trigger del esquema \`0001_profiles.sql\`. No se aceptan roles en el payload del registro.

La cuenta de un profesor puede obtener **modo evaluador** por una autorización explícita del propietario del proyecto, y después puede cambiar entre:
- Cliente (\`cliente\`).
- Especialista técnico (\`especialista_tecnico\`).
- Logística (\`logistica\`).
- Aplicador (\`aplicador\`).
- Control de calidad (\`calidad\`).

El cambio es **real, no solamente visual**: modifica el rol de la cuenta aprobada en \`public.profiles\` mediante una función protegida y registra el cambio en \`private.evaluator_role_events\`. Todas las rutas de negocio siguen validando el rol y usuario autenticado existentes. La cuenta de otro usuario nunca cambia. Ninguna cuenta puede elegir \`administrador\` desde el selector.

## Registro en COLORLINK

1. Abre **https://colorlink-web-4jb5.onrender.com**.
2. Pulsa **Crear cuenta**.
3. Ingresa nombre, correo propio y contraseña (mínimo 8 caracteres), confírmala y envía.
4. Si Supabase solicita confirmación, abre el correo y confirma el registro. Después regresa al portal e inicia sesión.
5. La cuenta comienza con rol **Cliente**, sin permisos privilegiados.
6. Una vez aprobada como evaluador, cierra sesión y entra nuevamente o recarga el portal. Entonces aparecerá el selector **Modo evaluador** en la barra lateral.

**Configuración importante:** en [Supabase → Authentication → URL Configuration](https://supabase.com/dashboard/project/btkvlpeqjccnjgsqxwix/auth/url-configuration), configura el **Site URL** de producción en \`https://colorlink-web-4jb5.onrender.com\` y permite esa URL como destino. Si este ajuste falta, el enlace de confirmación puede redirigir a localhost aunque la confirmación ocurra. Revisa en **Authentication → Providers → Email** que se acepten nuevas altas. No desactives la confirmación de correo solo para facilitar las pruebas.

Supabase puede limitar la cantidad de correos enviados con su proveedor predeterminado. Si una confirmación no llega, consulta las restricciones de correo o configura un proveedor SMTP autorizado. No desactives protecciones para sortear los límites.

## Autorizar al profesor SIN crearle la cuenta

**Únicamente después de que él se registre** y confirme su correo:

1. Entra a [Supabase → SQL Editor](https://supabase.com/dashboard/project/btkvlpeqjccnjgsqxwix/sql/new).
2. Ejecuta este SQL, reemplazando el correo de ejemplo por el real. No necesitas su contraseña:

\`\`\`sql
insert into private.evaluator_accounts (user_id, enabled)
select u.id, true
from auth.users u
where lower(u.email) = lower('CORREO_DEL_PROFESOR@EJEMPLO.COM')
  and u.email_confirmed_at is not null
on conflict (user_id)
do update set enabled = true;
\`\`\`

Se habilita únicamente el usuario registrado con ese correo y previamente confirmado. Si el resultado muestra **0 filas insertadas**, verifica que la cuenta exista y haya confirmado su dirección. Nunca elimines el filtro de correo para aprobar a todos.

El profesor vuelve al portal, recarga la página y encontrará **Modo evaluador → Probar funcionalidades como** en el menú lateral. Selecciona un rol y pulsa **Cambiar al rol seleccionado**. El sistema actualiza los permisos reales y la pantalla.

## Cómo probar el ciclo completo con una sola cuenta

1. **Cliente:** crear empresa, proyecto y solicitud, adjuntar fotografías, ejecutar análisis/cálculo e inventario.
2. **Especialista técnico:** consultar la solicitud y registrar aprobación u observaciones.
3. **Logística:** reservar lotes, preparar y despachar; en **Aplicadores y campo** seleccionar su propia cuenta de evaluador, que figura como aplicador elegible aun cuando ejerza Logística.
4. **Aplicador:** cambiar a este rol y registrar avance, incidencias y evidencias de la tarea que se autoasignó.
5. **Calidad:** cambiar a Inspector de calidad, revisar y emitir dictamen; si hay corrección, retornar a Aplicador y luego a Calidad.
6. **Cliente:** volver para consultar el historial y cierre de su solicitud.

Las autorizaciones por rol no omiten las dependencias del flujo: no se puede despachar una solicitud no aprobada ni inspeccionar una aplicación que no esté lista.

## Seguridad y datos

- Solo el propietario de Supabase puede crear o revocar autorizaciones, mediante SQL Editor. Los usuarios normales no tienen permisos \`SELECT/INSERT/UPDATE\` sobre las habilitaciones ni \`UPDATE\` sobre \`public.profiles\`.
- La función \`private.cl_evaluator_change_role\` comprueba el usuario autenticado, la autorización activa y el conjunto cerrado de cinco roles. El frontend no puede usar metadatos editables para obtener permisos.
- Los cambios quedan en \`private.evaluator_role_events\`; no se imprimen credenciales, contraseñas ni tokens.
- **Los roles de logística, revisión y calidad pueden acceder a datos de varias solicitudes existentes**, según el diseño actual. Activa el modo evaluador solamente para un profesor de confianza y utiliza **datos sintéticos**, nunca información real de clientes. No es un sistema de impersonación entre usuarios.
- No habilites perfiles evaluadores para visitantes sin verificar su identidad ni para cuentas de uso cotidiano.

### Revocar acceso al finalizar la prueba

Ejecuta el siguiente SQL en una transacción, reemplazando el correo:

\`\`\`sql
begin;
update private.evaluator_accounts
set enabled = false
where user_id in (
  select id from auth.users
  where lower(email) = lower('CORREO_DEL_PROFESOR@EJEMPLO.COM')
);
update public.profiles
set role = 'cliente', updated_at = now()
where id in (
  select id from auth.users
  where lower(email) = lower('CORREO_DEL_PROFESOR@EJEMPLO.COM')
);
commit;
\`\`\`

Esto deshabilita el cambio de roles y devuelve su perfil a Cliente. Cierra sesiones activas si deseas cortar también el acceso inmediatamente.

## Archivos implementados

- \`database/migrations/0012_evaluator_access.sql\` — autorizaciones, auditoría, RPC y autoasignación controlada RF-07.
- \`backend/app/api/auth.py\` — \`POST /api/v1/auth/register\` y \`POST /api/v1/auth/evaluator/role\`.
- \`backend/app/services/supabase_auth.py\` — registro seguro vía Supabase y verificación de autorización.
- \`frontend/app.py\` — pestaña de registro y selector de roles en sidebar para autorizados.
- \`tests/test_auth_self_service.py\` y \`tests/test_frontend_redesign.py\` — pruebas de entrada, rechazo de escalamiento y navegación.

La migración está instalada en el proyecto Supabase vinculado. El funcionamiento completo debe validarse con el correo real del profesor, siguiendo el proceso anterior; no se crean cuentas de terceros durante las pruebas automatizadas.
