-- RF-02: historial de clasificaciones IA. Sin modificar el estado del proceso.
create table if not exists public.analisis_ia (
    id uuid primary key default gen_random_uuid(),
    solicitud_id uuid not null references public.solicitudes(id) on delete restrict,
    usuario_id uuid not null references auth.users(id) on delete cascade,
    proveedor text not null default 'gemini' check (proveedor = 'gemini'),
    modelo text not null check (length(modelo) between 3 and 100),
    version_esquema smallint not null default 1 check (version_esquema=1),
    resultado jsonb not null check (jsonb_typeof(resultado)='object'),
    numero_imagenes smallint not null default 0 check (numero_imagenes between 0 and 2),
    envio_externo_consentido boolean not null check (envio_externo_consentido),
    created_at timestamptz not null default now()
);
create index if not exists idx_analisis_ia_usuario_solicitud
  on public.analisis_ia(usuario_id,solicitud_id,created_at desc);
alter table public.analisis_ia enable row level security;
revoke all on public.analisis_ia from anon,authenticated;
grant select on public.analisis_ia to authenticated;
grant insert (solicitud_id, usuario_id, modelo, resultado, numero_imagenes, envio_externo_consentido)
  on public.analisis_ia to authenticated;
create policy "Cliente lee sus clasificaciones" on public.analisis_ia
  for select to authenticated
  using (usuario_id=(select auth.uid()));
create policy "Cliente registra clasificaciones propias" on public.analisis_ia
  for insert to authenticated
  with check (
    usuario_id=(select auth.uid()) and envio_externo_consentido
    and exists (
      select 1 from public.solicitudes s
      where s.id=solicitud_id and s.usuario_id=(select auth.uid())
    )
  );
