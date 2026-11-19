# Publicar COLORLINK en internet (Render)

COLORLINK utiliza **Streamlit + FastAPI + Supabase**. Para compartir una URL pública sin dejar encendido el computador, el proyecto incluye un Blueprint de Render con un **único Web Service Docker** en el plan gratuito.

> **Estado:** los archivos de despliegue y tests están en GitHub. El despliegue final y el dominio público requieren que el propietario conecte/autorice su cuenta Render y asigne las variables de entorno. Este documento no significa que ya exista una URL publicada.

## 1. Qué se publica

- **Interfaz Streamlit:** Render publica el puerto \`$PORT\` (por defecto 10000).
- **FastAPI:** escucha solo en \`127.0.0.1:8000\` dentro del contenedor y no tiene un acceso público independiente.
- **Supabase existente:** autenticación, tablas y fotografías privadas continúan allí. No se duplica ni migra la base de datos.
- **Gemini:** conserva su integración si se define \`GEMINI_API_KEY\`.
- **Acceso:** la URL pública mostrará el formulario de inicio de sesión; para consultar los expedientes se necesita una cuenta válida de Supabase.

Archivos:
- \`render.yaml\`: Blueprint listo para seleccionar la rama y lanzar un Web Service gratuito.
- \`Dockerfile.render\`: imagen Docker con dependencias y código de frontend/backend.
- \`deploy/serve.py\`: arranca ambos procesos, atiende señales del proveedor y reinicia el contenedor si un servicio se detiene.
- \`.dockerignore\`: evita incluir \`.env\`, claves y carpetas innecesarias en la imagen.
- \`tests/test_deploy_config.py\`: verifica configuración y exposición de puertos.
- \`.github/workflows/deploy-smoke.yml\`: construye y prueba el contenedor con 512 MB, sin claves reales.

**No se modifica** \`backend/\`, \`frontend/app.py\`, autenticación, endpoints, migraciones ni reglas de negocio.

## 2. Paso a paso en Render

1. Abre [Render Dashboard](https://dashboard.render.com) y entra en tu cuenta.
2. Pulsa **+ New → Blueprint**.
3. Cuando te pida conectar GitHub, autoriza acceso al repositorio privado \`brayanespinelucc/pintuco-360\`. No es necesario hacerlo público.
4. Selecciona **este repositorio**, la rama exacta:
   \`\`\`
   feat/base-plataforma-pintuco360
   \`\`\`
   y el archivo Blueprint \`render.yaml\` de la raíz.
5. Confirma el recurso \`colorlink-web\`, tipo **Web Service**, plan **Free**, Dockerfile \`Dockerfile.render\`. No crees una base de datos en Render.
6. Introduce las variables secretas que Render te solicite:

   | Variable | Valor |
   |---|---|
   | \`SUPABASE_URL\` | Ya está en \`render.yaml\` apuntando al Supabase actual |
   | \`SUPABASE_ANON_KEY\` | Copiar la clave **anon/publishable** desde tu \`.env\` local o Supabase → Settings → API Keys |
   | \`GEMINI_API_KEY\` | Copiar la misma clave de tu \`.env\` local, si usas la función de Gemini |
   | \`GEMINI_MODEL\` | Ya está configurada como \`gemini-3.5-flash-lite\` |
   | \`ENVIRONMENT\` | Ya está configurada como \`production\` |
   | \`APP_NAME\` | Ya está configurada como \`COLORLINK\` |
   | \`API_BASE_URL\` | Se configura automáticamente como \`http://127.0.0.1:8000\` dentro del contenedor |

   **Importante:** no utilices \`service_role\`, no subas tu archivo \`.env\` a GitHub y no pegues ninguna clave en un chat o captura. Si aún no necesitas Gemini, su clave puede configurarse en Render más adelante (el resto de módulos funcionará, pero el análisis IA requerirá la clave).

7. Pulsa **Deploy Blueprint** y revisa el progreso. Cuando el servicio se indique como **Live**, abre la URL HTTPS \`*.onrender.com\` que Render muestra para \`colorlink-web\`.
8. Confirma que aparece el inicio de sesión y entra con uno de tus usuarios de prueba. Comprueba el menú, las solicitudes existentes y el expediente de calidad ya finalizado. El profesor deberá recibir la URL y credenciales de **una cuenta de prueba**, no tu contraseña personal.

## 3. Limitaciones del plan Free

- Render apaga un servicio gratuito que pasa **15 minutos sin tráfico** y lo vuelve a iniciar cuando recibe una visita. El primer acceso puede tardar aproximadamente **un minuto**. Es esperable y no significa que COLORLINK haya dejado de funcionar.
- El plan Free tiene **512 MB** de RAM y recursos limitados; está bien para demostraciones, no para uso comercial de producción.
- El sistema de archivos del contenedor es temporal. COLORLINK ya persiste sus datos e imágenes en Supabase, por lo que no depende del almacenamiento del servidor para los expedientes.
- Comprueba que la cuota mensual de tu cuenta gratuita sea suficiente. No prometas disponibilidad continua para una sustentación importante.

Fuentes oficiales:
- [Render Free](https://render.com/docs/free)
- [Render Blueprints](https://render.com/docs/infrastructure-as-code)
- [Blueprint Spec](https://render.com/docs/blueprint-spec)
- [Streamlit Docker](https://docs.streamlit.io/deploy/tutorials/docker)

## 4. Si la página publica pero no puedes iniciar sesión

- Revisa **Render → colorlink-web → Environment**.
- \`SUPABASE_URL\` debe apuntar a \`https://btkvlpeqjccnjgsqxwix.supabase.co\`.
- \`SUPABASE_ANON_KEY\` debe ser la misma clave válida que usas en local.
- Comprueba que el servicio tenga la versión del repositorio \`feat/base-plataforma-pintuco360\`.
- Abre **Logs** para ver errores. No compartas tokens, claves, contraseñas ni cabeceras de autorización.
- El puerto público es el de Streamlit; **no intentes abrir \`:8000\` en el navegador**. Es interno.
- Si Render muestra que no puede localizar \`render.yaml\`, revisa que seleccionaste la **rama de trabajo**, no \`main\`.

## 5. Cómo compartirlo con el profesor

Envíale el enlace HTTPS que aparece en Render, junto con el usuario de prueba (y su contraseña temporal a través de un canal adecuado). Si el profesor necesita revisar la información de Constructora Horizonte, usa una cuenta de prueba con acceso a esos datos; una cuenta nueva con rol \`cliente\` tendrá su propio ámbito y no verá registros de otra empresa.

Si vas a mostrar cambios en tiempo real, considera que ambos participantes pueden escribir sobre la misma base de datos; crea datos de prueba y limita permisos según el rol.

## 6. Alternativa mediante el conector Render de ChatGPT

Una vez conectes Render a ChatGPT, es posible coordinar el despliegue directamente desde la conversación (con la autorización de tu cuenta). Para el despliegue final, las claves deben permanecer en la configuración protegida de Render, no en el código.

## 7. Publicación no completada aún

La infraestructura está preparada en GitHub, pero no hay prueba de un servicio Render \`Live\` ni de una URL pública hasta que se configure y ejecute el Blueprint en la cuenta del propietario.
