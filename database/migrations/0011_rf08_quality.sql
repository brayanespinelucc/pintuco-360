-- RF-08 · Inspección humana de calidad. Solo operación académica.
-- Dictámenes: aprobar, solicitar_correccion o rechazar; nunca automáticos.
-- La evaluación es documentaria/simulada, NO una certificación técnica ni de obra.

alter table public.aplicaciones_campo drop constraint if exists aplicaciones_campo_estado_check;
alter table public.aplicaciones_campo add constraint aplicaciones_campo_estado_check
 check (estado in (
   'asignada','en_ejecucion','pendiente_calidad','en_correccion',
   'calidad_aprobada','calidad_rechazada'
 ));
alter table public.bitacora_campo drop constraint if exists bitacora_campo_tipo_check;
alter table public.bitacora_campo add constraint bitacora_campo_tipo_check
 check (tipo in (
   'asignacion','inicio','avance','incidencia','evidencia',
   'finalizacion','subsanacion'
 ));

create table public.inspecciones_calidad (
 id uuid primary key default gen_random_uuid(),
 aplicacion_id uuid not null references public.aplicaciones_campo(id) on delete restrict,
 solicitud_id uuid not null references public.solicitudes(id) on delete restrict,
 cliente_id uuid not null references auth.users(id) on delete restrict,
 inspector_id uuid not null references auth.users(id) on delete restrict,
 decision text not null check (decision in ('aprobar','solicitar_correccion','rechazar')),
 criterios jsonb not null check (jsonb_typeof(criterios)='object'),
 observaciones text not null check (char_length(btrim(observaciones)) between 15 and 2000),
 numero_inspeccion integer not null check (numero_inspeccion between 1 and 20),
 estado_solicitud_anterior text not null,
 estado_solicitud_nuevo text not null,
 estado_aplicacion_anterior text not null,
 estado_aplicacion_nuevo text not null,
 evidencias_examinadas integer not null check (evidencias_examinadas>=0),
 incidencias_examinadas integer not null check (incidencias_examinadas>=0),
 es_demostrativo boolean not null default true check (es_demostrativo),
 created_at timestamptz not null default now(),
 unique(aplicacion_id,numero_inspeccion)
);
create index idx_inspecciones_calidad_solicitud on public.inspecciones_calidad(solicitud_id,created_at desc);

alter table public.inspecciones_calidad enable row level security;
revoke all on public.inspecciones_calidad from public,anon,authenticated;
-- No conceder SELECT/INSERT/UPDATE/DELETE directos. Solo RPC autorizadas.
create schema if not exists private;
revoke all on schema private from public,anon,authenticated;
grant usage on schema private to authenticated;

create or replace function private.rf08_es_inspector()
returns boolean language sql stable security definer set search_path=''
as $$
 select auth.uid() is not null and exists (
  select 1 from public.profiles p
  where p.id=auth.uid() and p.role in ('calidad','administrador')
 );
$$;
revoke all on function private.rf08_es_inspector() from public,anon,authenticated;
grant execute on function private.rf08_es_inspector() to authenticated;

-- Bandeja: solo aplicaciones terminadas y efectivamente remitidas a calidad.
create or replace function private.rf08_bandeja()
returns jsonb language plpgsql stable security definer set search_path=''
as $$
declare v_result jsonb;
begin
 if not private.rf08_es_inspector() then
   raise exception 'Solo calidad puede consultar la bandeja' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(to_jsonb(t) order by t.fecha_finalizacion desc),'[]'::jsonb)
 into v_result
 from (
  select a.id as aplicacion_id,a.solicitud_id,a.estado as estado_aplicacion,
     a.avance_pct,a.finalizacion_at as fecha_finalizacion,
     p.nombre_proyecto,p.tipo_superficie,p.ambiente,p.area_m2,
     c.nombre_empresa,c.ciudad,
     (select count(*)::integer from public.bitacora_campo b
       where b.aplicacion_id=a.id and b.tipo='evidencia') as evidencias,
     (select count(*)::integer from public.bitacora_campo b
       where b.aplicacion_id=a.id and b.tipo='incidencia') as incidencias,
     (select count(*)::integer from public.inspecciones_calidad i
       where i.aplicacion_id=a.id) as inspecciones_anteriores
  from public.aplicaciones_campo a
  join public.solicitudes s on s.id=a.solicitud_id
  join public.proyectos p on p.id=s.proyecto_id
  join public.clientes c on c.id=p.cliente_id
  where a.estado='pendiente_calidad' and a.avance_pct=100
    and s.estado='en_calidad'
  order by a.finalizacion_at desc,a.id desc limit 100
 ) t;
 return v_result;
end;
$$;
revoke all on function private.rf08_bandeja() from public,anon,authenticated;
grant execute on function private.rf08_bandeja() to authenticated;

-- Un expediente seguro para el inspector, el aplicador asignado y el cliente dueño.
create or replace function private.rf08_expedientes()
returns jsonb language plpgsql stable security definer set search_path=''
as $$
declare v_rol text;v_result jsonb;
begin
 if auth.uid() is null then raise exception 'Debes iniciar sesión' using errcode='42501';end if;
 select role into v_rol from public.profiles where id=auth.uid();
 if v_rol not in ('calidad','administrador','cliente','aplicador') then
   raise exception 'Sin permiso sobre expedientes de calidad' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(to_jsonb(t) order by t.fecha_finalizacion desc),'[]'::jsonb)
 into v_result from (
  select a.id as aplicacion_id,a.solicitud_id,a.aplicador_id,a.cliente_id,
    a.avance_pct,a.estado as estado_aplicacion,
    s.estado as estado_solicitud,a.finalizacion_at as fecha_finalizacion,
    p.nombre_proyecto,p.area_m2,p.tipo_superficie,p.condicion,p.ambiente,
    c.nombre_empresa,
    ol.referencia_despacho,
    coalesce(nullif(pr.full_name,''),'Aplicador '||left(a.aplicador_id::text,8)) as aplicador,
    coalesce((
      select jsonb_agg(jsonb_build_object(
       'id',b.id,'tipo',b.tipo,'avance_pct',b.avance_pct,'observaciones',b.observaciones,
       'foto_path',b.foto_path,'foto_mime',b.foto_mime,'created_at',b.created_at
      ) order by b.created_at asc,b.id asc)
      from public.bitacora_campo b where b.aplicacion_id=a.id
    ),'[]'::jsonb) as bitacora,
    coalesce((
      select jsonb_agg(jsonb_build_object(
        'id',i.id,'numero_inspeccion',i.numero_inspeccion,'decision',i.decision,
        'observaciones',i.observaciones,'criterios',i.criterios,
        'estado_solicitud_anterior',i.estado_solicitud_anterior,
        'estado_solicitud_nuevo',i.estado_solicitud_nuevo,
        'evidencias_examinadas',i.evidencias_examinadas,
        'incidencias_examinadas',i.incidencias_examinadas,
        'inspector_id',i.inspector_id,'created_at',i.created_at
      ) order by i.created_at asc,i.numero_inspeccion asc)
      from public.inspecciones_calidad i where i.aplicacion_id=a.id
    ),'[]'::jsonb) as inspecciones
  from public.aplicaciones_campo a
  join public.solicitudes s on s.id=a.solicitud_id
  join public.proyectos p on p.id=s.proyecto_id
  join public.clientes c on c.id=p.cliente_id
  join public.profiles pr on pr.id=a.aplicador_id
  join public.ordenes_logisticas ol on ol.id=a.orden_logistica_id
  where v_rol in ('calidad','administrador')
     or (v_rol='cliente' and a.cliente_id=auth.uid())
     or (v_rol='aplicador' and a.aplicador_id=auth.uid())
  order by a.finalizacion_at desc nulls last,a.id desc limit 100
 ) t;
 return v_result;
end;
$$;
revoke all on function private.rf08_expedientes() from public,anon,authenticated;
grant execute on function private.rf08_expedientes() to authenticated;

-- Dictamen y cambio de estado dentro de una sola transacción con bloqueo.
create or replace function private.rf08_resolver(
 p_aplicacion_id uuid,p_decision text,p_criterios jsonb,p_observaciones text
)
returns jsonb language plpgsql volatile security definer set search_path=''
as $$
declare
 v_app public.aplicaciones_campo%rowtype;
 v_sol public.solicitudes%rowtype;
 v_ins public.inspecciones_calidad%rowtype;
 v_key text;
 v_n integer;
 v_criterios_todos_ok boolean;
 v_estado_app_nuevo text;
 v_estado_sol_nuevo text;
 v_evidencias integer;
 v_incidencias integer;
begin
 if not private.rf08_es_inspector() then
   raise exception 'Solo calidad registra dictámenes' using errcode='42501';
 end if;
 if p_decision not in ('aprobar','solicitar_correccion','rechazar') then
   raise exception 'Decisión de calidad inválida' using errcode='22023';
 end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 15 and 2000 then
   raise exception 'Se requiere justificación técnica de 15 a 2000 caracteres' using errcode='22023';
 end if;
 if p_criterios is null or jsonb_typeof(p_criterios)<>'object' then
   raise exception 'Lista de verificación de calidad inválida' using errcode='22023';
 end if;
 foreach v_key in array array[
  'superficie_preparada','cobertura_adecuada','acabado_uniforme',
  'evidencias_verificadas','incidencias_gestionadas'
 ] loop
   if jsonb_typeof(p_criterios->v_key) is distinct from 'boolean' then
     raise exception 'Todos los criterios deben evaluarse como Sí o No' using errcode='22023';
   end if;
 end loop;
 if p_criterios <> jsonb_build_object(
  'superficie_preparada',p_criterios->'superficie_preparada',
  'cobertura_adecuada',p_criterios->'cobertura_adecuada',
  'acabado_uniforme',p_criterios->'acabado_uniforme',
  'evidencias_verificadas',p_criterios->'evidencias_verificadas',
  'incidencias_gestionadas',p_criterios->'incidencias_gestionadas'
 ) then
   raise exception 'Criterios desconocidos en el formulario' using errcode='22023';
 end if;
 v_criterios_todos_ok:=(
   select bool_and(value='true'::jsonb)
   from jsonb_each(p_criterios)
 );
 if p_decision='aprobar' and not v_criterios_todos_ok then
   raise exception 'No se puede aprobar con criterios incumplidos' using errcode='23514';
 end if;
 if p_decision in ('solicitar_correccion','rechazar') and v_criterios_todos_ok then
   raise exception 'Identifica al menos un criterio incumplido' using errcode='23514';
 end if;
 select * into v_app from public.aplicaciones_campo
 where id=p_aplicacion_id for update;
 if not found then raise exception 'Aplicación no encontrada' using errcode='42501';end if;
 select * into v_sol from public.solicitudes
 where id=v_app.solicitud_id for update;
 if v_app.estado<>'pendiente_calidad' or v_app.avance_pct<>100
    or v_sol.estado<>'en_calidad' or v_app.finalizacion_at is null then
   raise exception 'No está pendiente de inspección de calidad' using errcode='23514';
 end if;
 select count(*)::integer into v_evidencias from public.bitacora_campo
 where aplicacion_id=v_app.id and tipo='evidencia';
 select count(*)::integer into v_incidencias from public.bitacora_campo
 where aplicacion_id=v_app.id and tipo='incidencia';
 if p_decision='aprobar' and v_evidencias<1 then
   raise exception 'Aprobación requiere al menos una fotografía de campo' using errcode='23514';
 end if;
 select count(*)::integer+1 into v_n from public.inspecciones_calidad
 where aplicacion_id=v_app.id;
 if v_n>20 then raise exception 'Máximo de 20 inspecciones por aplicación' using errcode='23514';end if;
 v_estado_app_nuevo:=case p_decision
   when 'aprobar' then 'calidad_aprobada'
   when 'rechazar' then 'calidad_rechazada'
   else 'en_correccion' end;
 v_estado_sol_nuevo:=case p_decision
   when 'aprobar' then 'finalizada'
   when 'rechazar' then 'rechazada'
   else 'en_aplicacion' end;

 insert into public.inspecciones_calidad(
   aplicacion_id,solicitud_id,cliente_id,inspector_id,
   decision,criterios,observaciones,numero_inspeccion,
   estado_solicitud_anterior,estado_solicitud_nuevo,
   estado_aplicacion_anterior,estado_aplicacion_nuevo,
   evidencias_examinadas,incidencias_examinadas,es_demostrativo
 ) values (
   v_app.id,v_app.solicitud_id,v_app.cliente_id,auth.uid(),
   p_decision,p_criterios,btrim(p_observaciones),v_n,
   v_sol.estado,v_estado_sol_nuevo,v_app.estado,v_estado_app_nuevo,
   v_evidencias,v_incidencias,true
 ) returning * into v_ins;

 update public.aplicaciones_campo
 set estado=v_estado_app_nuevo,updated_at=now()
 where id=v_app.id;
 update public.solicitudes set estado=v_estado_sol_nuevo,updated_at=now()
 where id=v_sol.id;
 return jsonb_build_object(
  'inspeccion_id',v_ins.id,'numero_inspeccion',v_n,
  'aplicacion_id',v_app.id,'solicitud_id',v_sol.id,
  'decision',p_decision,'estado_aplicacion',v_estado_app_nuevo,
  'estado_solicitud',v_estado_sol_nuevo,'es_demostrativo',true
 );
end;
$$;
revoke all on function private.rf08_resolver(uuid,text,jsonb,text) from public,anon,authenticated;
grant execute on function private.rf08_resolver(uuid,text,jsonb,text) to authenticated;

-- Subsanación documentada: no elimina el dictamen ni retrocede porcentajes.
-- El 100% es avance del trabajo, NO una aprobación de calidad.
create or replace function private.rf08_subsanar(
 p_aplicacion_id uuid,p_observaciones text
)
returns jsonb language plpgsql volatile security definer set search_path=''
as $$
declare v_app public.aplicaciones_campo%rowtype;
 v_evento public.bitacora_campo%rowtype;
begin
 if auth.uid() is null or not exists(
  select 1 from public.profiles p
  where p.id=auth.uid() and p.role='aplicador'
 ) then raise exception 'Solo el aplicador asignado registra subsanaciones' using errcode='42501';end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 15 and 1500 then
  raise exception 'Se necesita una explicación de al menos 15 caracteres' using errcode='22023';
 end if;
 select * into v_app from public.aplicaciones_campo
 where id=p_aplicacion_id for update;
 if not found or v_app.aplicador_id<>auth.uid() then
  raise exception 'La aplicación no está asignada a tu cuenta' using errcode='42501';
 end if;
 if v_app.estado<>'en_correccion' or v_app.avance_pct<>100 then
  raise exception 'No hay correcciones pendientes en este trabajo' using errcode='23514';
 end if;
 update public.solicitudes
 set estado='en_calidad',updated_at=now()
 where id=v_app.solicitud_id and estado='en_aplicacion';
 if not found then
  raise exception 'Estado de solicitud incompatible con subsanación' using errcode='23514';
 end if;
 update public.aplicaciones_campo set estado='pendiente_calidad',updated_at=now()
 where id=v_app.id;
 insert into public.bitacora_campo(
  aplicacion_id,actor_id,tipo,avance_pct,observaciones
 ) values (v_app.id,auth.uid(),'subsanacion',100,btrim(p_observaciones))
 returning * into v_evento;
 return jsonb_build_object(
  'evento_id',v_evento.id,'aplicacion_id',v_app.id,
  'estado_aplicacion','pendiente_calidad','estado_solicitud','en_calidad'
 );
end;
$$;
revoke all on function private.rf08_subsanar(uuid,text) from public,anon,authenticated;
grant execute on function private.rf08_subsanar(uuid,text) to authenticated;

-- Extender únicamente las políticas y RPC de evidencia, sin conceder acceso a otro rol.
create or replace function private.rf07_storage_autorizado(
 p_aplicacion_id text,p_operacion text
)
returns boolean language sql stable security definer set search_path=''
as $$
 select auth.uid() is not null and exists(
  select 1 from public.aplicaciones_campo a
  join public.profiles p on p.id=auth.uid()
  where a.id::text=p_aplicacion_id
   and (
    (p_operacion in ('upload','delete') and p.role='aplicador'
     and a.aplicador_id=auth.uid()
     and a.estado in ('en_ejecucion','en_correccion'))
    or
    (p_operacion='read' and (
      (p.role='aplicador' and a.aplicador_id=auth.uid())
      or (p.role='cliente' and a.cliente_id=auth.uid())
      or p.role in ('logistica','administrador','calidad')
    ))
   )
 );
$$;
revoke all on function private.rf07_storage_autorizado(text,text) from public,anon,authenticated;
grant execute on function private.rf07_storage_autorizado(text,text) to authenticated;

create or replace function private.rf07_evidencia(
 p_aplicacion_id uuid,p_storage_path text,p_mime text,p_bytes integer,p_observaciones text
)
returns jsonb language plpgsql volatile security definer set search_path=''
as $$
declare v_app public.aplicaciones_campo%rowtype;v_event public.bitacora_campo%rowtype;
begin
 if auth.uid() is null or not exists(
  select 1 from public.profiles p where p.id=auth.uid() and p.role='aplicador'
 ) then raise exception 'Solo el aplicador registra evidencias' using errcode='42501';end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 10 and 1500
    or p_mime not in ('image/png','image/jpeg')
    or p_bytes is null or p_bytes not between 1 and 5242880 then
  raise exception 'Datos de fotografía u observaciones inválidos' using errcode='22023';
 end if;
 select * into v_app from public.aplicaciones_campo where id=p_aplicacion_id for update;
 if not found or v_app.aplicador_id<>auth.uid() then
  raise exception 'Trabajo no asignado' using errcode='42501';end if;
 if v_app.estado not in ('en_ejecucion','en_correccion') then
  raise exception 'Evidencia permitida solo en ejecución o corrección' using errcode='23514';end if;
 if p_storage_path not like auth.uid()::text || '/' || v_app.id::text || '/%'
   or p_storage_path !~ '^[a-f0-9-]{36}/[a-f0-9-]{36}/[a-f0-9-]{36}\.(jpg|png)$' then
  raise exception 'Ruta de evidencia incorrecta' using errcode='22023';end if;
 if (select count(*) from public.bitacora_campo
     where aplicacion_id=v_app.id and tipo='evidencia')>=10 then
  raise exception 'Límite de 10 fotografías por aplicación' using errcode='23514';end if;
 if not exists(
   select 1 from storage.objects o
   where o.bucket_id='colorlink-campo' and o.name=p_storage_path
     and o.owner_id=auth.uid()::text
 ) then raise exception 'Archivo no encontrado o ajeno a la cuenta' using errcode='42501';end if;
 insert into public.bitacora_campo(
  aplicacion_id,actor_id,tipo,avance_pct,observaciones,
  foto_path,foto_mime,foto_bytes
 ) values (v_app.id,auth.uid(),'evidencia',v_app.avance_pct,
           btrim(p_observaciones),p_storage_path,p_mime,p_bytes)
 returning * into v_event;
 return to_jsonb(v_event);
end;
$$;
revoke all on function private.rf07_evidencia(uuid,text,text,integer,text) from public,anon,authenticated;
grant execute on function private.rf07_evidencia(uuid,text,text,integer,text) to authenticated;

-- Wrappers de invocador. Los privilegios reales residen en el esquema privado.
create or replace function public.bandeja_calidad()
returns jsonb language sql stable security invoker set search_path=''
as $$select private.rf08_bandeja();$$;
revoke all on function public.bandeja_calidad() from public,anon,authenticated;
grant execute on function public.bandeja_calidad() to authenticated;

create or replace function public.expedientes_calidad()
returns jsonb language sql stable security invoker set search_path=''
as $$select private.rf08_expedientes();$$;
revoke all on function public.expedientes_calidad() from public,anon,authenticated;
grant execute on function public.expedientes_calidad() to authenticated;

create or replace function public.resolver_calidad(
 p_aplicacion_id uuid,p_decision text,p_criterios jsonb,p_observaciones text
)
returns jsonb language sql volatile security invoker set search_path=''
as $$select private.rf08_resolver(p_aplicacion_id,p_decision,p_criterios,p_observaciones);$$;
revoke all on function public.resolver_calidad(uuid,text,jsonb,text) from public,anon,authenticated;
grant execute on function public.resolver_calidad(uuid,text,jsonb,text) to authenticated;

create or replace function public.subsanar_calidad(
 p_aplicacion_id uuid,p_observaciones text
)
returns jsonb language sql volatile security invoker set search_path=''
as $$select private.rf08_subsanar(p_aplicacion_id,p_observaciones);$$;
revoke all on function public.subsanar_calidad(uuid,text) from public,anon,authenticated;
grant execute on function public.subsanar_calidad(uuid,text) to authenticated;
