# RF-08 — Control de calidad (MVP académico, versión 0.9.0)

## Qué se implementó

- La bandeja de inspección incluye únicamente aplicaciones finalizadas al 100 % y solicitudes en estado `en_calidad`.
- Un inspector humano con rol `calidad` (o `administrador` desde la API) revisa proyecto, registro de actividades, incidencias, fotografías y revisiones previas.
- Checklist obligatorio de cinco criterios (Sí/No): `superficie_preparada`, `cobertura_adecuada`, `acabado_uniforme`, `evidencias_verificadas`, `incidencias_gestionadas`.
- Dictámenes: **aprobar**, **solicitar_correccion** y **rechazar**, con observaciones y autor/fecha.
- **Aprobar** requiere los cinco criterios positivos, al menos una evidencia fotográfica de campo y solicitud vigente `en_calidad`. La solicitud pasa a `finalizada`; la aplicación, a `calidad_aprobada`.
- **Solicitar corrección** requiere al menos un criterio negativo. La solicitud regresa a `en_aplicacion`; la aplicación pasa a `en_correccion`.
- El aplicador asignado puede añadir nuevas fotografías privadas durante `en_correccion`, documentar la subsanación y devolver el expediente a `en_calidad` / `pendiente_calidad` sin borrar la inspección anterior.
- **Rechazar** requiere al menos un criterio negativo; deja la solicitud `rechazada` y la aplicación `calidad_rechazada`, de forma terminal en este MVP.
- Cada inspección se conserva con número de revisión, criterios, observaciones, responsable, estados anterior y nuevo, e inventario del número de evidencias e incidencias consultadas.
- El cliente solo ve la información de sus propios expedientes y puede consultar dictámenes en la pestaña **Control de calidad**, sin poder emitirlos.
- El progreso original 100 % representa ejecución terminada, **no aprobación de calidad**. Sigue 100 % durante una subsanación para preservar lo que se informó en RF-07.
- Todo es **demostrativo**: no se certifican acabados, no se realiza inspección física, no hay un aval comercial de Pintuco.

## Arquitectura y seguridad

- Migración: `database/migrations/0011_rf08_quality.sql`.
- Tabla `public.inspecciones_calidad` con RLS activo y sin permisos de lectura/escritura directa para usuarios Data API.
- Funciones privadas SECURITY DEFINER con `search_path=''`, controles explícitos del rol almacenado en `public.profiles`, propiedad de la solicitud y transición; los wrappers públicos son SECURITY INVOKER y solo `authenticated`.
- La escritura bloquea filas con `FOR UPDATE` y comprueba que la aplicación esté `pendiente_calidad` y la solicitud `en_calidad`. Evita aprobar dos veces o sobre un estado obsoleto.
- La nueva subsanación es una entrada de bitácora `subsanacion`; no reescribe ni borra decisiones. Límite de 20 inspecciones por aplicación.
- Las fotografías permanecen en el bucket privado `colorlink-campo` y se descargan únicamente después de autorización con JWT.
- No existe edición o eliminación de inspecciones desde la interfaz ni desde RPC.

## API

- `GET /api/v1/calidad/bandeja` — inspector/administrador.
- `GET /api/v1/calidad/expedientes` — inspector/administrador, cliente dueño, aplicador asignado.
- `POST /api/v1/calidad/aplicaciones/{uuid}/resolver` — inspector/administrador.

Ejemplo de dictamen:

```json
{
  "decision": "solicitar_correccion",
  "criterios": {
    "superficie_preparada": true,
    "cobertura_adecuada": true,
    "acabado_uniforme": false,
    "evidencias_verificadas": true,
    "incidencias_gestionadas": false
  },
  "observaciones": "El acabado y el seguimiento a la incidencia requieren verificación adicional."
}
```

- `POST /api/v1/campo/aplicaciones/{uuid}/subsanar` — solo aplicador asignado con trabajo `en_correccion`; JSON `{"observaciones":"Se atendieron los dos criterios señalados por el inspector."}`.
- El mismo endpoint privado RF-07 de fotografía admite ahora `en_correccion`, sin habilitar acceso a roles adicionales.

## Pruebas técnicas realizadas

- Casos SQL transaccionales revertidos: aprobar, rechazo, bloqueo de aprobación con criterios negativos, bloqueo de rechazo con todos criterios positivos, reintento duplicado, remisión a correcciones y nueva inspección posterior al informe de subsanación.
- Se comprobó que el cliente no puede subir subsanaciones y que la foto privada puede adjuntarse durante la corrección únicamente desde la cuenta aplicador.
- La inspección inicial y la segunda permanecen vinculadas a la misma solicitud y a la bitácora original.
- Todas las operaciones de prueba se ejecutaron con `ROLLBACK`: NO se modificó la solicitud real `en_calidad` ni se creó un dictamen permanente.
- Pruebas automatizadas de FastAPI en `tests/test_quality.py` y GitHub Actions.

## Cómo probarlo manualmente

1. Crea **una quinta cuenta** distinta en Supabase > Authentication > Users. Usa correo y contraseña de prueba propios; no modifiques los roles de cliente, especialista, logística ni aplicador.
2. En Supabase SQL Editor ejecuta, reemplazando el correo:

```sql
update public.profiles
set role='calidad'
where id=(select id from auth.users where email='CORREO_DEL_QUINTO_USUARIO');
```

3. Detén la aplicación local y sincroniza:

```bash
git pull origin feat/base-plataforma-pintuco360
docker compose down
docker compose up --build
```

4. En `http://localhost:8501` debe figurar `Interfaz 0.9.0`. Inicia sesión como `calidad`.
5. Abre **RF-08 · Control de calidad académico**. En la bandeja debe figurar la solicitud de Constructora Horizonte finalizada en RF-07, con 100 % de avance, 1 incidencia y 1 fotografía.
6. Abre la bitácora y pulsa **Ver fotografía privada** para comprobar acceso a Storage.
7. Para probar el ciclo completo sin terminar inmediatamente el caso, selecciona **Solicitar correcciones**, marca Sí los criterios cumplidos y deja al menos un criterio en No (por ejemplo acabado uniforme e incidencias gestionadas), añade una justificación de al menos 15 caracteres y confirma el dictamen.
8. Como cliente, consulta **Control de calidad**. Debe reflejar las observaciones y el estado `en_aplicacion`.
9. Como aplicador, abre el trabajo `en_correccion`, añade foto correctiva opcional, documenta la subsanación y pulsa **Enviar correcciones a calidad**.
10. De nuevo como calidad, reabre el expediente, revisa los dos informes y decide **Aprobar calidad** solo si los cinco criterios se consideran cumplidos en la simulación. La solicitud pasará a `finalizada` y la aplicación a `calidad_aprobada`.
11. El cliente observa la aprobación y el historial completo en **Control de calidad**.

## Límites y precauciones

- La aprobación es una **decisión simulada sobre un expediente académico**, no un certificado técnico o una evaluación real de fachada; el inspector debe basarse en la información ficticia documentada.
- La opción **Rechazar inspección** es terminal; se requiere una nueva solicitud académica para seguir probando otras ramas si se selecciona.
- El MVP no permite reclamaciones, reapertura automática, ensayos físicos, firmas digitales, reglamentación de obra, ni autorización de facturación/cierre contable.
