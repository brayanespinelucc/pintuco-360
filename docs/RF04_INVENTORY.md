# RF-04: disponibilidad por bodegas y lotes

## Funcionalidad
- Bodegas, lotes, ubicaciones, fechas de vencimiento y cantidades expresadas en envases.
- Disponible por lote = existencia - reservado. Se excluyen lotes bloqueados, vencidos y sin unidades.
- Se propone una asignación FEFO (vence primero, sale primero) que puede utilizar varios lotes.
- Si todos los envases están disponibles, devuelve inventario_disponible; si faltan, devuelve derivar_produccion con unidades faltantes.
- Almacena una evaluación con propuestas y marcas temporales en Supabase.
- No reserva, descuenta ni transfiere inventario. Ese paso pertenece a RF-06.
- Conserva el indicador de revisión humana del cálculo de RF-03; si está activo NO autoriza despacho.

## Seguridad
La función segura private.evaluar_stock valida auth.uid() contra el dueño del cálculo y consulta las tablas de stock sin permitir que el cliente lea o modifique directamente bodegas ni lotes. Se expone únicamente el wrapper de invocador público public.evaluar_disponibilidad_calculo. Las evaluaciones tienen políticas RLS de propietario y solo se escriben mediante la función del servidor.

## API
- POST /api/v1/inventario/solicitudes/{id}/evaluar con cuerpo JSON que contiene calculo_id.
- GET /api/v1/inventario/solicitudes/{id}/evaluaciones.

## Datos de prueba
Las dos bodegas y lotes añadidos son exclusivamente académicos, NO son existencias oficiales de Pintuco:
- Lote DEMO MDE: 4 envases físicos, 1 reservado de prueba, 3 disponibles.
- Lote DEMO BEL: 5 envases físicos, 1 reservado de prueba, 4 disponibles.
- Total disponible: 7 envases de 4 litros por envase, equivalentes a 28 litros.

En el ejemplo teórico de 85 metros cuadrados y 5 envases, la propuesta asigna 3 del primer lote y 2 del segundo. El último cálculo real del usuario puede tener otra cantidad: la consulta SIEMPRE utiliza lo que figure guardado en RF-03, no el ejemplo.

## Cómo probar
1. En VS Code y la rama feat/base-plataforma-pintuco360, detén Docker con Control+C.
2. Ejecuta: git pull origin feat/base-plataforma-pintuco360
3. Ejecuta: docker compose up --build
4. Abre http://localhost:8501, inicia sesión y entra en Inventario / Disponibilidad.
5. Elige la solicitud y su cálculo técnico; pulsa Consultar disponibilidad.
6. Observa la cantidad requerida, disponible y los lotes propuestos; comprueba que diga PROVISIONAL.
7. Recarga la página para confirmar el historial.
8. Para demostrar escasez, crea una solicitud de mayor área, calcula más de 7 envases y evalúa de nuevo.

## Límites
- Los datos semilla son ficticios. No utilizarlos para estimar stock comercial o vender.
- No existe conexión al ERP real.
- No hay reserva, movimiento ni despacho; estos deben usar transacciones e idempotencia para evitar sobreventa.
- La consulta FEFO excluye lotes vencidos, pero para la aplicación real habría que validar reglas técnicas de caducidad y lote.
- La derivación a producción es una etiqueta de decisión, NO una orden de producción.
