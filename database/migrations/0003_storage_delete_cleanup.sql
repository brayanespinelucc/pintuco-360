create policy "Evidencias: eliminar solo propias" on storage.objects
 for delete to authenticated using (
 bucket_id='colorlink-evidencias'
 and (storage.foldername(name))[1]=(select auth.uid())::text
 and exists(select 1 from public.solicitudes s
 where s.id::text=(storage.foldername(name))[2]
 and s.usuario_id=(select auth.uid()))
 );
