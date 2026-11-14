# Requisitos funcionales obligatorios

Fuente: imagen del reto transversal entregada en la conversación. Se incorporará el Product Backlog completo cuando el usuario aporte el archivo.

## Caso de demostración
- Cliente: Constructora Horizonte.
- Ciudad: Medellín.
- Proyecto: fachada edificio residencial.
- Área: 85,00 m².
- Superficie: concreto.
- Condición: humedad y fisuras.
- Ambiente: exterior.
- Color: gris.
- Fecha requerida: 20 días.
- Fotografías adjuntas.

## Quince etapas
1. **Captura:** datos, fotografías y características.
2. **Validación:** faltantes, errores y duplicados.
3. **IA/Gemini:** clasifica la necesidad a partir de texto e imágenes.
4. **Motor técnico:** cruza superficie, ambiente, condición y catálogo.
5. **Cantidades:** calcula área, manos, rendimiento, desperdicio y unidades.
6. **Disponibilidad:** consulta inventario, presentación, ubicación y lote.
7. **Decisión:** determina inventario o producción/tintometría.
8. **Solicitud:** genera presupuesto preliminar.
9. **Human-in-the-loop:** casos complejos a especialista.
10. **Logística:** reserva inventario y solicita despacho.
11. **Servicio:** agenda acompañamiento técnico cuando aplique.
12. **Comunicación:** informa cambios de estado al cliente.
13. **Aplicación:** registra evidencias, consumos y novedades.
14. **Calidad:** relaciona incidencias con producto, lote y proyecto.
15. **Analítica:** actualiza indicadores en dashboard.

## Herramientas prescritas
- Automatización: Activepieces o n8n Community.
- IA: Google AI Studio / Gemini API.
- Desarrollo: VS Code.
- APIs: Bruno.
- Base de datos: Supabase PostgreSQL.
- Dashboard: Metabase / Looker Studio.
- Backend: FastAPI.
- Frontend: Streamlit.
- Arquitectura: diagrams.net.
- Repositorio: GitHub.

## Reglas
- La IA se utiliza donde aporta valor: contenido no estructurado a datos estructurados.
- Gemini no inventa cantidades de pintura; el cálculo es determinístico.
- Las condiciones técnicas de humedad y fisuras pueden requerir inspección humana.
- La plataforma debe funcionar de extremo a extremo, con persistencia, seguridad y pruebas.
