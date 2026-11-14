-- RF-06: logística académica: reserva transaccional, preparación, despacho y cancelación.
-- Los envases, bodegas y lotes iniciales son demostrativos; NO son existencias de Pintuco.

create table if not exists public.ordenes_logisticas (
  id uuid primary key default gen_random_uuid(),
  solicitud_id uuid not null references public.solicitudes(id) on delete restrict,
  cliente_id uuid not null references auth.users(id) on delete restrict,
  calculo_id uuid not null references public.calculos_materiales(id) on delete restrict,
  producto_id uuid not null references public.catalogo_productos_tecnicos(id) on delete restrict,
  envases_requeridos integer not null check (envases_requeridos > 0),
  estado text not null default 'reservada'
    check (estado in ('reservada','preparada','despachada','cancelada')),
  es_demostrativo boolean not null default true check (es_demostrativo=true),
  referencia_despacho text,
  creado_por uuid not null references auth.users(id),
  actualizado_por uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists uq_orden_logistica_activa_por_solicitud
  on public.ordenes_logisticas(solicitud_id) where estado <> 'cancelada';
create index if not exists idx_ordenes_logisticas_cliente
  on public.ordenes_logisticas(cliente_id,created_at desc);

create table if not exists public.reservas_lotes_logistica (
  id uuid primary key default gen_random_uuid(),
  orden_id uuid not null references public.ordenes_logisticas(id) on delete restrict,
  lote_id uuid not null references public.lotes_inventario(id) on delete restrict,
  envases integer not null check (envases > 0),
  created_at timestamptz not null default now(),
  unique(orden_id,lote_id)
);

create table if not exists public.eventos_logisticos (
  id uuid primary key default gen_random_uuid(),
  orden_id uuid not null references public.ordenes_logisticas(id) on delete restrict,
  actor_id uuid not null references auth.users(id),
  accion text not null check (accion in ('reservar','preparar','despachar','cancelar')),
  estado_anterior text,
  estado_nuevo text not null,
  observaciones text not null check (char_length(btrim(observaciones)) between 10 and 1000),
  created_at timestamptz not null default now()
);
create index if not exists idx_eventos_logisticos_orden
  on public.eventos_logisticos(orden_id,created_at desc);

alter table public.ordenes_logisticas enable row level security;
alter table public.reservas_lotes_logistica enable row level security;
alter table public.eventos_logisticos enable row level security;
revoke all on public.ordenes_logisticas,public.reservas_lotes_logistica,
  public.eventos_logisticos from public,anon,authenticated;
-- Acceso a pedidos solo por RPC, con validación explícita de auth.uid().

create schema if not exists private;
revoke all on schema private from public,anon,authenticated;
grant usage on schema private to authenticated;

create or replace function private.rf06_es_logistica()
returns boolean
language sql stable security definer set search_path=''
as $$
 select auth.uid() is not null and exists(
  select 1 from public.profiles p
  where p.id=auth.uid() and p.role in ('logistica','administrador')
 );
$$;
revoke all on function private.rf06_es_logistica() from public,anon,authenticated;
grant execute on function private.rf06_es_logistica() to authenticated;

-- Cola de solicitudes con aprobación técnica y sin reserva activa.
create or replace function private.rf06_bandeja()
returns jsonb
language plpgsql stable security definer set search_path=''
as $$
declare v_out jsonb;
begin
 if not private.rf06_es_logistica() then
   raise exception 'Solo logística puede ver la bandeja' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(to_jsonb(t) order by t.fecha_solicitud desc),'[]'::jsonb)
 into v_out from (
   select s.id as solicitud_id,s.estado,s.created_at as fecha_solicitud,
          c.nombre_empresa,p.nombre_proyecto,p.ambiente,p.color_requerido,p.area_m2,
          k.id as calculo_id,k.envases as envases_requeridos,
          k.presentacion_litros,k.es_demostrativo,
          (select coalesce(sum(l.existencia_envases-l.reservado_envases),0)::integer
             from public.lotes_inventario l join public.bodegas b on b.id=l.bodega_id
             where l.producto_id=k.producto_id and l.estado='disponible'
               and b.activa and (l.fecha_vencimiento is null or l.fecha_vencimiento>=current_date)
          ) as disponibles_ahora
   from public.solicitudes s
   join public.proyectos p on p.id=s.proyecto_id
   join public.clientes c on c.id=p.cliente_id
   join lateral (
     select r.calculo_id from public.revisiones_tecnicas r
     where r.solicitud_id=s.id and r.decision='aprobar'
     order by r.created_at desc,r.id desc limit 1
   ) rev on true
   join public.calculos_materiales k on k.id=rev.calculo_id and k.solicitud_id=s.id
   where s.estado='aprobada'
   and not exists (
     select 1 from public.ordenes_logisticas ol
     where ol.solicitud_id=s.id and ol.estado<>'cancelada'
   )
   order by s.created_at desc limit 100
 ) t;
 return v_out;
end;
$$;
revoke all on function private.rf06_bandeja() from public,anon,authenticated;
grant execute on function private.rf06_bandeja() to authenticated;

-- Consulta de órdenes y eventos: logística ve todas, cliente ve exclusivamente las propias.
create or replace function private.rf06_listar()
returns jsonb
language plpgsql stable security definer set search_path=''
as $$
declare v_role text;v_out jsonb;
begin
 if auth.uid() is null then raise exception 'Sesión requerida' using errcode='42501';end if;
 select role into v_role from public.profiles where id=auth.uid();
 if v_role not in ('logistica','administrador','cliente') then
   raise exception 'Sin acceso al seguimiento' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc),'[]'::jsonb)
 into v_out from (
   select o.*, s.estado as estado_solicitud,p.nombre_proyecto,
          c.nombre_empresa,pt.nombre as producto,
          coalesce((
            select jsonb_agg(jsonb_build_object(
             'lote_id',l.id,'codigo_lote',l.codigo_lote,
             'bodega',b.nombre,'ciudad',b.ciudad,'ubicacion',l.ubicacion,
             'envases',rl.envases
            ) order by l.fecha_vencimiento asc nulls last,l.id)
            from public.reservas_lotes_logistica rl
            join public.lotes_inventario l on l.id=rl.lote_id
            join public.bodegas b on b.id=l.bodega_id
            where rl.orden_id=o.id
          ),'[]'::jsonb) as lotes,
          coalesce((
            select jsonb_agg(jsonb_build_object(
              'accion',e.accion,'estado_anterior',e.estado_anterior,
              'estado_nuevo',e.estado_nuevo,'observaciones',e.observaciones,
              'created_at',e.created_at
            ) order by e.created_at desc,e.id desc)
            from public.eventos_logisticos e where e.orden_id=o.id
          ),'[]'::jsonb) as eventos
   from public.ordenes_logisticas o
   join public.solicitudes s on s.id=o.solicitud_id
   join public.proyectos p on p.id=s.proyecto_id
   join public.clientes c on c.id=p.cliente_id
   join public.catalogo_productos_tecnicos pt on pt.id=o.producto_id
   where v_role in ('logistica','administrador') or o.cliente_id=auth.uid()
   order by o.created_at desc limit 100
 ) t;
 return v_out;
end;
$$;
revoke all on function private.rf06_listar() from public,anon,authenticated;
grant execute on function private.rf06_listar() to authenticated;

-- Reserva FEFO estrictamente atómica. Nunca descuenta existencia física.
create or replace function private.rf06_reservar(
 p_solicitud_id uuid,p_observaciones text
)
returns jsonb
language plpgsql volatile security definer set search_path=''
as $$
declare
 v_s public.solicitudes%rowtype;
 v_orden public.ordenes_logisticas%rowtype;
 v_calc public.calculos_materiales%rowtype;
 v_aprobacion public.revisiones_tecnicas%rowtype;
 v_lote record;
 v_pendiente integer;
 v_tomar integer;
 v_ubicados integer:=0;
begin
 if not private.rf06_es_logistica() then
   raise exception 'No autorizado para reservar' using errcode='42501';
 end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 10 and 1000 then
   raise exception 'Incluye observaciones entre 10 y 1000 caracteres' using errcode='22023';
 end if;
 select * into v_s from public.solicitudes
 where id=p_solicitud_id for update;
 if not found then raise exception 'Solicitud inexistente' using errcode='42501';end if;
 -- Reintentos de red son idempotentes y no vuelven a descontar saldo.
 select * into v_orden from public.ordenes_logisticas
 where solicitud_id=p_solicitud_id and estado<>'cancelada'
 order by created_at desc limit 1 for update;
 if found then return to_jsonb(v_orden); end if;
 if v_s.estado <> 'aprobada' then
   raise exception 'La solicitud debe estar aprobada antes de reservar' using errcode='23514';
 end if;
 select * into v_aprobacion from public.revisiones_tecnicas
 where solicitud_id=v_s.id and decision='aprobar'
 order by created_at desc,id desc limit 1;
 if not found or v_aprobacion.calculo_id is null then
   raise exception 'Aprobación sin cálculo vinculado' using errcode='23514';
 end if;
 select * into v_calc from public.calculos_materiales
 where id=v_aprobacion.calculo_id and solicitud_id=v_s.id;
 if not found or v_calc.envases<=0 then
   raise exception 'No hay cálculo válido para reservar' using errcode='23514';
 end if;
 -- En esta versión solo se permite operación académica con lotes demostrativos.
 if not v_calc.es_demostrativo then
   raise exception 'RF-06 habilitado solo para entorno demostrativo' using errcode='23514';
 end if;
 v_pendiente:=v_calc.envases;
 insert into public.ordenes_logisticas (
   solicitud_id,cliente_id,calculo_id,producto_id,envases_requeridos,
   creado_por,actualizado_por,es_demostrativo
 ) values (
   v_s.id,v_s.usuario_id,v_calc.id,v_calc.producto_id,v_calc.envases,
   auth.uid(),auth.uid(),true
 ) returning * into v_orden;

 for v_lote in
   select l.id,l.existencia_envases,l.reservado_envases
   from public.lotes_inventario l join public.bodegas b on b.id=l.bodega_id
   where l.producto_id=v_calc.producto_id and l.estado='disponible'
     and l.es_demostrativo and b.es_demostrativo and b.activa
     and (l.fecha_vencimiento is null or l.fecha_vencimiento>=current_date)
   order by l.fecha_vencimiento asc nulls last,l.created_at,l.id
   for update of l
 loop
   if v_pendiente<=0 then exit; end if;
   v_tomar:=least(v_pendiente,v_lote.existencia_envases-v_lote.reservado_envases);
   if v_tomar<=0 then continue;end if;
   update public.lotes_inventario
   set reservado_envases=reservado_envases+v_tomar
   where id=v_lote.id
     and existencia_envases-reservado_envases>=v_tomar;
   if not found then raise exception 'Cambio concurrente en stock' using errcode='23514';end if;
   insert into public.reservas_lotes_logistica(orden_id,lote_id,envases)
     values (v_orden.id,v_lote.id,v_tomar);
   v_ubicados:=v_ubicados+v_tomar;
   v_pendiente:=v_pendiente-v_tomar;
 end loop;
 if v_pendiente<>0 or v_ubicados<>v_calc.envases then
   raise exception 'Inventario insuficiente: no se reservó ningún envase' using errcode='23514';
 end if;
 update public.solicitudes set estado='en_logistica',updated_at=now()
 where id=v_s.id;
 insert into public.eventos_logisticos(
   orden_id,actor_id,accion,estado_anterior,estado_nuevo,observaciones
 ) values (v_orden.id,auth.uid(),'reservar',null,'reservada',btrim(p_observaciones));
 return to_jsonb(v_orden);
end;
$$;
revoke all on function private.rf06_reservar(uuid,text) from public,anon,authenticated;
grant execute on function private.rf06_reservar(uuid,text) to authenticated;

-- Preparar, despachar o cancelar de manera auditada y transaccional.
create or replace function private.rf06_accion(
 p_orden_id uuid,p_accion text,p_observaciones text
)
returns jsonb
language plpgsql volatile security definer set search_path=''
as $$
declare
 v_orden public.ordenes_logisticas%rowtype;
 v_reserva record;
 v_ant text;
 v_nuevo text;
begin
 if not private.rf06_es_logistica() then
   raise exception 'No autorizado para operación logística' using errcode='42501';
 end if;
 if p_accion not in ('preparar','despachar','cancelar') then
   raise exception 'Acción logística desconocida' using errcode='22023';
 end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 10 and 1000 then
   raise exception 'Incluye observaciones de 10 a 1000 caracteres' using errcode='22023';
 end if;
 select * into v_orden from public.ordenes_logisticas where id=p_orden_id for update;
 if not found then raise exception 'Orden no encontrada' using errcode='42501';end if;
 -- Los reintentos de operaciones completadas retornan la misma orden.
 if (p_accion='preparar' and v_orden.estado='preparada')
    or (p_accion='despachar' and v_orden.estado='despachada')
    or (p_accion='cancelar' and v_orden.estado='cancelada') then
     return to_jsonb(v_orden);
 end if;
 if p_accion='preparar' and v_orden.estado<>'reservada' then
   raise exception 'Solo órdenes reservadas pueden prepararse' using errcode='23514';
 end if;
 if p_accion='despachar' and v_orden.estado<>'preparada' then
   raise exception 'Se requiere preparación antes de despachar' using errcode='23514';
 end if;
 if p_accion='cancelar' and v_orden.estado not in ('reservada','preparada') then
   raise exception 'No se puede cancelar una orden despachada' using errcode='23514';
 end if;
 v_ant:=v_orden.estado;
 v_nuevo:=case p_accion when 'preparar' then 'preparada'
   when 'despachar' then 'despachada' else 'cancelada' end;

 if p_accion in ('despachar','cancelar') then
   for v_reserva in
     select r.lote_id,r.envases,l.estado,l.fecha_vencimiento,b.activa
     from public.reservas_lotes_logistica r
     join public.lotes_inventario l on l.id=r.lote_id
     join public.bodegas b on b.id=l.bodega_id
     where r.orden_id=v_orden.id order by r.lote_id
     for update of l
   loop
     if p_accion='despachar' and
        (v_reserva.estado<>'disponible'
         or (v_reserva.fecha_vencimiento is not null
             and v_reserva.fecha_vencimiento<current_date)
         or not v_reserva.activa) then
       raise exception 'Lote no apto para despacho' using errcode='23514';
     end if;
     if p_accion='despachar' then
       update public.lotes_inventario
       set reservado_envases=reservado_envases-v_reserva.envases,
           existencia_envases=existencia_envases-v_reserva.envases
       where id=v_reserva.lote_id and reservado_envases>=v_reserva.envases
         and existencia_envases>=v_reserva.envases;
     else
       update public.lotes_inventario
       set reservado_envases=reservado_envases-v_reserva.envases
       where id=v_reserva.lote_id and reservado_envases>=v_reserva.envases;
     end if;
     if not found then
       raise exception 'Saldo de lotes incompatible; operación revertida' using errcode='23514';
     end if;
   end loop;
 end if;
 update public.ordenes_logisticas
 set estado=v_nuevo,actualizado_por=auth.uid(),updated_at=now(),
     referencia_despacho=case when p_accion='despachar'
       then 'CL-DEMO-' || upper(substr(replace(id::text,'-',''),1,10))
       else referencia_despacho end
 where id=v_orden.id returning * into v_orden;
 update public.solicitudes
 set estado=case when p_accion='despachar' then 'en_aplicacion'
   when p_accion='cancelar' then 'aprobada' else 'en_logistica' end,
     updated_at=now()
 where id=v_orden.solicitud_id;
 insert into public.eventos_logisticos(
   orden_id,actor_id,accion,estado_anterior,estado_nuevo,observaciones
 ) values (v_orden.id,auth.uid(),p_accion,v_ant,v_nuevo,btrim(p_observaciones));
 return to_jsonb(v_orden);
end;
$$;
revoke all on function private.rf06_accion(uuid,text,text) from public,anon,authenticated;
grant execute on function private.rf06_accion(uuid,text,text) to authenticated;

-- API pública únicamente con SECURITY INVOKER y roles authenticated.
create or replace function public.bandeja_logistica()
returns jsonb language sql stable security invoker set search_path=''
as $$ select private.rf06_bandeja(); $$;
revoke all on function public.bandeja_logistica() from public,anon,authenticated;
grant execute on function public.bandeja_logistica() to authenticated;

create or replace function public.listar_ordenes_logisticas()
returns jsonb language sql stable security invoker set search_path=''
as $$ select private.rf06_listar(); $$;
revoke all on function public.listar_ordenes_logisticas() from public,anon,authenticated;
grant execute on function public.listar_ordenes_logisticas() to authenticated;

create or replace function public.reservar_logistica(
 p_solicitud_id uuid,p_observaciones text
)
returns jsonb language sql volatile security invoker set search_path=''
as $$ select private.rf06_reservar(p_solicitud_id,p_observaciones); $$;
revoke all on function public.reservar_logistica(uuid,text) from public,anon,authenticated;
grant execute on function public.reservar_logistica(uuid,text) to authenticated;

create or replace function public.accion_logistica(
 p_orden_id uuid,p_accion text,p_observaciones text
)
returns jsonb language sql volatile security invoker set search_path=''
as $$ select private.rf06_accion(p_orden_id,p_accion,p_observaciones); $$;
revoke all on function public.accion_logistica(uuid,text,text) from public,anon,authenticated;
grant execute on function public.accion_logistica(uuid,text,text) to authenticated;
