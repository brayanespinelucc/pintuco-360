# Evolución UX/UI de COLORLINK — experiencia orientada al proceso

## 1. Auditoría del sistema existente

**Stack inspeccionado:** Streamlit \`frontend/app.py\`, sistema visual \`frontend/design.py\`, FastAPI en \`backend/app/api\`, Supabase para sesiones, entidades, expedientes y registros de actividad, Gemini para análisis con consentimiento. La aplicación ya tiene autenticación, navegación por roles, menú lateral, tokens visuales, tema oscuro y formularios funcionales.

### Hallazgos por prioridad

| Prioridad | Hallazgo observado | Intervención |
|---|---|---|
| Alta | El estado de una solicitud aparece como texto técnico y varias tablas independientes. | Vista central de solicitud, resumen de estado y stepper del recorrido completo. |
| Alta | El cliente no visualiza fácilmente dónde continuar según el estado actual. | Acción contextual que navega a un módulo ya autorizado; nunca ejecuta una transición. |
| Alta | Los eventos de revisión, despacho y control de calidad se consultan como tablas o texto. | Timeline cronológico de eventos existentes con etiquetas, fechas y observaciones. |
| Media | El dashboard contiene solo totales de entidades, sin resumen de estados. | Distribución por estados reales y selector de expediente. |
| Media | Los espacios operativos muestran trabajo pendiente sin indicadores a primera vista. | Métricas de pendientes/órdenes/expedientes/trabajos basadas en datos existentes. |
| Media | En aplicación se consulta el porcentaje real, sin tratamiento visual consistente entre roles. | Componente reutilizable de progreso físico RF-07, sin aproximar el progreso completo. |
| Media | Navegación de 11 módulos lineales. | Mantiene los accesos para no romper los recorridos; añade acciones directas del expediente. La reorganización estructural completa del sidebar queda pendiente. |

## 2. Concepto de diseño

**"El expediente como centro de trabajo"**. Una tarjeta de resumen comunica el estado, el identificador, el nombre del proyecto cuando se obtiene del endpoint ya utilizado y la descripción de la próxima actividad. Un stepper visual presenta siete fases del ciclo de COLORLINK; una vista desplegable permite explorar cualquier etapa sin modificar registros ni saltar validaciones.

Las acciones son **botones nativos de Streamlit** que seleccionan módulos ya existentes. El HTML y CSS solo tienen finalidad presentacional y se insertan mediante \`st.html\`; se escapan los valores no confiables provenientes del servidor. Se conserva la identidad visual azul/turquesa de \`frontend/design.py\`, con versiones claro/oscuro, foco accesible y movimiento reducido.

### Etapas y mapeo explícito de estados persistidos

| Etapa UX | Estados existentes del campo \`solicitudes.estado\` |
|---|---|
| Solicitud | \`radicada\`, \`en_validacion\` |
| Análisis | \`en_analisis\` |
| Revisión técnica | \`pendiente_informacion\`, \`en_revision_tecnica\`, \`cotizada\`, \`aprobada\` |
| Logística | \`en_logistica\` |
| Aplicación | \`en_aplicacion\` |
| Calidad | \`en_calidad\` |
| Cierre | \`finalizada\` |
| Excepción | \`cancelada\`: mensaje de cancelación, sin simular progreso |

**Advertencia de interpretación:** el stepper presenta orientación a partir del estado actual, no auditoría probatoria de finalización por etapa. Las fases anteriores se indican como "Etapa anterior", no se inventan eventos de completitud. Los eventos auditables reales se muestran únicamente cuando el endpoint devuelve un registro con fecha real. Para cada etapa sin fecha individual, el componente no muestra fechas.

No se crean nuevos estados ni transiciones. Los porcentajes solo proceden de \`avance_pct\` de ejecución de campo. No hay un porcentaje sintético "del proceso".

## 3. Mapeo de recorridos y navegación

**Cliente:** Panel → Empresa → Proyecto → Solicitud → Análisis IA (consentimiento) → Cálculo técnico → Inventario → Revisión técnica → Logística → Campo → Calidad. Un estado pendiente de información dirige al módulo donde ya se ofrece el formulario de respuesta; nunca responde automáticamente. El panel permite seleccionar una solicitud y pasar a su siguiente módulo informativo.

**Especialista técnico:** Bandeja → Expediente → Análisis/Cálculo/Inventario → Dictamen. Se agrega stepper de referencia e historial visual, conservando los formularios y verificaciones.

**Logística:** Reservas → Preparación/despacho → Asignaciones. Nuevos indicadores de carga real, stepper contextual y línea de eventos. Los botones existentes conservan sus endpoints y condiciones.

**Aplicador:** Trabajo asignado → Inicio → Avance/Incidencia → Evidencias → Finalización → Correcciones si calidad lo solicita. Progreso basado en \`avance_pct\` real; sin confundir ejecución al 100% con aprobación de calidad.

**Calidad:** Inspecciones pendientes → Verificar expediente/evidencias → Dictamen → Historial. Carga de trabajo real y eventos visualizados sin sustituir la evidencia ni la validación humana.

Las cuentas que cuentan con autorización de evaluador pueden cambiar entre los roles configurados; este rediseño no altera ese permiso ni su lógica.

## 4. Implementación realizada

| Archivo | Cambio |
|---|---|
| \`frontend/process_ui.py\` | Nuevo componente de estado, vista central de solicitud, stepper, explorador de etapas, distribución de estados, porcentaje físico y timeline de eventos. |
| \`frontend/design.py\` | Estilos responsables del nuevo stepper, tarjeta de expediente, estados y timeline, accesibles en claro/oscuro y pantallas estrechas. |
| \`frontend/app.py\` | Integración en panel, solicitudes, revisión, logística, campo y calidad; rutas contextuales hacia módulos existentes y métricas operativas con datos ya consultados. |
| \`tests/test_process_ui.py\` | Pruebas para todos los estados, cancelación, porcentajes, escape HTML, fechas reales y componentes. |
| \`tests/test_frontend_redesign.py\` | Pruebas Streamlit AppTest que comprueban selección de expediente y navegación por acción contextual sin POST de negocio. |

**Intencionalmente NO modificados:** \`backend/\`, contratos FastAPI, migraciones Supabase, roles/RLS, Gemini, proceso de registro, permisos, estados persistidos ni configuración de despliegue. Ningún componente introduce llamadas de red propias.

## 5. Pruebas y limitaciones

Las pruebas automáticas del repositorio ejecutan \`python -m compileall -q backend frontend\`, \`python -m pytest -q\`, y un smoke test que construye \`Dockerfile.render\` y arranca API+Streamlit en 512 MB. Se añadieron casos sobre estados reales, rutas contextuales, datos inseguros y UI.

**Por validar manualmente:** escritorio/móvil/tablet en navegador real, zoom 200%, teclado y lector de pantalla, contraste WCAG 2.2 AA, captura con usuarios reales de todos los roles, scroll horizontal del stepper, volumen de expedientes y posibles problemas de tiempos de carga del plan gratuito Render.

**Restricciones:** el componente no prueba la ejecución histórica de un hito por el solo hecho de conocer un estado actual. Se usa "Anterior" y "Pendiente" como orientación, sin inventar una bitácora. No se agregó un porcentaje del proceso. Los formularios originales conservan sus etiquetas y validaciones; algunas tablas técnicas continúan disponibles y requieren refinamiento visual posterior.

## 6. Siguientes refinamientos priorizados

1. Probar la interfaz visualmente en ancho de 360 px, 768 px y escritorio, con muestras de registros reales.
2. Reorganizar el menú de 11 módulos en grupos de navegación sin perder acciones ni enlaces de contexto.
3. Mejorar presentación contextual de formularios largos y de tablas sin eliminar los campos técnicos útiles.
4. Validación de accesibilidad WCAG 2.2 AA con herramientas de contraste y teclado, no solo CSS.
5. Probar el recorrido íntegro de cliente→especialista→logística→campo→calidad con los datos autorizados.

El despliegue desde GitHub a Render se ejecuta según la configuración ya existente del proyecto y se debe comprobar en el servicio público después de la CI.
