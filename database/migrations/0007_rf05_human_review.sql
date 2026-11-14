-- RF-05: historial de revisión humana y resolución autorizada por asesor técnico.
-- Cambios de estado auditables; no reservas ni cambios de inventario.
alter table public.solicitudes drop constraint if exists solicitudes_estado_check;
alter table public.solicitudes add constraint solicitudes_estado_check check (
  estado in ('radicada','en_validacion','pendiente_informacion','en_analisis',
  'en_revision_tecnica','cotizada','aprobada','rechazada','en_logistica',
  'en_aplicacion','en_calidad','finalizada','cancelada')
);

create table if not exists public.revisiones_tecnicas (
  id uuid primary key default gen_random_uuid(),
  solicitud_id uuid not null references public.solicitudes(id) on delete restrict,
  cliente_id uuid not null references auth.users(id) on delete cascade,
  especialista_id uuid not null references auth.users(id) on delete restrict,
  decision text not null check (
    decision in ('aprobar','rechazar','solicitar_informacion','solicitar_correccion')
  ),
  observaciones text not null check (char_length(btrim(observaciones)) between 10 and 2000),
  correccion_propuesta jsonb not null default '{}'::jsonb
    check (jsonb_typeof(correccion_propuesta)='object'),
  estado_anterior text not null,
  estado_nuevo text not null,
  analisis_id uuid references public.analisis_ia(id) on delete set null,
  calculo_id uuid references public.calculos_materiales(id) on delete set null,
  evaluacion_id uuid references public.evaluaciones_disponibilidad(id) on delete set null,
  created_at timestamptz not null default now()
);
create index if not exists idx_revisiones_solicitud on public.revisiones_tecnicas(solicitud_id,created_at desc);
alter table public.revisiones_tecnicas enable row level security;
revoke all on public.revisiones_tecnicas from public, anon, authenticated;
-- Intencional: sin políticas Data API; el acceso se canaliza por RPCs verificadas.
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
grant usage on schema private to authenticated;

create or replace function private.rf05_es_asesor()
returns boolean
language sql stable security definer set search_path=''
as $$
 select exists (
  select 1 from public.profiles p
  where p.id = (select auth.uid())
  and p.role in ('asesor','especialista_tecnico','administrador')
 );
$$;
revoke all on function private.rf05_es_asesor() from public, anon;
grant execute on function private.rf05_es_asesor() to authenticated;

create or replace function private.rf05_bandeja()
returns jsonb
language plpgsql stable security definer set search_path=''
as $$
declare
 v_result jsonb;
begin
 if auth.uid() is null or not private.rf05_es_asesor() then
  raise exception 'No tiene permisos de asesor' using errcode='42501';
 end if;
 select coalesce(jsonb_agg(to_jsonb(item) order by item.fecha_registro desc),'[]'::jsonb)
 into v_result
 from (
  select s.id as solicitud_id, s.estado, s.created_at as fecha_registro,
         s.descripcion_libre, p.nombre_proyecto, p.area_m2,
         p.tipo_superficie, p.condicion, p.ambiente,
         c.nombre_empresa, c.ciudad,
         exists(select 1 from public.analisis_ia a where a.solicitud_id=s.id) as tiene_analisis_ia,
         exists(select 1 from public.calculos_materiales k where k.solicitud_id=s.id) as tiene_calculo,
         exists(select 1 from public.calculos_materiales k where k.solicitud_id=s.id and k.requiere_revision_humana) as requiere_revision
  from public.solicitudes s
  join public.proyectos p on p.id=s.proyecto_id
  join public.clientes c on c.id=p.cliente_id
  where s.estado in ('radicada','en_validacion','en_analisis',
                     'en_revision_tecnica','pendiente_informacion')
  order by s.created_at desc, s.id desc limit 100
 ) item;
 return v_result;
end;
$$;
revoke all on function private.rf05_bandeja() from public, anon;
grant execute on function private.rf05_bandeja() to authenticated;

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
  'revisiones',coalesce((
     select jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id desc)
     from public.revisiones_tecnicas t where t.solicitud_id=v_s.id
  ),'[]'::jsonb)
 ) into v_result;
 return v_result;
end;
$$;
revoke all on function private.rf05_detalle(uuid) from public, anon;
grant execute on function private.rf05_detalle(uuid) to authenticated;

create or replace function private.rf05_resolver(
 p_solicitud_id uuid, p_decision text, p_observaciones text,
 p_correccion_propuesta jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql volatile security definer set search_path=''
as $$
declare
 v_s public.solicitudes%rowtype;
 v_estado text;
 v_analisis uuid;
 v_calculo uuid;
 v_evaluacion uuid;
 v_revision public.revisiones_tecnicas%rowtype;
 v_campo text;
 v_valor text;
begin
 if auth.uid() is null or not private.rf05_es_asesor() then
  raise exception 'Solo el especialista puede resolver la solicitud' using errcode='42501';
 end if;
 if p_decision not in ('aprobar','rechazar','solicitar_informacion','solicitar_correccion') then
  raise exception 'Decisión no permitida' using errcode='22023';
 end if;
 if p_observaciones is null or char_length(btrim(p_observaciones)) not between 10 and 2000 then
  raise exception 'Las observaciones deben tener entre 10 y 2000 caracteres' using errcode='22023';
 end if;
 if p_correccion_propuesta is null or jsonb_typeof(p_correccion_propuesta) <> 'object' then
  raise exception 'Formato de corrección inválido' using errcode='22023';
 end if;
 if p_decision='solicitar_correccion' then
  if (select count(*) from jsonb_object_keys(p_correccion_propuesta)) <> 2
    or not (p_correccion_propuesta ? 'campo' and p_correccion_propuesta ? 'valor_propuesto') then
   raise exception 'Indique el campo y valor propuesto de corrección' using errcode='22023';
  end if;
  v_campo := p_correccion_propuesta->>'campo';
  v_valor := p_correccion_propuesta->>'valor_propuesto';
  if v_campo not in ('area_m2','tipo_superficie','condicion','ambiente','color_requerido')
     or v_valor is null or char_length(btrim(v_valor)) not between 2 and 180 then
   raise exception 'Corrección técnica inválida' using errcode='22023';
  end if;
  if v_campo='area_m2' and (v_valor !~ '^[0-9]+([.][0-9]+)?$' or v_valor::numeric <= 0) then
   raise exception 'El área propuesta debe ser positiva' using errcode='22023';
  end if;
  if v_campo='ambiente' and v_valor not in ('interior','exterior') then
   raise exception 'Ambiente inválido' using errcode='22023';
  end if;
 elsif p_correccion_propuesta <> '{}'::jsonb then
  raise exception 'Las correcciones solo se admiten al solicitarlas' using errcode='22023';
 end if;

 -- Evita decisiones simultáneas inconsistentes.
 select * into v_s from public.solicitudes
 where id=p_solicitud_id for update;
 if not found then raise exception 'Solicitud no encontrada' using errcode='42501'; end if;
 if v_s.estado not in ('radicada','en_validacion','en_analisis','en_revision_tecnica','pendiente_informacion') then
  raise exception 'La solicitud ya tiene una decisión final o no está revisable' using errcode='23514';
 end if;

 select a.id into v_analisis from public.analisis_ia a
 where a.solicitud_id=v_s.id order by a.created_at desc,a.id desc limit 1;
 select k.id into v_calculo from public.calculos_materiales k
 where k.solicitud_id=v_s.id order by k.created_at desc,k.id desc limit 1;
 select e.id into v_evaluacion from public.evaluaciones_disponibilidad e
 where e.solicitud_id=v_s.id order by e.created_at desc,e.id desc limit 1;

 if p_decision='aprobar' and (v_analisis is null or v_calculo is null) then
  raise exception 'Para aprobar se requiere análisis de IA y cálculo técnico' using errcode='23514';
 end if;
 v_estado := case p_decision
  when 'aprobar' then 'aprobada'
  when 'rechazar' then 'rechazada'
  else 'pendiente_informacion'
 end;
 insert into public.revisiones_tecnicas (
   solicitud_id,cliente_id,especialista_id,decision,observaciones,
   correccion_propuesta,estado_anterior,estado_nuevo,analisis_id,calculo_id,evaluacion_id
 ) values (
   v_s.id,v_s.usuario_id,auth.uid(),p_decision,btrim(p_observaciones),
   p_correccion_propuesta,v_s.estado,v_estado,v_analisis,v_calculo,v_evaluacion
 ) returning * into v_revision;
 update public.solicitudes set estado=v_estado,updated_at=now() where id=v_s.id;
 return to_jsonb(v_revision);
end;
$$;
revoke all on function private.rf05_resolver(uuid,text,text,jsonb) from public, anon;
grant execute on function private.rf05_resolver(uuid,text,text,jsonb) to authenticated;

-- Wrappers SECURITY INVOKER en el esquema expuesto; las funciones privilegiadas son privadas.
create or replace function public.bandeja_revision_tecnica()
returns jsonb language sql stable security invoker set search_path=''
as $$select private.rf05_bandeja();$$;
revoke all on function public.bandeja_revision_tecnica() from public, anon;
grant execute on function public.bandeja_revision_tecnica() to authenticated;

create or replace function public.detalle_revision_tecnica(p_solicitud_id uuid)
returns jsonb language sql stable security invoker set search_path=''
as $$select private.rf05_detalle(p_solicitud_id);$$;
revoke all on function public.detalle_revision_tecnica(uuid) from public, anon;
grant execute on function public.detalle_revision_tecnica(uuid) to authenticated;

create or replace function public.resolver_revision_tecnica(
 p_solicitud_id uuid,p_decision text,p_observaciones text,
 p_correccion_propuesta jsonb default '{}'::jsonb
)
returns jsonb language sql volatile security invoker set search_path=''
as $$select private.rf05_resolver(p_solicitud_id,p_decision,p_observaciones,p_correccion_propuesta);$$;
revoke all on function public.resolver_revision_tecnica(uuid,text,text,jsonb) from public, anon;
grant execute on function public.resolver_revision_tecnica(uuid,text,text,jsonb) to authenticated;
