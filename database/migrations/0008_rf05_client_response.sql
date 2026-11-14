-- RF-05.1: respuesta escrita del cliente a solicitudes de información/corrección.
-- La respuesta NO modifica parámetros técnicos ni crea una aprobación.
create table if not exists public.respuestas_revision_cliente (
    id uuid primary key default gen_random_uuid(),
    solicitud_id uuid not null references public.solicitudes(id) on delete restrict,
    revision_id uuid not null unique references public.revisiones_tecnicas(id) on delete restrict,
    cliente_id uuid not null references auth.users(id) on delete cascade,
    respuesta text not null check (char_length(btrim(respuesta)) between 10 and 3000),
    estado_anterior text not null check (estado_anterior = 'pendiente_informacion'),
    estado_nuevo text not null check (estado_nuevo = 'en_revision_tecnica'),
    created_at timestamptz not null default now()
);
create index if not exists idx_respuestas_cliente_solicitud
    on public.respuestas_revision_cliente (solicitud_id, created_at desc);
alter table public.respuestas_revision_cliente enable row level security;
revoke all on public.respuestas_revision_cliente from public, anon, authenticated;
-- Sin acceso directo a la tabla, únicamente por funciones verificadas por usuario.

create or replace function private.rf05_responder_cliente(
    p_solicitud_id uuid,
    p_respuesta text
)
returns jsonb
language plpgsql volatile security definer set search_path=''
as $$
declare
    v_s public.solicitudes%rowtype;
    v_ultima public.revisiones_tecnicas%rowtype;
    v_resp public.respuestas_revision_cliente%rowtype;
begin
    if auth.uid() is null or not exists (
        select 1 from public.profiles p
        where p.id=auth.uid() and p.role='cliente'
    ) then
        raise exception 'Solo el cliente autenticado puede responder'
            using errcode='42501';
    end if;
    if p_respuesta is null or char_length(btrim(p_respuesta)) not between 10 and 3000 then
        raise exception 'La respuesta debe tener entre 10 y 3000 caracteres'
            using errcode='22023';
    end if;

    -- Bloqueo transaccional: una revisión pendiente sólo puede responderse una vez.
    select * into v_s from public.solicitudes s
    where s.id=p_solicitud_id for update;
    if not found or v_s.usuario_id <> auth.uid() then
        raise exception 'Solicitud no encontrada o ajena al cliente'
            using errcode='42501';
    end if;
    if v_s.estado <> 'pendiente_informacion' then
        raise exception 'La solicitud no está pendiente de información'
            using errcode='23514';
    end if;
    select * into v_ultima from public.revisiones_tecnicas r
    where r.solicitud_id=v_s.id
    order by r.created_at desc,r.id desc limit 1;
    if not found or v_ultima.decision not in ('solicitar_informacion','solicitar_correccion') then
        raise exception 'No hay una solicitud de información activa'
            using errcode='23514';
    end if;
    if exists (
        select 1 from public.respuestas_revision_cliente r where r.revision_id=v_ultima.id
    ) then
        raise exception 'Esta solicitud de información ya fue respondida'
            using errcode='23514';
    end if;

    insert into public.respuestas_revision_cliente (
        solicitud_id,revision_id,cliente_id,respuesta,estado_anterior,estado_nuevo
    ) values (
        v_s.id,v_ultima.id,auth.uid(),btrim(p_respuesta),
        'pendiente_informacion','en_revision_tecnica'
    ) returning * into v_resp;

    update public.solicitudes
    set estado='en_revision_tecnica',updated_at=now()
    where id=v_s.id;

    return to_jsonb(v_resp);
end;
$$;

revoke all on function private.rf05_responder_cliente(uuid,text) from public, anon, authenticated;
grant execute on function private.rf05_responder_cliente(uuid,text) to authenticated;

create or replace function public.responder_revision_tecnica(
    p_solicitud_id uuid, p_respuesta text
)
returns jsonb
language sql volatile security invoker set search_path=''
as $$select private.rf05_responder_cliente(p_solicitud_id,p_respuesta);$$;
revoke all on function public.responder_revision_tecnica(uuid,text) from public, anon, authenticated;
grant execute on function public.responder_revision_tecnica(uuid,text) to authenticated;

-- Se amplía el detalle ya protegido por auth.uid() con las respuestas auditadas.
create or replace function private.rf05_detalle(p_solicitud_id uuid)
returns jsonb
language plpgsql stable security definer set search_path=''
as $$
declare
 v_s public.solicitudes%rowtype;
 v_result jsonb;
begin
 if auth.uid() is null then raise exception 'Sin sesión' using errcode='28000'; end if;
 select * into v_s from public.solicitudes where id=p_solicitud_id;
 if not found then raise exception 'Solicitud no encontrada' using errcode='42501'; end if;
 if v_s.usuario_id <> auth.uid() and not private.rf05_es_asesor() then
  raise exception 'Acceso a solicitud denegado' using errcode='42501';
 end if;
 select jsonb_build_object(
  'solicitud',to_jsonb(v_s),
  'proyecto',(select to_jsonb(p) from public.proyectos p where p.id=v_s.proyecto_id),
  'empresa',(select jsonb_build_object('nombre',c.nombre_empresa,'ciudad',c.ciudad)
     from public.clientes c join public.proyectos p on p.cliente_id=c.id
     where p.id=v_s.proyecto_id),
  'analisis',(select to_jsonb(a) from public.analisis_ia a
     where a.solicitud_id=v_s.id order by a.created_at desc,a.id desc limit 1),
  'calculo',(select to_jsonb(k) from public.calculos_materiales k
     where k.solicitud_id=v_s.id order by k.created_at desc,k.id desc limit 1),
  'inventario',(select to_jsonb(e) from public.evaluaciones_disponibilidad e
     where e.solicitud_id=v_s.id order by e.created_at desc,e.id desc limit 1),
  'respuestas_cliente',coalesce((
    select jsonb_agg(to_jsonb(rc) order by rc.created_at desc,rc.id desc)
    from public.respuestas_revision_cliente rc where rc.solicitud_id=v_s.id
  ),'[]'::jsonb),
  'revisiones',coalesce((
     select jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id desc)
     from public.revisiones_tecnicas t where t.solicitud_id=v_s.id
  ),'[]'::jsonb)
 ) into v_result;
 return v_result;
end;
$$;

-- Mantener permisos únicamente al usuario autenticado.
revoke all on function private.rf05_detalle(uuid) from public, anon;
grant execute on function private.rf05_detalle(uuid) to authenticated;
