-- Evaluador: se habilita EXCLUSIVAMENTE mediante SQL Editor tras auto-registro.
-- El disparador 0001 fija 'cliente' en usuarios nuevos; metadata nunca concede roles.
create schema if not exists private;
revoke all on schema private from public,anon,authenticated;
grant usage on schema private to authenticated;

create table if not exists private.evaluator_accounts (
 user_id uuid primary key references auth.users(id) on delete cascade,
 enabled boolean not null default true,
 granted_at timestamptz not null default now()
);
alter table private.evaluator_accounts enable row level security;
revoke all on private.evaluator_accounts from public,anon,authenticated;

create table if not exists private.evaluator_role_events (
 id bigint generated always as identity primary key,
 actor_id uuid not null references auth.users(id) on delete cascade,
 role_from text not null,
 role_to text not null,
 changed_at timestamptz not null default now()
);
create index if not exists idx_cl_evaluator_role_events_actor
 on private.evaluator_role_events(actor_id,changed_at desc);
alter table private.evaluator_role_events enable row level security;
revoke all on private.evaluator_role_events from public,anon,authenticated;

create or replace function private.cl_evaluator_is_allowed(p_user_id uuid)
returns boolean language sql stable security definer set search_path=''
as $$
 select p_user_id is not null
    and p_user_id = auth.uid()
    and exists(select 1 from private.evaluator_accounts e
     where e.user_id=p_user_id and e.enabled);
$$;
revoke all on function private.cl_evaluator_is_allowed(uuid) from public,anon,authenticated;
grant execute on function private.cl_evaluator_is_allowed(uuid) to authenticated;

create or replace function private.cl_evaluator_status()
returns jsonb language sql stable security definer set search_path=''
as $$
 select jsonb_build_object(
  'enabled',private.cl_evaluator_is_allowed(auth.uid()),
  'roles',case when private.cl_evaluator_is_allowed(auth.uid())
     then jsonb_build_array('cliente','especialista_tecnico','logistica','aplicador','calidad')
     else '[]'::jsonb end);
$$;
revoke all on function private.cl_evaluator_status() from public,anon,authenticated;
grant execute on function private.cl_evaluator_status() to authenticated;

create or replace function private.cl_evaluator_change_role(p_role text)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_user uuid:=auth.uid(); v_old text;
begin
 if v_user is null or not private.cl_evaluator_is_allowed(v_user) then
   raise exception 'Cuenta no habilitada para cambiar roles' using errcode='42501';
 end if;
 if p_role is null or p_role not in
   ('cliente','especialista_tecnico','logistica','aplicador','calidad') then
   raise exception 'Rol no permitido' using errcode='22023';
 end if;
 select p.role into v_old from public.profiles p
 where p.id=v_user for update;
 if not found then
   raise exception 'Perfil no encontrado' using errcode='42501';
 end if;
 if v_old is distinct from p_role then
   update public.profiles set role=p_role,updated_at=now() where id=v_user;
   insert into private.evaluator_role_events(actor_id,role_from,role_to)
     values(v_user,v_old,p_role);
 end if;
 return jsonb_build_object('role',p_role,'enabled',true);
end;
$$;
revoke all on function private.cl_evaluator_change_role(text) from public,anon,authenticated;
grant execute on function private.cl_evaluator_change_role(text) to authenticated;

create or replace function public.evaluator_status()
returns jsonb language sql stable security invoker set search_path=''
as $$ select private.cl_evaluator_status(); $$;
revoke all on function public.evaluator_status() from public,anon,authenticated;
grant execute on function public.evaluator_status() to authenticated;

create or replace function public.evaluator_change_role(p_role text)
returns jsonb language sql volatile security invoker set search_path=''
as $$ select private.cl_evaluator_change_role(p_role); $$;
revoke all on function public.evaluator_change_role(text) from public,anon,authenticated;
grant execute on function public.evaluator_change_role(text) to authenticated;

-- Evaluador autorizado puede asignarse su propio trabajo al ejercer Logística.
CREATE OR REPLACE FUNCTION private.rf07_aplicadores()
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_out jsonb;
begin
 if not private.rf07_es_logistica() then
  raise exception 'Solo logística consulta aplicadores' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(jsonb_build_object('id',p.id,'nombre',coalesce(nullif(p.full_name,''),'Aplicador '||left(p.id::text,8)))
  order by p.created_at),'[]'::jsonb)
 into v_out from public.profiles p where p.role='aplicador'
 or exists(select 1 from private.evaluator_accounts e
            where e.user_id=p.id and e.enabled);
 return v_out;
end;
$function$
;
CREATE OR REPLACE FUNCTION private.rf07_asignar(p_solicitud_id uuid, p_aplicador_id uuid, p_observaciones text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_s public.solicitudes%rowtype;v_orden public.ordenes_logisticas%rowtype;
 v_app public.aplicaciones_campo%rowtype;
begin
 if not private.rf07_es_logistica() then raise exception 'No autorizado para asignar' using errcode='42501';end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 10 and 1500 then
  raise exception 'Observaciones entre 10 y 1500 caracteres' using errcode='22023';end if;
 if not exists(select 1 from public.profiles p where p.id=p_aplicador_id
 and (p.role='aplicador' or exists(
   select 1 from private.evaluator_accounts e
   where e.user_id=p.id and e.enabled))) then
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
$function$
;
