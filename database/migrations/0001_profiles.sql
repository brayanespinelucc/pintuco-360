-- Ejecutar una vez en Supabase SQL Editor.
-- El rol se establece en el servidor; nunca debe poder ser promovido por un cliente.
create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    full_name text,
    role text not null default 'cliente'
      check (role in (
        'administrador', 'cliente', 'asesor', 'especialista_tecnico',
        'inventario', 'produccion', 'logistica', 'aplicador', 'calidad', 'gerencia'
      )),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;

drop policy if exists "Usuarios consultan solo su perfil" on public.profiles;
create policy "Usuarios consultan solo su perfil"
    on public.profiles for select to authenticated
    using ((select auth.uid()) = id);

create or replace function public.create_profile_for_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (id, full_name, role)
    values (new.id, new.raw_user_meta_data ->> 'full_name', 'cliente')
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created_pintuco on auth.users;
create trigger on_auth_user_created_pintuco
after insert on auth.users for each row
execute function public.create_profile_for_new_user();

-- Si ya existen usuarios de Auth antes de aplicar esta migración:
insert into public.profiles (id, full_name, role)
select id, raw_user_meta_data ->> 'full_name', 'cliente'
from auth.users
on conflict (id) do nothing;

-- Para asignar un rol administrativo, usar exclusivamente SQL Editor con permisos
-- de administrador y un UUID de usuario verificado. Ejemplo:
-- update public.profiles set role = 'administrador' where id = 'UUID_REAL';
