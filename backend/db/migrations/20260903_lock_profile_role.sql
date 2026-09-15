-- Migración: impedir que un usuario se asigne o se cambie el rol.
-- Ejecutar una sola vez en Supabase (SQL Editor) o vía psql contra producción.
-- Es idempotente: puede correrse de nuevo sin efecto.
--
-- POR QUÉ ESTA MIGRACIÓN EXISTE
--
-- Las políticas anteriores sobre `profiles` solo comprobaban la propiedad de
-- la fila:
--
--     profiles_insert_own  WITH CHECK (id = auth.uid())
--     profiles_update_own  USING (id = auth.uid()) WITH CHECK (id = auth.uid())
--
-- Combinadas con el GRANT de UPDATE sobre todas las columnas (schemas.sql:212),
-- permitían que cualquier usuario autenticado ejecutara desde el navegador:
--
--     supabase.from('profiles').update({ role: 'admin' }).eq('id', <su id>)
--
-- La fila es suya, así que RLS lo aceptaba. Un paciente podía convertirse en
-- administrador y leer los perfiles de todos. Quitar «Admin» del formulario de
-- registro no cerraba nada: el camino no pasaba por el formulario.

-- Lee el rol saltándose RLS. Sin SECURITY DEFINER, una política sobre
-- `profiles` que consulte `profiles` provoca recursión infinita.
CREATE OR REPLACE FUNCTION public.current_profile_role()
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role FROM public.profiles WHERE id = auth.uid();
$$;

REVOKE ALL ON FUNCTION public.current_profile_role() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.current_profile_role() TO authenticated;

DO $$
BEGIN
  -- ---------------------------------------------------------------------
  -- INSERT: puedes crear tu propia fila, pero nunca como administrador.
  -- El registro público sigue pudiendo crear 'patient' e 'ips'.
  -- ---------------------------------------------------------------------
  DROP POLICY IF EXISTS profiles_insert_own ON profiles;
  CREATE POLICY profiles_insert_own
    ON profiles FOR INSERT TO authenticated
    WITH CHECK (id = auth.uid() AND role <> 'admin');

  -- ---------------------------------------------------------------------
  -- UPDATE: puedes editar tu perfil, pero no tocar tu rol.
  -- `role = current_profile_role()` exige que el valor entrante sea el que
  -- ya tenías: cualquier cambio de rol propio queda rechazado, incluso de
  -- 'patient' a 'ips'.
  -- ---------------------------------------------------------------------
  DROP POLICY IF EXISTS profiles_update_own ON profiles;
  CREATE POLICY profiles_update_own
    ON profiles FOR UPDATE TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid() AND role = public.current_profile_role());

  -- ---------------------------------------------------------------------
  -- Los administradores sí gestionan perfiles ajenos, incluido el rol.
  -- Sin estas dos políticas, un admin no podría ver ni editar a nadie.
  -- ---------------------------------------------------------------------
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'profiles' AND policyname = 'profiles_select_admin'
  ) THEN
    CREATE POLICY profiles_select_admin
      ON profiles FOR SELECT TO authenticated
      USING (public.current_profile_role() = 'admin');
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'profiles' AND policyname = 'profiles_update_admin'
  ) THEN
    CREATE POLICY profiles_update_admin
      ON profiles FOR UPDATE TO authenticated
      USING (public.current_profile_role() = 'admin')
      WITH CHECK (public.current_profile_role() = 'admin');
  END IF;

  -- ---------------------------------------------------------------------
  -- Lectura agregada para el panel de administración.
  --
  -- Las políticas de schemas.sql:303 y :312 son de propiedad de fila:
  --
  --     clinical_reports_select_own  USING (patient_id = auth.uid())
  --     alerts_select_own            USING (patient_id = auth.uid()
  --                                         OR acknowledged_by = auth.uid())
  --
  -- Un administrador no es paciente de nadie, así que ambas le devuelven
  -- cero filas. Las métricas «Reportes hoy», «Alertas hoy» y «Críticas»
  -- salían en 0 aunque la base estuviera llena. Estas dos políticas son de
  -- solo lectura: no permiten al admin escribir ni reconocer alertas.
  --
  -- `rag_documents` no necesita nada: su política ya es USING (TRUE) para
  -- cualquier autenticado (schemas.sql:331).
  -- ---------------------------------------------------------------------
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'alerts' AND policyname = 'alerts_select_admin'
  ) THEN
    CREATE POLICY alerts_select_admin
      ON alerts FOR SELECT TO authenticated
      USING (public.current_profile_role() = 'admin');
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'clinical_reports' AND policyname = 'clinical_reports_select_admin'
  ) THEN
    CREATE POLICY clinical_reports_select_admin
      ON clinical_reports FOR SELECT TO authenticated
      USING (public.current_profile_role() = 'admin');
  END IF;
END
$$;

COMMENT ON FUNCTION public.current_profile_role() IS
  'Rol del usuario actual, leído saltándose RLS. Existe para que las políticas de profiles puedan consultar profiles sin recursión infinita.';

-- ---------------------------------------------------------------------------
-- DESPUÉS DE APLICARLA, COMPROBAR QUE YA NO HAY ADMINISTRADORES DE MÁS.
-- Esta migración cierra la puerta, pero no deshace lo que haya entrado por
-- ella. Revisa quién es admin hoy y degrada a quien no deba serlo:
--
--     SELECT id, full_name, role FROM profiles WHERE role = 'admin';
--
-- Hazlo con la clave de servicio (service_role). Las políticas permisivas se
-- combinan con OR, así que `profiles_update_admin` deja que un admin cambie
-- cualquier fila, incluida la suya: degradarse a uno mismo SÍ es posible desde
-- el panel, y quien lo haga pierde el acceso para deshacerlo. La pantalla de
-- usuarios rechaza ese caso por su cuenta
-- (frontend/app/(admin)/admin/users/actions.ts), pero es una barrera de
-- interfaz, no de base de datos.
-- ---------------------------------------------------------------------------
