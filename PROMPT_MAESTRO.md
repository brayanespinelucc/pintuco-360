# Instrucciones para el agente de desarrollo — Pintuco 360

## Misión
Construir una plataforma académica **funcional de extremo a extremo** para atención de solicitudes de pintura y recubrimientos. No entregar solamente una maqueta. Desarrollar, probar e integrar cada proceso de [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md). Ninguna operación se puede declarar completa sin persistencia, controles de autorización y pruebas adecuadas. Diferenciar funcionalidades reales de demostraciones.

## Tecnologías obligatorias
- Backend: FastAPI + Pydantic + Python.
- Frontend: Streamlit con diseño corporativo.
- Identidad, datos y archivos: Supabase Auth / PostgreSQL / Storage.
- Inteligencia artificial: Gemini API, **solo para clasificación/extracción** y con revisión humana cuando se requiera.
- Automatización: n8n Community o Activepieces.
- Analítica: dashboards en la aplicación y Metabase o Looker Studio.
- Diagramas: diagrams.net. Versionado: GitHub. Pruebas de API: Bruno.

## Estilo visual
Basarse en https://www.pintuco.com.co/ y la guía pública de marca disponible. Tokens de referencia: azul #0A1E8C, amarillo #FFDD00 y rojo #E20024. Usar Montserrat como alternativa web cuando no exista licencia de fuentes propietarias. Diseño responsive y accesible, todo en español. No representar la solución académica como producto oficial.

## Roles mínimos
Administrador, cliente, asesor comercial, especialista técnico, inventario, producción/tintometría, logística, aplicador de campo, analista de calidad y gerencia. Implementar RBAC validado en backend y aislamiento entre clientes; no confiar solo en controles visuales. Evitar credenciales en código.

## Caso E2E obligatorio
Cliente Constructora Horizonte, Medellín, fachada de edificio residencial, 85 m², concreto, humedad y fisuras, exterior, gris, requerimiento en 20 días, fotografías adjuntas. El diagnóstico debe reconocer la necesidad de verificar causas de humedad y fisuras antes de recomendar pintura.

## Procesos
1. Captura con fotografías y datos.
2. Validaciones de faltantes/errores/duplicados.
3. Gemini clasifica texto e imágenes.
4. Motor técnico de reglas y fichas de producto.
5. Cálculos matemáticos determinísticos de cantidades, desperdicio, manos, rendimientos y presentaciones.
6. Inventario real por ubicación y lote.
7. Decisión inventario/producción/tintometría.
8. Cotización con versiones, impuestos y PDF.
9. Aprobación/revisión humana para casos especiales.
10. Reserva transaccional de inventario, despacho y entrega.
11. Agenda de asistencia técnica.
12. Notificaciones y cambios de estado.
13. Registro de aplicación, consumo y evidencias.
14. Incidencias y trazabilidad lote-producto-proyecto.
15. Indicadores desde datos reales y dashboards.

## Implementación
- Lee primero el repositorio y los documentos de requisitos que se incorporen. Respeta lo ya construido.
- No deshagas cambios sin revisar. Trabaja en ramas y pull requests.
- No inventes existencias, rendimientos, precios, diagnósticos o datos de producción. Etiqueta los datos de demostración.
- Cada módulo debe tener esquema/migraciones, servicio, API con validaciones, interfaz, permisos, errores y pruebas.
- Toda reserva de inventario debe ser transaccional e idempotente y nunca sobrepasar existencias.
- La IA no puede aprobar ni cambiar inventarios ni precios.
- Configura logging, auditoría, validación y tratamiento seguro de archivos.
- Entrega automatizaciones exportables, documentación OpenAPI y despliegue reproducible.
- Ejecuta pruebas reales; distingue siempre implementado, validado, probado, pendiente de credenciales y pendiente de producción.
- Actualiza docs/IMPLEMENTATION_STATUS.md y README a medida que avances.
- Continúa progresivamente hasta completar el flujo E2E, sin bloquearse por tareas futuras no necesarias para el siguiente módulo.
