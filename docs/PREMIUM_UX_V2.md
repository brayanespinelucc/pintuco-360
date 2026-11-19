# COLORLINK — Premium UX v2

## Alcance y rama de trabajo

- Rama aislada: \`feat/premium-ux-v2\` creada desde \`feat/base-plataforma-pintuco360\`.
- La versión accesible actualmente en \`https://colorlink-web-4jb5.onrender.com\` **no se modifica** mientras se desarrolla esta rama.
- Dirección visual: **NOVA** — contraste entre navegación profunda en azul tinta, superficies limpias cálidas, acentos violeta y turquesa, tipografía Outfit + DM Sans, contenedores elaborados, contraste y jerarquía editorial.
- Objetivo: rediseño integral del frontend existente manteniendo reales los formularios, endpoints, datos y permisos.

## Inventario de 18 vistas y transformación

| Vista real | Nueva composición | Función que se conserva |
|---|---|---|
| Acceso | Landing inmersiva de dos columnas + acceso y registro en pestañas | Inicio de sesión y alta pública Supabase |
| Cliente: Mi panel | Hero editorial, indicadores, stepper, resumen y siguiente acción | Consultas de empresas/proyectos/solicitudes |
| Cliente: Mi empresa | Formulario + directorio, dos columnas, tarjetas y tabla | Registrar y consultar empresas |
| Cliente: Proyectos | Planificador con formulario y cartera lateral | Crear y consultar proyectos |
| Cliente: Solicitudes | Pestañas de radicación y expediente, evidencia y stepper | Radicar, adjuntar y consultar evidencias |
| Cliente: Análisis con Gemini | Nueva guía contextual + formularios, resultados y estilos unificados | Consentimiento y análisis |
| Cliente: Cálculo técnico | Nueva guía contextual + formulario y métricas de resultado | Cálculos determinísticos |
| Cliente: Inventario | Guía contextual + indicadores y propuestas FEFO | Consulta y evaluación sin reservar |
| Cliente: Revisión técnica | Guía y stepper; historial de eventos y formulario conservado | Respuestas al especialista |
| Cliente: Seguimiento logístico | Resúmenes de órdenes, stepper e historial | Consultar sus propias órdenes |
| Cliente: Aplicación en campo | Resumen visual de trabajos, progreso real y bitácora | Consultar avance y evidencias |
| Cliente: Control de calidad | Tarjetas de expedientes, estados y dictámenes | Consultar evaluaciones |
| Especialista técnico | Bandeja visual, eventos, detalle y dictamen | Revisar y resolver solicitudes |
| Logística: Reservas | Carga real, tarjetas y tabla bajo detalle | Reservar envases |
| Logística: Órdenes y despachos | Estados de órdenes, tarjetas y timeline | Preparar, cancelar y despachar |
| Logística: Aplicadores y campo | Vista de asignación y trabajos con indicadores | Asignar responsables |
| Aplicador | Tarjetas de trabajos, progreso y formulario contextual | Iniciar, registrar avance, corregir, evidencia |
| Calidad: Pendientes e historial | Expedientes y tablas visuales, checklist y bitácora | Dictamen y consulta de historial |

El inventario cuenta **11 vistas Cliente, 3 Logística, 2 Calidad, 1 Aplicador, 1 Especialista**, más la **pantalla de acceso y registro**. Otros roles reutilizan los espacios que ya poseen; no se inventan permisos ni páginas.

## Cambios técnicos verificables

**\`frontend/premium.css\`**: stylesheet único, tokens por tema, sidebar oscuro, navegación por botones, accesibilidad/foco, formularios, inputs, selectores, tabs, cards, estados vacíos, tablas, uploaders, progress, alertas, login y stepper. Las media queries contemplan escritorio, tablet, móvil y movimiento reducido.

**\`frontend/design.py\`**: concentra las funciones presentacionales existentes \`brand\`, \`user_identity\`, \`page_hero\`, \`metric_cards\`, \`section_intro\`, y añade \`auth_showcase\`, \`auth_form_heading\`, \`workspace_breadcrumb\`, \`navigation_group\`, \`record_cards\`, \`empty_state\`, \`journey_hint\`. Su salida HTML escapa todo texto dinámico y no introduce botones inertes.

**\`frontend/app.py\`**: login en dos columnas, sidebar reorganizado por grupos con botones Streamlit reales, encabezado contextual y ayudas por rol, formularios de Cliente reestructurados en dos columnas o pestañas, resúmenes visuales para Logística, Campo, Calidad y Especialista. La navegación mantiene como fuente \`st.session_state\` las claves \`cl_page\`, \`cl_logistics_page\`, \`cl_quality_page\`, por lo que los accesos directos y el selector de roles continúan funcionando.

**\`frontend/process_ui.py\`**: se conserva el componente orientado al proceso (etapas reales, timeline, estados y avance físico) y se integra en el nuevo diseño.

**Tests**: se actualiza el recorrido por botones agrupados en lugar del antiguo radio lineal, sin desactivar los tests de permisos, endpoints, formularios o lazy loading. Se agregan checks de identidad, textos escapados, contraste esperado de tokens, teclado/movimiento reducido, ayudas a 11 módulos y no existencia de botones visuales inertes.

## Restricciones respetadas

- **Sin cambios** en \`backend\`, \`database\`, migraciones, modelos, integraciones ni flujo de permisos.
- No se agregan endpoints ni llamadas de red en los componentes visuales.
- No se reemplazan formularios ni datos reales por maquetas. Los \`st.dataframe\` originales se mantienen en la misma vista (algunos dentro de un expander) para conservar consulta y ordenamiento.
- Cambiar de rol sigue requiriendo autorización de evaluador en Supabase, como en la versión anterior.
- Las ayudas estáticas no se presentan como eventos auditados; el progreso de campo viene del valor real \`avance_pct\`.

## Validación

- \`python -m compileall -q backend frontend\`.
- \`pytest -q\` (incluye pruebas de Streamlit AppTest con llamadas HTTP simuladas).
- \`Dockerfile.render\` CI con límite de 512 MB: arranque de Streamlit y API privada.

**La compilación y las pruebas automatizadas no equivalen a una auditoría visual real**. Antes de fusionar esta rama, revisa en navegador: 360px, 768px, 1440px; contraste WCAG AA; scroll del stepper; teclado; zoom 200%; pestañas de registro; carga de expedientes; alertas de validación; un recorrido real en cada rol; y modo oscuro. Corrige cualquier desalineación antes de considerarlo cerrado.

## Revisión, integración y reversión

1. Inspeccionar la comparación de GitHub de esta rama contra \`feat/base-plataforma-pintuco360\`.
2. Revisar los tests y el diseño en una instancia temporal si se dispone de ella, sin generar recursos pagados inadvertidamente.
3. Fusionar a \`feat/base-plataforma-pintuco360\` cuando el usuario apruebe el cambio visual. El servicio Render auto-deploy detectará los commits de esa rama.
4. Si la nueva interfaz requiere reversión, restaurar el commit anterior de la rama base y volver a desplegar por el mecanismo habitual.

La publicación actual para el profesor se mantiene intacta hasta fusionar.
