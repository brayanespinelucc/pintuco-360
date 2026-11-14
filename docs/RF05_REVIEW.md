# RF-05 — Bandeja de revisión humana (asesor/especialista)

## Funcionalidad implementada
- Bandeja de solicitudes revisables para perfiles con rol asesor, especialista_tecnico o administrador.
- Consulta de datos de solicitud, empresa, proyecto, resultado Gemini, cálculo de materiales, evaluación de stock e historial.
- Acciones humanas auditables: aprobar, rechazar, solicitar información o solicitar corrección de un parámetro.
- Trazabilidad: especialista, fecha, decisión, observaciones, estado anterior/nuevo, análisis/cálculo/evaluación consultados.
- Control de estados con bloqueo de fila para evitar aprobaciones concurrentes y decisiones repetidas después de un estado terminal.
- Aprobación condicionada a que existan al menos un análisis de IA y un cálculo técnico para la solicitud.
- El cliente puede consultar el estado e historial de sus propias solicitudes; no puede revisar ni aprobar.
- Una corrección propuesta se **registra como observación estructurada**, pero NO modifica automáticamente los datos del proyecto, el cálculo, el análisis ni las existencias. El nuevo estado será pendiente_informacion.
- RF-05 NO emite pedidos, no descuenta stock, no autoriza una compra real y no sustituye inspección de campo; la aprobación en este MVP es una decisión de flujo académico.

## Arquitectura y seguridad
- Tabla public.revisiones_tecnicas con RLS y permisos Data API revocados.
- Funciones privadas SECURITY DEFINER con search_path vacío, auth.uid() y consulta del rol real en public.profiles.
- RPC públicas de seguridad INVOKER con ejecución únicamente para authenticated.
- Funciones RPC: bandeja_revision_tecnica, detalle_revision_tecnica y resolver_revision_tecnica.
- Únicamente la función privada puede escribir decisiones y actualizar el estado de las solicitudes.
- El cliente mantiene acceso SELECT únicamente a sus solicitudes gracias a la política RF-01.

## API
- GET /api/v1/revision/bandeja — asesor, especialista_tecnico, administrador
- GET /api/v1/revision/solicitudes/{uuid}/detalle — asesor o cliente dueño
- POST /api/v1/revision/solicitudes/{uuid}/resolver — solo asesor
  Cuerpo JSON:
  {"decision":"aprobar","observaciones":"Se revisaron análisis y cálculos del caso."}

Para proponer un cambio:
  {"decision":"solicitar_correccion","observaciones":"Solicito verificar superficie real de la fachada.", "correccion_propuesta":{"campo":"area_m2","valor_propuesto":"90.00"}}

## Creación de un usuario asesor de prueba

No cambiar el rol de la cuenta cliente existente: necesitamos validar la separación de permisos.

1. En Supabase > Authentication > Users, crea un SEGUNDO usuario con un correo distinto y contraseña propia.
2. En Supabase > SQL Editor, ejecuta este SQL modificando el correo. No pegues contraseñas en la consulta:

```sql
update public.profiles
set role = 'especialista_tecnico'
where id = (select id from auth.users where email = 'CORREO_DEL_SEGUNDO_USUARIO');
```

3. Confirma en SQL Editor:

```sql
select p.role, (u.id is not null) as tiene_usuario
from public.profiles p
join auth.users u on u.id = p.id
where u.email = 'CORREO_DEL_SEGUNDO_USUARIO';
```

4. Actualiza tu copia local de la rama: git pull origin feat/base-plataforma-pintuco360.
5. Detén y reconstruye contenedores: docker compose up --build.
6. Inicia sesión como especialista en http://localhost:8501. Abre la bandeja, revisa la solicitud, registra una decisión con justificación.
7. Cierra sesión e inicia como cliente. Abre Revisión técnica, comprueba estado e historial.
8. Intentar aprobar desde la cuenta cliente debe estar bloqueado (probado con tests y SQL de verificación).

## Pruebas y límites
- La primera solicitud tiene Gemini, cálculo e inventario, por lo que es elegible para revisión.
- La SQL de seguridad se probó en transacciones que se revirtieron; no se aprobaron ni cambiaron solicitudes reales durante la prueba.
- No hay carga de correcciones desde la cuenta cliente; las solicitudes de corrección quedan a la espera de ese desarrollo.
- No se incluyen notificaciones ni workflows de n8n; serán fases siguientes.
- Los productos e inventarios son académicos y no representan servicios reales de Pintuco.
