-- RF-03: catálogo técnico auditable + resultados reproducibles de cálculos.
-- Valores demostrativos explícitos: no son fichas oficiales de Pintuco.
create table if not exists public.catalogo_productos_tecnicos (
    id uuid primary key default gen_random_uuid(),
    nombre text not null check (length(btrim(nombre)) between 5 and 200),
    fabricante text not null check (length(btrim(fabricante)) between 2 and 100),
    descripcion text,
    superficie text not null check (superficie in ('concreto', 'mamposteria', 'metal', 'madera', 'cualquiera')),
    ambiente text not null check (ambiente in ('interior', 'exterior', 'ambos')),
    rendimiento_m2_litro_mano numeric(12,3) not null check (rendimiento_m2_litro_mano > 0),
    manos_recomendadas smallint not null check (manos_recomendadas between 1 and 6),
    desperdicio_pct numeric(5,2) not null check (desperdicio_pct between 0 and 50),
    presentacion_litros numeric(12,3) not null check (presentacion_litros > 0),
    ficha_tecnica_url text,
    es_demostrativo boolean not null default true,
    activo boolean not null default true,
    created_at timestamptz not null default now()
);
alter table public.catalogo_productos_tecnicos enable row level security;
revoke all on public.catalogo_productos_tecnicos from anon, authenticated;
grant select on public.catalogo_productos_tecnicos to authenticated;
create policy "Catálogo: consultar productos activos"
    on public.catalogo_productos_tecnicos for select to authenticated using (activo);

create table if not exists public.calculos_materiales (
    id uuid primary key default gen_random_uuid(),
    solicitud_id uuid not null references public.solicitudes(id) on delete restrict,
    usuario_id uuid not null references auth.users(id) on delete cascade,
    producto_id uuid not null references public.catalogo_productos_tecnicos(id) on delete restrict,
    area_m2 numeric(12,2) not null check (area_m2 > 0),
    manos smallint not null check (manos between 1 and 6),
    rendimiento_m2_litro_mano numeric(12,3) not null check (rendimiento_m2_litro_mano > 0),
    desperdicio_pct numeric(5,2) not null check (desperdicio_pct between 0 and 50),
    presentacion_litros numeric(12,3) not null check (presentacion_litros > 0),
    litros_teoricos numeric(16,3) not null check (litros_teoricos > 0),
    litros_con_desperdicio numeric(16,3) not null check (litros_con_desperdicio > 0),
    envases integer not null check (envases > 0),
    litros_comerciales numeric(16,3) not null check (litros_comerciales > 0),
    requiere_revision_humana boolean not null default false,
    motivos_revision text[] not null default '{}',
    es_demostrativo boolean not null default true,
    created_at timestamptz not null default now()
);
create index if not exists idx_calculos_materiales_solicitud
    on public.calculos_materiales (usuario_id, solicitud_id, created_at desc);
alter table public.calculos_materiales enable row level security;
revoke all on public.calculos_materiales from anon, authenticated;
grant select on public.calculos_materiales to authenticated;
grant insert (
    solicitud_id, usuario_id, producto_id, area_m2, manos,
    rendimiento_m2_litro_mano, desperdicio_pct, presentacion_litros,
    litros_teoricos, litros_con_desperdicio, envases, litros_comerciales,
    requiere_revision_humana, motivos_revision, es_demostrativo
) on public.calculos_materiales to authenticated;
create policy "Cálculos: consultar propios"
    on public.calculos_materiales for select to authenticated
    using (usuario_id = (select auth.uid()));
create policy "Cálculos: registrar sobre solicitud propia"
    on public.calculos_materiales for insert to authenticated
    with check (
        usuario_id = (select auth.uid())
        and exists (
            select 1 from public.solicitudes s
            where s.id = solicitud_id and s.usuario_id = (select auth.uid())
        )
    );

-- Semilla académica reproducible: NO es producto oficial ni rendimiento validado.
insert into public.catalogo_productos_tecnicos (
    id, nombre, fabricante, descripcion, superficie, ambiente,
    rendimiento_m2_litro_mano, manos_recomendadas, desperdicio_pct,
    presentacion_litros, es_demostrativo, activo
) values (
    'd4b29936-e985-4b6d-af82-d675a06a1233',
    'Recubrimiento DEMOSTRATIVO para concreto exterior (4 L)',
    'Datos académicos (NO Pintuco)',
    'Valores ficticios para probar el algoritmo: 10 m²/L por mano, 2 manos, 15% desperdicio y envase de 4 L. NO representa ficha técnica comercial.',
    'concreto', 'exterior', 10.000, 2, 15.00, 4.000, true, true
) on conflict (id) do nothing;
