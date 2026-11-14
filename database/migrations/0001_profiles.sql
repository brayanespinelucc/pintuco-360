-- Migration 0001: perfiles y roles de Pintuco 360.
-- Crear una tabla segura de perfiles vinculada a Supabase Auth.
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
revoke all on table public.profiles from anon, authenticated;
grant select on table public.profiles to authenticated;

drop policy if exists "Usuarios consultan solo su perfil" on public.profiles;
create policy "Usuarios consultan solo su perfil"
    on public.profiles for select to authenticated
    using ((select auth.uid()) = id);

-- Evita que una función SECURITY DEFINER quede en el esquema público expuesto por la API.
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create or replace function private.create_profile_for_new_user()
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

revoke all on function private.create_profile_for_new_user() from public, anon, authenticated;

drop trigger if exists on_auth_user_created_pintuco on auth.users;
create trigger on_auth_user_created_pintuco
after insert on auth.users for each row
execute function private.create_profile_for_new_user();

-- Para usuarios creados antes de esta migración:
insert into public.profiles (id, full_name, role)
select id, raw_user_meta_data ->> 'full_name', 'cliente'
from auth.users
on conflict (id) do nothing;

-- Asignación de roles privilegiados: solo por SQL Editor con administrador.
-- update public.profiles set role = 'administrador' where id = 'UUID_REAL';
