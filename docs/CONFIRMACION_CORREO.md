# Confirmación de correo: COLORLINK en producción

## Causa del error
Los correos de Supabase Auth usaban el Site URL predeterminado
`http://localhost:3000`. En un equipo remoto, localhost apunta al
equipo del usuario y no a COLORLINK. Un enlace con `otp_expired`
ha caducado o ya fue utilizado; no se puede reutilizar.

## Configuración administrativa obligatoria (Supabase Auth)
En **Authentication → URL Configuration** del proyecto
`btkvlpeqjccnjgsqxwix`, establecer:

- **Site URL:** `https://colorlink-web-4jb5.onrender.com`
- **Redirect URLs:** incluir `https://colorlink-web-4jb5.onrender.com/**`

Revisar **Authentication → Email Templates → Confirm signup**:
la plantilla estándar debe utilizar `{{ .ConfirmationURL }}`,
sin URL fija localhost ni enlaces de ejemplo. No desactivar la
confirmación por correo como solución.

## Corrección de código
El backend pasa `redirect_to=${PUBLIC_APP_URL}` a Supabase
en `/auth/v1/signup` y `/auth/v1/resend`. La dirección está
controlada en configuración del servidor; un usuario no puede establecer
un destino externo. En Render, `PUBLIC_APP_URL` puede omitirse si se
usa la URL pública predeterminada de COLORLINK.

El formulario **Crear cuenta → ¿El enlace de confirmación expiró?**
permite solicitar un enlace nuevo con el mismo correo, sin registrarse
de nuevo. El endpoint `POST /api/v1/auth/resend-confirmation`
limita solicitudes por correo y devuelve una respuesta genérica para
evitar revelar si el correo existe. El limitador en memoria aplica por
instancia y no sustituye los límites de Supabase.

## Verificación manual
1. Abrir el portal en Render e intentar registrar una cuenta de prueba
   con una dirección accesible.
2. Revisar el correo nuevo: su enlace de confirmación debe dirigirse
   a Supabase y después redirigir a `https://colorlink-web-4jb5.onrender.com`.
3. Comprobar que después de confirmar se puede iniciar sesión.
4. Si el correo anterior caducó, reenviar desde el portal; usar
   únicamente el enlace más reciente.
5. Repetir desde otro navegador o equipo, no solo localhost.

**Nunca pegar enlaces de confirmación completos ni claves en chats o tickets.**
