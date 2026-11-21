# COLORLINK — Rediseño UX/UI Premium (Frontend)

**Alcance:** exclusivamente la capa de presentación Streamlit. No se modificaron los endpoints, modelos, autenticación, roles, migraciones, operaciones, Supabase ni servicios de FastAPI.

## A. Diagnóstico fundamentado en código

Se auditó \`frontend/app.py\` (MVP RF-01–RF-08, aproximadamente 1.293 líneas antes del cambio), \`frontend/requirements.txt\`, \`frontend/Dockerfile\` y las pruebas de GitHub Actions.

- El CSS original era una capa única de unas pocas reglas: tipografía Montserrat, fondo gris, títulos azul corporativo y botón amarillo.
- El cliente navegaba por **11 pestañas horizontales** renderizadas al mismo tiempo, con sus respectivas llamadas a la API en cada ejecución. Esto generaba un espacio de trabajo saturado y podía solicitar datos de módulos no visibles.
- El encabezado de todas las pantallas era «Portal de gestión», sin título ni orientación contextual al perfil o a la tarea.
- El resumen usaba 3 métricas nativas y una nota obsoleta sobre módulos pendientes, sin accesos rápidos.
- Logística agrupaba reservas, despacho y asignaciones de campo en una sola vista larga.
- La vista de calidad mezclaba bandeja pendiente e histórico de inspecciones, incluso después de cerrar un caso.
- Formas, tablas, estados vacíos y expanders utilizaban sobre todo el tema nativo, sin tokens compartidos.
- No había selector de apariencia ni una estrategia de movimiento reducido.

## B. Dirección de diseño

**Concepto:** «Modern SaaS para gestión de proyectos». Mantiene el carácter técnico de COLORLINK y ofrece continuidad visual entre cliente, especialista, logística, aplicador e inspector de calidad. Las referencias de diseño son de calidad y patrones, no se copian interfaces externas.

### Design tokens (modo claro)

| Token | Valor |
|---|---|
| Fondo de aplicación | \`#F5F7FB\` |
| Superficie de tarjetas | \`#FFFFFF\` |
| Texto principal | \`#172238\` |
| Encabezados | \`#111D36\` |
| Texto secundario | \`#64748B\` |
| Bordes | \`#E5EAF2\` |
| Primario | \`#2959D6\` |
| Acento | \`#0E948D\` |
| Éxito | \`#13845A\` |
| Tipografía | Manrope para encabezados, DM Sans para interfaz; fallback a fuentes del sistema |

**Modo oscuro:** paleta independiente, con fondo \`#0A1221\`, tarjetas \`#121D31\`, texto \`#DAE4F3\` y primario \`#80A4FF\`. Se activa con el interruptor **Modo oscuro** de Streamlit y se conserva en \`st.session_state\` durante la sesión, sin escribir datos en el servidor. Las fuentes web tienen alternativas de sistema si el navegador no puede descargarlas.

La iconografía decorativa es un único juego de trazos SVG inline, de estilo Lucide, sin paquetes externos. Las animaciones de hover son discretas; \`prefers-reduced-motion\` desactiva transiciones y animaciones.

## C. Implementación concreta

Archivos:
- **Nuevo** \`frontend/design.py\`: paletas claro/oscuro, CSS con variables \`--cl-*\`, encabezados contextuales, marca, tarjeta de identidad, iconos SVG, tarjetas KPI y secciones; texto dinámico escapado con \`html.escape\`.
- **Actualizado** \`frontend/app.py\`: diseño general, inicio de sesión centrado, sidebar con sesión/rol/modo oscuro, encabezados por rol, cliente con 11 **páginas contextuales** en menú vertical, panel resumen con KPIs y accesos rápidos, logística con 3 secciones contextuales e inspector de calidad con bandeja e histórico separados.
- **Actualizadas** las pruebas del formulario de RF-05, adaptadas al nuevo menú manteniendo la posición del formulario antes del historial.
- **Nuevas** pruebas de humo con \`streamlit.testing.v1.AppTest\` que usan respuestas locales de API, sin tocar Supabase.

Los cambios se limitan al Frontend y archivos de documentación/pruebas. No se cambió el contrato JSON de las solicitudes ni su manejo de errores; no hay llamadas API nuevas ni simulación persistida en código de producción.

### Navegación cliente

1. Mi panel
2. Mi empresa
3. Proyectos
4. Solicitudes
5. Análisis con Gemini
6. Cálculo técnico
7. Inventario
8. Revisión técnica
9. Seguimiento logístico
10. Aplicación en campo
11. Control de calidad

En la versión anterior, los 11 cuerpos \`st.tabs\` se ejecutaban conjuntamente. Ahora se renderiza **solo el módulo seleccionado**. Se mantienen los mismos formularios, claves, funciones, campos y rutas.

### Navegación logística

**Reservas**, **Órdenes y despachos**, **Aplicadores y campo**, preservando los mismos botones y confirmaciones de operación, con carga de datos por sección. La cuenta no gana permisos ni nuevas acciones.

### Navegación inspector

**Inspecciones pendientes** (bandeja, expediente y dictamen) y **Historial de dictámenes** (seguimiento del caso ya aprobado). La bandeja solo se consulta al abrir la sección correspondiente; el historial mantiene las autorizaciones existentes.

### Componentes

- Sidebar con rol y nombre, selección de módulo, modo oscuro y cierre de sesión.
- Cabecera contextual con jerarquía, descripción y etiqueta de ámbito académico.
- Formularios, tablas, expanders, alertas y botones con estilo compartido.
- Indicadores KPI y accesos rápidos con comportamiento real mediante \`st.session_state\`.
- Diseño adaptativo por CSS en anchuras pequeñas; las tablas mantienen el componente nativo para conservar la legibilidad y operatividad.
- Estados vacíos, errores y confirmaciones mantienen la lógica y los mensajes originales.
- Todos los textos de empresa/usuario insertados en HTML se escapan.

## D. Beneficios esperados

- Menor carga cognitiva gracias al menú vertical y encabezados de cada tarea.
- Menos solicitudes API innecesarias al no renderizar todos los módulos del cliente simultáneamente.
- Mayor diferenciación visual y coherencia de marca.
- Accesos más rápidos desde el resumen.
- Diseño más accesible mediante estados de foco visibles, tamaños táctiles, contraste diseñado y movimiento reducido.
- Tema oscuro independiente sin depender del backend.

## E. Validación y pruebas

- Se compararon **54 referencias existentes a rutas API** en \`frontend/app.py\` antes y después del rediseño; coinciden.
- El sistema de CI compila \`backend\` y \`frontend\` y ejecuta \`pytest\`.
- \`tests/test_review_form_visibility.py\` comprueba que Revisión técnica permanece accesible y que el formulario condicional de respuesta sigue antes del historial.
- \`tests/test_frontend_redesign.py\` recorre las 11 vistas del cliente, las pantallas por rol, los cambios de tema y la carga diferenciada de páginas logísticas a través de \`AppTest\`.
- Los datos de los tests provienen de respuestas \`httpx\` locales simuladas **solo en pruebas**; no se crean credenciales reales ni datos permanentes.
- **Pendiente de comprobación manual:** comparar visualmente en Chrome/Safari o equivalente, desktop/tablet/móvil, probar con el expediente RF-08 real, comprobar contraste y navegación por teclado con herramientas de accesibilidad.

## F. Guía para ejecutar y revisar

Actualizar la rama de trabajo:

\`\`\`bash
git pull origin feat/base-plataforma-pintuco360
docker compose down
docker compose up --build
\`\`\`

Abrir \`http://localhost:8501\`, iniciar sesión con las **cuentas de prueba existentes** y revisar:
1. Cliente: menú lateral, tarjetas resumen, accesos rápidos, cada una de las 11 páginas y el histórico de calidad \`finalizada\`.
2. Inspector: RF-08 con el expediente ya aprobado, histórico de dos dictámenes y observaciones.
3. Aplicador: trabajo finalizado y bitácora original.
4. Logística: cambiar entre las tres áreas sin dejar de ver las órdenes registradas.
5. Especialista: consulta de la revisión humana.
6. Alternar el modo oscuro y comprobar lectura en pantalla pequeña.

**Limitaciones:** la interacción y responsive aún requieren inspección visual en navegadores reales; los tests automatizados no sustituyen esa revisión. No se agregó persistencia de tema entre dispositivos, ni librerías de animación innecesarias. No se realizó una migración de framework.
