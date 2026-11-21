-- RF-07: ejecución en campo, avances, incidencias, evidencias y remisión a calidad.
-- Módulo académico: ninguna acción representa una visita o aplicación física real.
create table public.aplicaciones_campo (
  id uuid primary key default gen_random_uuid(),
  solicitud_id uuid not null unique references public.solicitudes(id) on delete restrict,
  orden_logistica_id uuid not null unique references public.ordenes_logisticas(id) on delete restrict,
  cliente_id uuid not null references auth.users(id) on delete restrict,
  aplicador_id uuid not null references auth.users(id) on delete restrict,
  asignado_por uuid not null references auth.users(id) on delete restrict,
  estado text not null default 'asignada'
    check (estado in ('asignada','en_ejecucion','pendiente_calidad')),
  avance_pct integer not null default 0 check (avance_pct between 0 and 100),
  inicio_at timestamptz,
  finalizacion_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (estado <> 'asignada' or (avance_pct = 0 and inicio_at is null)),
  check (estado <> 'pendiente_calidad' or (avance_pct=100 and finalizacion_at is not null))
);
create index idx_aplicaciones_aplicador on public.aplicaciones_campo(aplicador_id,created_at desc);
create index idx_aplicaciones_cliente on public.aplicaciones_campo(cliente_id,created_at desc);

create table public.bitacora_campo (
  id uuid primary key default gen_random_uuid(),
  aplicacion_id uuid not null references public.aplicaciones_campo(id) on delete restrict,
  actor_id uuid not null references auth.users(id) on delete restrict,
  tipo text not null check (tipo in ('asignacion','inicio','avance','incidencia','evidencia','finalizacion')),
  avance_pct integer not null check (avance_pct between 0 and 100),
  observaciones text not null check (char_length(btrim(observaciones)) between 10 and 1500),
  foto_path text unique,
  foto_mime text check (foto_mime is null or foto_mime in ('image/jpeg','image/png')),
  foto_bytes integer check (foto_bytes is null or foto_bytes between 1 and 5242880),
  created_at timestamptz not null default now(),
  check (
    (tipo='evidencia' and foto_path is not null and foto_mime is not null and foto_bytes is not null)
    or
    (tipo<>'evidencia' and foto_path is null and foto_mime is null and foto_bytes is null)
  )
);
create index idx_bitacora_aplicacion on public.bitacora_campo(aplicacion_id,created_at desc);

alter table public.aplicaciones_campo enable row level security;
alter table public.bitacora_campo enable row level security;
revoke all on public.aplicaciones_campo,public.bitacora_campo from public,anon,authenticated;
-- Todas las lecturas/escrituras operativas usan RPC con ownership y rol validado.

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('colorlink-campo','colorlink-campo',false,5242880,array['image/jpeg','image/png'])
on conflict (id) do nothing;

create policy "RF07 Aplicador sube evidencia a su aplicacion" on storage.objects
for insert to authenticated with check (
  bucket_id='colorlink-campo'
  and (storage.foldername(name))[1]=(select auth.uid())::text
  and exists(
    select 1 from public.aplicaciones_campo a
    where a.id::text=(storage.foldername(name))[2]
    and a.aplicador_id=(select auth.uid())
    and a.estado='en_ejecucion'
  )
);
-- Esta consulta de autorización usa una tabla sin SELECT Data API.
-- Evaluar via función privada verificable y exponer solo un predicado BOOLEAN.
-- Las políticas se sustituyen más abajo por helper seguro.

create or replace function private.rf07_storage_autorizado(p_aplicacion_id text,p_operacion text)
returns boolean language sql stable security definer set search_path=''
as $$
 select auth.uid() is not null and exists(
  select 1 from public.aplicaciones_campo a
  join public.profiles p on p.id=auth.uid()
  where a.id::text=p_aplicacion_id
   and (
    (p_operacion in ('upload','delete') and p.role='aplicador'
     and a.aplicador_id=auth.uid() and a.estado='en_ejecucion')
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

drop policy "RF07 Aplicador sube evidencia a su aplicacion" on storage.objects;
create policy "RF07 Campo fotos upload" on storage.objects
 for insert to authenticated with check(
   bucket_id='colorlink-campo'
   and (storage.foldername(name))[1]=(select auth.uid())::text
   and private.rf07_storage_autorizado((storage.foldername(name))[2],'upload')
 );
create policy "RF07 Campo fotos read" on storage.objects
 for select to authenticated using(
   bucket_id='colorlink-campo'
   and private.rf07_storage_autorizado((storage.foldername(name))[2],'read')
 );
create policy "RF07 Campo fotos delete" on storage.objects
 for delete to authenticated using(
   bucket_id='colorlink-campo'
   and (storage.foldername(name))[1]=(select auth.uid())::text
   and private.rf07_storage_autorizado((storage.foldername(name))[2],'delete')
 );

create or replace function private.rf07_es_logistica()
returns boolean language sql stable security definer set search_path=''
as $$
 select auth.uid() is not null and exists(
  select 1 from public.profiles p where p.id=auth.uid()
  and p.role in ('logistica','administrador')
 );
$$;
revoke all on function private.rf07_es_logistica() from public,anon,authenticated;
grant execute on function private.rf07_es_logistica() to authenticated;

create or replace function private.rf07_aplicadores()
returns jsonb language plpgsql stable security definer set search_path=''
as $$
declare v_out jsonb;
begin
 if not private.rf07_es_logistica() then
  raise exception 'Solo logística consulta aplicadores' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(jsonb_build_object('id',p.id,'nombre',coalesce(nullif(p.full_name,''),'Aplicador '||left(p.id::text,8)))
  order by p.created_at),'[]'::jsonb)
 into v_out from public.profiles p where p.role='aplicador';
 return v_out;
end;
$$;
revoke all on function private.rf07_aplicadores() from public,anon,authenticated;
grant execute on function private.rf07_aplicadores() to authenticated;

create or replace function private.rf07_elegibles()
returns jsonb language plpgsql stable security definer set search_path=''
as $$
declare v_out jsonb;
begin
 if not private.rf07_es_logistica() then
  raise exception 'Solo logística asigna trabajos' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(to_jsonb(t) order by t.fecha_despacho desc),'[]'::jsonb) into v_out
 from (
  select s.id as solicitud_id,s.estado,ol.id as orden_logistica_id,
         ol.referencia_despacho,ol.updated_at as fecha_despacho,
         p.nombre_proyecto,p.area_m2,p.ambiente,p.tipo_superficie,
         c.nombre_empresa,c.ciudad
  from public.solicitudes s
  join public.ordenes_logisticas ol on ol.solicitud_id=s.id
     and ol.estado='despachada' and ol.es_demostrativo
  join public.proyectos p on p.id=s.proyecto_id
  join public.clientes c on c.id=p.cliente_id
  where s.estado='en_aplicacion'
    and not exists(select 1 from public.aplicaciones_campo a where a.solicitud_id=s.id)
  order by ol.updated_at desc limit 100
 ) t;
 return v_out;
end;
$$;
revoke all on function private.rf07_elegibles() from public,anon,authenticated;
grant execute on function private.rf07_elegibles() to authenticated;

create or replace function private.rf07_listar()
returns jsonb language plpgsql stable security definer set search_path=''
as $$
declare v_role text;v_out jsonb;
begin
 if auth.uid() is null then raise exception 'Autenticación requerida' using errcode='42501';end if;
 select p.role into v_role from public.profiles p where p.id=auth.uid();
 if v_role not in ('logistica','administrador','aplicador','cliente','calidad') then
  raise exception 'Rol sin acceso a trabajos de campo' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc),'[]'::jsonb) into v_out
 from (
  select a.id,a.solicitud_id,a.orden_logistica_id,a.cliente_id,a.aplicador_id,
     a.estado,a.avance_pct,a.inicio_at,a.finalizacion_at,a.created_at,
     p.nombre_proyecto,p.area_m2,p.tipo_superficie,p.ambiente,p.condicion,
     c.nombre_empresa,coalesce(nullif(pr.full_name,''),'Aplicador '||left(a.aplicador_id::text,8)) as aplicador,
     (select ol.referencia_despacho from public.ordenes_logisticas ol where ol.id=a.orden_logistica_id) as referencia_despacho,
     coalesce((
       select jsonb_agg(jsonb_build_object(
        'id',b.id,'tipo',b.tipo,'avance_pct',b.avance_pct,
        'observaciones',b.observaciones,'foto_path',b.foto_path,
        'foto_mime',b.foto_mime,'created_at',b.created_at
       ) order by b.created_at desc,b.id desc)
       from public.bitacora_campo b where b.aplicacion_id=a.id
     ),'[]'::jsonb) as bitacora
  from public.aplicaciones_campo a
  join public.solicitudes s on s.id=a.solicitud_id
  join public.proyectos p on p.id=s.proyecto_id
  join public.clientes c on c.id=p.cliente_id
  join public.profiles pr on pr.id=a.aplicador_id
  where v_role in ('logistica','administrador','calidad')
    or (v_role='aplicador' and a.aplicador_id=auth.uid())
    or (v_role='cliente' and a.cliente_id=auth.uid())
  order by a.created_at desc limit 100
 ) t;
 return v_out;
end;
$$;
revoke all on function private.rf07_listar() from public,anon,authenticated;
grant execute on function private.rf07_listar() to authenticated;

create or replace function private.rf07_asignar(
 p_solicitud_id uuid,p_aplicador_id uuid,p_observaciones text
)
returns jsonb language plpgsql volatile security definer set search_path=''
as $$
declare v_s public.solicitudes%rowtype;v_orden public.ordenes_logisticas%rowtype;
 v_app public.aplicaciones_campo%rowtype;
begin
 if not private.rf07_es_logistica() then raise exception 'No autorizado para asignar' using errcode='42501';end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 10 and 1500 then
  raise exception 'Observaciones entre 10 y 1500 caracteres' using errcode='22023';end if;
 if not exists(select 1 from public.profiles p where p.id=p_aplicador_id and p.role='aplicador') then
  raise exception 'Se requiere un usuario con rol aplicador' using errcode='22023';end if;
 select * into v_s from public.solicitudes where id=p_solicitud_id for update;
 if not found then raise exception 'Solicitud inexistente' using errcode='42501';end if;
 select * into v_app from public.aplicaciones_campo where solicitud_id=p_solicitud_id;
 if found then
  if v_app.aplicador_id=p_aplicador_id then return to_jsonb(v_app);end if;
  raise exception 'La solicitud ya está asignada a otro aplicador' using errcode='23514';
 end if;
 if v_s.estado<>'en_aplicacion' then
  raise exception 'Solo se asignan solicitudes despachadas en aplicación' using errcode='23514';
 end if;
 select * into v_orden from public.ordenes_logisticas
 where solicitud_id=v_s.id and estado='despachada' and es_demostrativo=true
 order by updated_at desc limit 1;
 if not found then raise exception 'No existe despacho confirmado' using errcode='23514';end if;
 insert into public.aplicaciones_campo(solicitud_id,orden_logistica_id,cliente_id,
     aplicador_id,asignado_por)
 values(v_s.id,v_orden.id,v_s.usuario_id,p_aplicador_id,auth.uid())
 returning * into v_app;
 insert into public.bitacora_campo(aplicacion_id,actor_id,tipo,avance_pct,observaciones)
 values(v_app.id,auth.uid(),'asignacion',0,btrim(p_observaciones));
 return to_jsonb(v_app);
end;
$$;
revoke all on function private.rf07_asignar(uuid,uuid,text) from public,anon,authenticated;
grant execute on function private.rf07_asignar(uuid,uuid,text) to authenticated;

create or replace function private.rf07_evento(
 p_aplicacion_id uuid,p_tipo text,p_avance_pct integer,p_observaciones text
)
returns jsonb language plpgsql volatile security definer set search_path=''
as $$
declare v_app public.aplicaciones_campo%rowtype;v_event public.bitacora_campo%rowtype;
v_pct integer;v_estado text;
begin
 if auth.uid() is null or not exists(
  select 1 from public.profiles p where p.id=auth.uid() and p.role='aplicador'
 ) then raise exception 'Solo el aplicador registra actividades' using errcode='42501';end if;
 if p_tipo not in ('inicio','avance','incidencia','finalizacion') then
  raise exception 'Tipo de evento no permitido' using errcode='22023';end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 10 and 1500 then
  raise exception 'Observaciones entre 10 y 1500 caracteres' using errcode='22023';end if;
 select * into v_app from public.aplicaciones_campo where id=p_aplicacion_id for update;
 if not found or v_app.aplicador_id<>auth.uid() then
  raise exception 'Trabajo no asignado a este aplicador' using errcode='42501';end if;

 if p_tipo='inicio' then
   if v_app.estado<>'asignada' or p_avance_pct is not null then
     raise exception 'Solo un trabajo asignado puede iniciarse' using errcode='23514';end if;
   v_pct:=0;v_estado:='en_ejecucion';
 elsif p_tipo='avance' then
   if v_app.estado<>'en_ejecucion' or p_avance_pct is null
       or p_avance_pct<=v_app.avance_pct or p_avance_pct>99 then
     raise exception 'Avance debe aumentar y estar entre 1 y 99' using errcode='23514';end if;
   v_pct:=p_avance_pct;v_estado:=v_app.estado;
 elsif p_tipo='incidencia' then
   if v_app.estado<>'en_ejecucion' or p_avance_pct is not null then
     raise exception 'Solo se registran incidencias durante la ejecución' using errcode='23514';end if;
   v_pct:=v_app.avance_pct;v_estado:=v_app.estado;
 else
   if v_app.estado<>'en_ejecucion' or v_app.avance_pct<1 or p_avance_pct is not null then
     raise exception 'Primero inicia y registra algún avance antes de finalizar' using errcode='23514';end if;
   v_pct:=100;v_estado:='pendiente_calidad';
 end if;

 update public.aplicaciones_campo
 set avance_pct=v_pct,estado=v_estado,updated_at=now(),
     inicio_at=case when p_tipo='inicio' then now() else inicio_at end,
     finalizacion_at=case when p_tipo='finalizacion' then now() else finalizacion_at end
 where id=v_app.id;

 if p_tipo='finalizacion' then
   update public.solicitudes set estado='en_calidad',updated_at=now()
   where id=v_app.solicitud_id and estado='en_aplicacion';
   if not found then raise exception 'Estado de solicitud incompatible para calidad' using errcode='23514';end if;
 end if;
 insert into public.bitacora_campo(aplicacion_id,actor_id,tipo,avance_pct,observaciones)
 values(v_app.id,auth.uid(),p_tipo,v_pct,btrim(p_observaciones))
 returning * into v_event;
 return jsonb_build_object(
  'evento',to_jsonb(v_event),'estado_aplicacion',v_estado,'avance_pct',v_pct
 );
end;
$$;
revoke all on function private.rf07_evento(uuid,text,integer,text) from public,anon,authenticated;
grant execute on function private.rf07_evento(uuid,text,integer,text) to authenticated;

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
 if v_app.estado<>'en_ejecucion' then
  raise exception 'Las evidencias se registran únicamente en ejecución' using errcode='23514';end if;
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
 ) then
  raise exception 'Archivo no encontrado o ajeno a la cuenta' using errcode='42501';end if;
 insert into public.bitacora_campo(aplicacion_id,actor_id,tipo,avance_pct,
   observaciones,foto_path,foto_mime,foto_bytes)
 values(v_app.id,auth.uid(),'evidencia',v_app.avance_pct,
   btrim(p_observaciones),p_storage_path,p_mime,p_bytes)
 returning * into v_event;
 return to_jsonb(v_event);
end;
$$;
revoke all on function private.rf07_evidencia(uuid,text,text,integer,text) from public,anon,authenticated;
grant execute on function private.rf07_evidencia(uuid,text,text,integer,text) to authenticated;

-- Wrappers invocadores expuestos por PostgREST; las funciones privilegiadas quedan privadas.
create or replace function public.campo_aplicadores()
returns jsonb language sql stable security invoker set search_path=''
as $$ select private.rf07_aplicadores(); $$;
revoke all on function public.campo_aplicadores() from public,anon,authenticated;
grant execute on function public.campo_aplicadores() to authenticated;

create or replace function public.campo_elegibles()
returns jsonb language sql stable security invoker set search_path=''
as $$ select private.rf07_elegibles(); $$;
revoke all on function public.campo_elegibles() from public,anon,authenticated;
grant execute on function public.campo_elegibles() to authenticated;

create or replace function public.campo_listar()
returns jsonb language sql stable security invoker set search_path=''
as $$ select private.rf07_listar(); $$;
revoke all on function public.campo_listar() from public,anon,authenticated;
grant execute on function public.campo_listar() to authenticated;

create or replace function public.campo_asignar(
 p_solicitud_id uuid,p_aplicador_id uuid,p_observaciones text
)
returns jsonb language sql volatile security invoker set search_path=''
as $$ select private.rf07_asignar(p_solicitud_id,p_aplicador_id,p_observaciones); $$;
revoke all on function public.campo_asignar(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.campo_asignar(uuid,uuid,text) to authenticated;

create or replace function public.campo_evento(
 p_aplicacion_id uuid,p_tipo text,p_avance_pct integer,p_observaciones text
)
returns jsonb language sql volatile security invoker set search_path=''
as $$ select private.rf07_evento(p_aplicacion_id,p_tipo,p_avance_pct,p_observaciones); $$;
revoke all on function public.campo_evento(uuid,text,integer,text) from public,anon,authenticated;
grant execute on function public.campo_evento(uuid,text,integer,text) to authenticated;

create or replace function public.campo_evidencia(
 p_aplicacion_id uuid,p_storage_path text,p_mime text,p_bytes integer,p_observaciones text
)
returns jsonb language sql volatile security invoker set search_path=''
as $$ select private.rf07_evidencia(p_aplicacion_id,p_storage_path,p_mime,p_bytes,p_observaciones); $$;
revoke all on function public.campo_evidencia(uuid,text,text,integer,text) from public,anon,authenticated;
grant execute on function public.campo_evidencia(uuid,text,text,integer,text) to authenticated;
