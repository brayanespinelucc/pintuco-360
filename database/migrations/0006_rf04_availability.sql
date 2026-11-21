-- RF-04: existencias por bodegas/lotes, consulta segura y propuesta NO reservada.
-- Los valores semilla son académicos, no inventario real de Pintuco.
create table if not exists public.bodegas (
    id uuid primary key default gen_random_uuid(),
    codigo text not null unique check (char_length(codigo) between 3 and 30),
    nombre text not null check (char_length(nombre) between 4 and 120),
    ciudad text not null check (char_length(ciudad) between 2 and 100),
    activa boolean not null default true,
    es_demostrativo boolean not null default true,
    created_at timestamptz not null default now()
);
create table if not exists public.lotes_inventario (
    id uuid primary key default gen_random_uuid(),
    producto_id uuid not null references public.catalogo_productos_tecnicos(id) on delete restrict,
    bodega_id uuid not null references public.bodegas(id) on delete restrict,
    codigo_lote text not null unique check (char_length(codigo_lote) between 3 and 80),
    ubicacion text not null check (char_length(ubicacion) between 2 and 50),
    existencia_envases integer not null default 0 check (existencia_envases >= 0),
    reservado_envases integer not null default 0 check (
        reservado_envases >= 0 and reservado_envases <= existencia_envases
    ),
    estado text not null default 'disponible' check (
        estado in ('disponible', 'bloqueado', 'agotado')
    ),
    fecha_vencimiento date,
    es_demostrativo boolean not null default true,
    created_at timestamptz not null default now()
);
create index if not exists idx_lotes_producto_estado
    on public.lotes_inventario (producto_id, estado, fecha_vencimiento);

create table if not exists public.evaluaciones_disponibilidad (
    id uuid primary key default gen_random_uuid(),
    calculo_id uuid not null references public.calculos_materiales(id) on delete restrict,
    solicitud_id uuid not null references public.solicitudes(id) on delete restrict,
    usuario_id uuid not null references auth.users(id) on delete cascade,
    producto_id uuid not null references public.catalogo_productos_tecnicos(id) on delete restrict,
    envases_requeridos integer not null check (envases_requeridos > 0),
    envases_disponibles integer not null check (envases_disponibles >= 0),
    envases_propuestos integer not null check (envases_propuestos >= 0),
    envases_faltantes integer not null check (envases_faltantes >= 0),
    decision text not null check (decision in ('inventario_disponible','derivar_produccion')),
    propuestas_lotes jsonb not null default '[]'::jsonb check (jsonb_typeof(propuestas_lotes)='array'),
    requiere_revision_humana boolean not null default false,
    es_provisional boolean not null default true check (es_provisional = true),
    es_demostrativo boolean not null default true,
    created_at timestamptz not null default now(),
    constraint evaluacion_suma_propuesta check (envases_propuestos + envases_faltantes = envases_requeridos)
);
create index if not exists idx_evaluaciones_cliente
    on public.evaluaciones_disponibilidad (usuario_id,solicitud_id,created_at desc);

alter table public.bodegas enable row level security;
alter table public.lotes_inventario enable row level security;
alter table public.evaluaciones_disponibilidad enable row level security;

-- El usuario cliente no puede consultar tablas internas ni alterar existencias.
revoke all on public.bodegas, public.lotes_inventario, public.evaluaciones_disponibilidad
    from anon, authenticated;
grant select on public.evaluaciones_disponibilidad to authenticated;
create policy "Cliente consulta solo su evaluación" on public.evaluaciones_disponibilidad
    for select to authenticated using (usuario_id = (select auth.uid()));

-- La función privilegiada vive fuera del esquema público expuesto.
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
grant usage on schema private to authenticated;

create or replace function private.evaluar_stock(p_calculo_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_usuario uuid := auth.uid();
    v_calculo public.calculos_materiales%rowtype;
    v_evaluacion public.evaluaciones_disponibilidad%rowtype;
    v_lote record;
    v_faltantes integer;
    v_disponibles integer;
    v_tomar integer;
    v_total integer := 0;
    v_propuestos jsonb := '[]'::jsonb;
    v_decision text;
begin
    if v_usuario is null then
        raise exception 'Debes iniciar sesión' using errcode='28000';
    end if;
    select * into v_calculo from public.calculos_materiales
    where id = p_calculo_id and usuario_id = v_usuario;
    if not found then
        raise exception 'El cálculo no existe o no pertenece al usuario' using errcode='42501';
    end if;

    v_faltantes := v_calculo.envases;
    -- Es una propuesta FEFO, NO una reserva: se revalidará al reservar (RF-06).
    for v_lote in
        select l.id, l.codigo_lote, l.ubicacion, l.existencia_envases,
               l.reservado_envases, l.fecha_vencimiento, l.es_demostrativo,
               b.nombre as bodega, b.ciudad
        from public.lotes_inventario l
        join public.bodegas b on b.id = l.bodega_id
        where l.producto_id = v_calculo.producto_id
          and l.estado = 'disponible' and b.activa = true
          and (l.fecha_vencimiento is null or l.fecha_vencimiento >= current_date)
        order by l.fecha_vencimiento asc nulls last, l.created_at asc, l.id asc
    loop
        v_disponibles := v_lote.existencia_envases - v_lote.reservado_envases;
        if v_disponibles <= 0 then
            continue;
        end if;
        v_total := v_total + v_disponibles;
        if v_faltantes > 0 then
            v_tomar := least(v_faltantes, v_disponibles);
            v_propuestos := v_propuestos || jsonb_build_array(jsonb_build_object(
                'lote_id', v_lote.id,
                'codigo_lote', v_lote.codigo_lote,
                'bodega', v_lote.bodega,
                'ciudad', v_lote.ciudad,
                'ubicacion', v_lote.ubicacion,
                'envases_disponibles', v_disponibles,
                'envases_propuestos', v_tomar,
                'fecha_vencimiento', v_lote.fecha_vencimiento,
                'es_demostrativo', v_lote.es_demostrativo
            ));
            v_faltantes := v_faltantes - v_tomar;
        end if;
    end loop;

    v_decision := case when v_faltantes = 0
        then 'inventario_disponible' else 'derivar_produccion' end;
    insert into public.evaluaciones_disponibilidad (
        calculo_id, solicitud_id, usuario_id, producto_id,
        envases_requeridos, envases_disponibles, envases_propuestos,
        envases_faltantes, decision, propuestas_lotes,
        requiere_revision_humana, es_provisional, es_demostrativo
    ) values (
        v_calculo.id, v_calculo.solicitud_id, v_usuario, v_calculo.producto_id,
        v_calculo.envases, v_total, v_calculo.envases - v_faltantes,
        v_faltantes, v_decision, v_propuestos,
        v_calculo.requiere_revision_humana, true, v_calculo.es_demostrativo
    ) returning * into v_evaluacion;
    return to_jsonb(v_evaluacion);
end;
$$;
revoke all on function private.evaluar_stock(uuid) from public, anon, authenticated;
grant execute on function private.evaluar_stock(uuid) to authenticated;

-- Exponer únicamente wrapper invoker, sin acceso a tablas internas.
create or replace function public.evaluar_disponibilidad_calculo(p_calculo_id uuid)
returns jsonb
language sql
security invoker
set search_path = ''
as $$
    select private.evaluar_stock(p_calculo_id);
$$;
revoke all on function public.evaluar_disponibilidad_calculo(uuid) from public, anon;
grant execute on function public.evaluar_disponibilidad_calculo(uuid) to authenticated;

-- Datos semilla explícitamente ficticios, sin precios ni stock Pintuco.
insert into public.bodegas(id,codigo,nombre,ciudad,activa,es_demostrativo)
values
 ('5dc1577e-1b37-4e4a-a285-dbf6ac1b5001','BD-DEMO-MDE','Bodega académica Medellín','Medellín',true,true),
 ('5dc1577e-1b37-4e4a-a285-dbf6ac1b5002','BD-DEMO-BEL','Bodega académica Bello','Bello',true,true)
on conflict (id) do nothing;

insert into public.lotes_inventario(
 id,producto_id,bodega_id,codigo_lote,ubicacion,
 existencia_envases,reservado_envases,estado,fecha_vencimiento,es_demostrativo
) values
 ('e7926c1b-3a49-42e0-9edc-2c9bc0aa0001',
  'd4b29936-e985-4b6d-af82-d675a06a1233',
  '5dc1577e-1b37-4e4a-a285-dbf6ac1b5001',
  'LOT-DEMO-MDE-01','A-01',4,1,'disponible','2028-09-30',true),
 ('e7926c1b-3a49-42e0-9edc-2c9bc0aa0002',
  'd4b29936-e985-4b6d-af82-d675a06a1233',
  '5dc1577e-1b37-4e4a-a285-dbf6ac1b5002',
  'LOT-DEMO-BEL-02','B-07',5,1,'disponible','2029-01-31',true)
on conflict (id) do nothing;
