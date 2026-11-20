# Copiloto inteligente de pintura y acabados

## Alcance
El chatbot orienta sobre pintura, superficies, preparación, colores, acabados y materiales, con
respuestas generadas dinámicamente por **Google Gemini**. No se conecta a módulos de escritura,
no modifica solicitudes ni inventarios, no consulta datos privados y no sustituye inspección técnica.
Disponible a cualquier rol **autenticado** mediante el botón de la barra lateral.

## Arquitectura
- `frontend/copilot_ui.py`: interfaz conversacional con `st.dialog`, sugerencias reales,
  historial acotado, entrada con Enter / Shift+Enter, cargas y errores.
- `backend/app/api/copilot.py`: `POST /api/v1/copiloto/chat`; reutiliza `current_user`,
  que verifica token Supabase y perfil. Cuotas por cuenta.
- `backend/app/services/copilot.py`: Gemini API `generateContent` vía backend con clave privada;
  clasifica intención y extrae parámetros estructurados. Responde con modelo real en asesoría;
  para cálculos compone respuesta basada exclusivamente en cifras calculadas en Python.
- `backend/app/services/copilot_math.py`: aritmética decimal verificable para superficies,
  puertas/ventanas, manos, rendimiento, desperdicio y conversión a galón estadounidense.

## Configuración
En Render (servicio existente) configurar/confirmar **GEMINI_API_KEY** desde la interfaz de
variables de entorno, sin incluirla en el frontend ni en GitHub.
`GEMINI_MODEL` utiliza la configuración existente (consultar disponibilidad para su proyecto
en Google AI Studio). La disponibilidad de cuotas o precios depende del proveedor; no se
garantiza gratuidad. Supabase requiere `SUPABASE_URL` y `SUPABASE_ANON_KEY` existentes.
El backend permanece solo en `127.0.0.1:8000` dentro del contenedor Render.

Para desarrollo local:
```bash
pip install -r backend/requirements.txt -r frontend/requirements.txt -r requirements-dev.txt
python -m pytest tests/test_copilot.py -q
```
Levantar backend con Uvicorn y frontend con Streamlit según el README principal.

## Entrada y cálculo
Petición: `{"message":"Pared de 4 m por 2.5 m, dos manos","history":[]}`
El modelo extrae la geometría; la función determinista calcula:
- 10 m² área neta, 2 manos
- rendimiento supuesto 10 m²/L/mano
- 2 L base + 10 % de margen = **2,2 L estimados**.

Para habitaciones se calcula perímetro × altura, con techo opcional.
El resultado no es una especificación de producto. Si falta información esencial, el
modelo pide datos antes de calcular. Puede usar los datos en los turnos anteriores
que el frontend envía explícitamente. No se persisten conversaciones en Supabase.

## Seguridad y límites
- Solo credenciales de usuario válidas; nunca `service_role`.
- Límite de 8 consultas por minuto y 80 por día por identidad, **por instancia**.
  Para varias réplicas implementar limitador distribuido; este control no garantiza
  cuota global y no ofrece aislamiento económico frente a ataques distribuidos.
- Entrada limitada a 1500 caracteres y a 12 mensajes de historial;
  salida textual limitada a 6000 caracteres.
- Sin ejecución de acciones por el modelo, sin acceso privilegiado a datos.
- Render Markdown con HTML inseguro deshabilitado.
- No se registran chats permanentemente; el historial solo reside en sesión Streamlit.
- Un proveedor caído o con 429/credenciales inválidas devuelve error explícito;
  **nunca se generan respuestas de demostración**.

## Validación pendiente antes de publicar
1. Confirmar que el workflow CI de GitHub esté verde y revisar manualmente UI y móvil.
2. Verificar **GEMINI_API_KEY**, modelo y cuota activos en Render.
3. Validar interacción desde todos los roles, historial, logout y selector de evaluador.
4. Prueba real de las 10 conversaciones del requerimiento con Gemini y el proveedor activo.
5. Revisar regresión de login, registro y todas las transacciones previas.

La rama `feat/copiloto-ia-pintura` es independiente de
`feat/base-plataforma-pintuco360`, que alimenta el despliegue público.
La integración no será visible en producción hasta revisión y fusión deliberada.


## Matriz de aceptación y desglose visual (fase 2)

Pruebas automatizadas en `tests/test_copilot_acceptance.py`: diez escenarios
con respuestas de extracción y orientación **simuladas**, no consultas reales
a Google Gemini. Cubren pared rectangular, habitación, techo, aberturas,
rendimiento informado, varias paredes, datos ausentes, puertas sin dimensiones,
asesoría exterior y combinación de colores. Incluyen continuidad de contexto.
Estas pruebas verifican la orquestación y la matemática, pero **no prueban**
la fiabilidad del modelo real ni sustituyen una revisión de contenido por experto.

El chat muestra una sección desplegable «Ver desglose del cálculo» con los
valores numéricos retornados por la herramienta matemática del servidor.
La explicación identifica cuándo el número de manos, rendimiento o margen
son supuestos orientativos y cuándo fueron aportados en la conversación.
Un valor explícito igual al predeterminado **no debe** marcarse como supuesto.

Criterios pendientes de validación manual en producción con usuario autenticado:
- Solicitar una recomendación de pintura interior y una de fachada exterior.
- Pedir un cálculo con medidas, luego continuar con una aclaración.
- Verificar el desglose y los supuestos, sin atribuirlos a un fabricante.
- Revisar que humedad o fisuras no se describan como diagnósticos definitivos.
- Probar una nueva conversación y el cambio a otra cuenta.
- Comprobar diseño móvil, errores de conectividad y reintentos.

El despliegue solo se considera aceptado cuando todas las verificaciones CI
pasan y Render reporta la nueva versión `Live`.
