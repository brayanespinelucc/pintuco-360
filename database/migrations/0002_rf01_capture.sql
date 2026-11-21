-- RF-01: clientes, proyectos, solicitudes y fotografías (aplicada a Supabase).
create table if not exists public.clientes (
 id uuid primary key default gen_random_uuid(),
 usuario_id uuid not null unique references auth.users(id) on delete cascade,
 nombre_empresa text not null check (char_length(btrim(nombre_empresa)) between 2 and 160),
 ciudad text not null check (char_length(btrim(ciudad)) between 2 and 100),
 created_at timestamptz not null default now()
);
create table if not exists public.proyectos (
 id uuid primary key default gen_random_uuid(),
 cliente_id uuid not null references public.clientes(id) on delete restrict,
 usuario_id uuid not null references auth.users(id) on delete cascade,
 nombre_proyecto text not null check (char_length(btrim(nombre_proyecto)) between 3 and 180),
 area_m2 numeric(12,2) not null check (area_m2 > 0),
 tipo_superficie text not null check (char_length(btrim(tipo_superficie)) between 2 and 100),
 condicion text not null check (char_length(btrim(condicion)) between 2 and 300),
 ambiente text not null check (ambiente in ('interior','exterior')),
 color_requerido text not null check (char_length(btrim(color_requerido)) between 2 and 100),
 fecha_requerida date,
 created_at timestamptz not null default now()
);
create index if not exists idx_proyectos_usuario_created on public.proyectos(usuario_id,created_at desc);
create table if not exists public.solicitudes (
 id uuid primary key default gen_random_uuid(),
 proyecto_id uuid not null references public.proyectos(id) on delete restrict,
 usuario_id uuid not null references auth.users(id) on delete cascade,
 descripcion_libre text not null check (char_length(btrim(descripcion_libre)) between 10 and 4000),
 estado text not null default 'radicada' check (estado in (
 'radicada','en_validacion','pendiente_informacion','en_analisis','en_revision_tecnica','cotizada',
 'aprobada','en_logistica','en_aplicacion','en_calidad','finalizada','cancelada')),
 paso_actual smallint not null default 1 check (paso_actual between 1 and 15),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists idx_solicitudes_usuario_created on public.solicitudes(usuario_id,created_at desc);
create table if not exists public.solicitud_evidencias (
 id uuid primary key default gen_random_uuid(),
 solicitud_id uuid not null references public.solicitudes(id) on delete cascade,
 usuario_id uuid not null references auth.users(id) on delete cascade,
 storage_path text not null unique,
 archivo_original text not null check (char_length(archivo_original) between 1 and 255),
 mime_type text not null check (mime_type in ('image/jpeg','image/png')),
 bytes integer not null check (bytes > 0 and bytes <= 5242880),
 created_at timestamptz not null default now()
);
create index if not exists idx_evidencias_solicitud on public.solicitud_evidencias(solicitud_id,created_at desc);
alter table public.clientes enable row level security;
alter table public.proyectos enable row level security;
alter table public.solicitudes enable row level security;
alter table public.solicitud_evidencias enable row level security;
revoke all on public.clientes,public.proyectos,public.solicitudes,public.solicitud_evidencias from anon,authenticated;
grant select on public.clientes,public.proyectos,public.solicitudes,public.solicitud_evidencias to authenticated;
grant insert(usuario_id,nombre_empresa,ciudad) on public.clientes to authenticated;
grant insert(cliente_id,usuario_id,nombre_proyecto,area_m2,tipo_superficie,condicion,ambiente,color_requerido,fecha_requerida) on public.proyectos to authenticated;
grant insert(proyecto_id,usuario_id,descripcion_libre) on public.solicitudes to authenticated;
grant insert(solicitud_id,usuario_id,storage_path,archivo_original,mime_type,bytes) on public.solicitud_evidencias to authenticated;
create policy "Cliente lee su empresa" on public.clientes for select to authenticated using (usuario_id=(select auth.uid()));
create policy "Cliente crea su empresa" on public.clientes for insert to authenticated with check (usuario_id=(select auth.uid()));
create policy "Cliente lee sus proyectos" on public.proyectos for select to authenticated using (usuario_id=(select auth.uid()));
create policy "Cliente crea proyectos propios" on public.proyectos for insert to authenticated with check (
 usuario_id=(select auth.uid()) and exists(select 1 from public.clientes c where c.id=cliente_id and c.usuario_id=(select auth.uid()))
);
create policy "Cliente lee sus solicitudes" on public.solicitudes for select to authenticated using (usuario_id=(select auth.uid()));
create policy "Cliente radica sus solicitudes" on public.solicitudes for insert to authenticated with check (
 usuario_id=(select auth.uid()) and exists(select 1 from public.proyectos p where p.id=proyecto_id and p.usuario_id=(select auth.uid()))
);
create policy "Cliente lee sus evidencias" on public.solicitud_evidencias for select to authenticated using (usuario_id=(select auth.uid()));
create policy "Cliente registra sus evidencias" on public.solicitud_evidencias for insert to authenticated with check (
 usuario_id=(select auth.uid()) and storage_path like usuario_id::text || '/' || solicitud_id::text || '/%'
 and exists(select 1 from public.solicitudes s where s.id=solicitud_id and s.usuario_id=(select auth.uid()))
);
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('colorlink-evidencias','colorlink-evidencias',false,5242880,ARRAY['image/jpeg','image/png'])
on conflict (id) do nothing;
create policy "Evidencias: subir solo a solicitud propia" on storage.objects
 for insert to authenticated with check (
 bucket_id='colorlink-evidencias'
 and (storage.foldername(name))[1]=(select auth.uid())::text
 and exists(select 1 from public.solicitudes s where s.id::text=(storage.foldername(name))[2] and s.usuario_id=(select auth.uid()))
);
create policy "Evidencias: leer solo propias" on storage.objects
 for select to authenticated using (
 bucket_id='colorlink-evidencias'
 and (storage.foldername(name))[1]=(select auth.uid())::text
 and exists(select 1 from public.solicitudes s where s.id::text=(storage.foldername(name))[2] and s.usuario_id=(select auth.uid()))
);
