-- Migración 2026-09-02: contexto demográfico colombiano en el perfil.
-- Habilita el reporte por EPS, grupo étnico DANE y clasificación de
-- insuficiencia cardiaca, ausentes hasta ahora en `profiles`.
-- Ejecutar una sola vez en Supabase (SQL Editor) o vía psql contra producción.
-- Es idempotente: puede correrse de nuevo sin efecto.

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS eps TEXT,
  ADD COLUMN IF NOT EXISTS ethnic_group TEXT,
  ADD COLUMN IF NOT EXISTS heart_failure_class TEXT,
  ADD COLUMN IF NOT EXISTS birth_date DATE,
  ADD COLUMN IF NOT EXISTS biological_sex TEXT,
  ADD COLUMN IF NOT EXISTS department TEXT,
  ADD COLUMN IF NOT EXISTS city TEXT;

-- Restricciones añadidas por separado: ALTER TABLE ... ADD CONSTRAINT no
-- admite IF NOT EXISTS, así que se comprueba el catálogo primero para que la
-- migración siga siendo idempotente.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'profiles_ethnic_group_check'
  ) THEN
    ALTER TABLE profiles ADD CONSTRAINT profiles_ethnic_group_check
      CHECK (ethnic_group IS NULL OR ethnic_group IN (
        'indigena', 'afrocolombiano', 'raizal', 'palenquero', 'gitano', 'ninguno'
      ));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'profiles_heart_failure_class_check'
  ) THEN
    ALTER TABLE profiles ADD CONSTRAINT profiles_heart_failure_class_check
      CHECK (heart_failure_class IS NULL OR heart_failure_class IN ('A', 'B', 'C', 'D'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'profiles_biological_sex_check'
  ) THEN
    ALTER TABLE profiles ADD CONSTRAINT profiles_biological_sex_check
      CHECK (biological_sex IS NULL OR biological_sex IN ('female', 'male', 'intersex'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'profiles_birth_date_check'
  ) THEN
    ALTER TABLE profiles ADD CONSTRAINT profiles_birth_date_check
      CHECK (birth_date IS NULL OR birth_date <= CURRENT_DATE);
  END IF;
END
$$;

COMMENT ON COLUMN profiles.eps IS
  'Entidad Promotora de Salud a la que está afiliado el paciente. Texto libre: no existe un catálogo estable de EPS con el que validar.';

COMMENT ON COLUMN profiles.ethnic_group IS
  'Autorreconocimiento étnico según las categorías DANE. Es un dato autodeclarado por la persona, no una observación clínica.';

COMMENT ON COLUMN profiles.heart_failure_class IS
  'Estadio de insuficiencia cardiaca ACC/AHA. A: riesgo · B: pre-IC · C: sintomática · D: avanzada. Lo asigna el equipo clínico, no el paciente.';

COMMENT ON COLUMN profiles.birth_date IS
  'Fecha de nacimiento. Preferida sobre una edad almacenada: la edad se calcula al consultar y no queda desactualizada. Ver la nota sobre patient_clinical_info.age más abajo.';

COMMENT ON COLUMN profiles.biological_sex IS
  'Sexo biológico, usado como variable clínica. Distinto de la identidad de género, que este esquema no registra.';

COMMENT ON COLUMN profiles.department IS
  'Departamento de residencia del paciente. Homónimo de ips.department, que describe la sede de la IPS, no al paciente.';

COMMENT ON COLUMN profiles.city IS
  'Municipio de residencia del paciente. Homónimo de ips.city, que describe la sede de la IPS, no al paciente.';

-- ---------------------------------------------------------------------------
-- SOLAPAMIENTO PENDIENTE DE DECIDIR — leer antes de aplicar.
--
-- `patient_clinical_info` ya guarda dos datos equivalentes a los que esta
-- migración añade:
--
--   patient_clinical_info.age    INTEGER              <-> profiles.birth_date
--   patient_clinical_info.gender TEXT (male/female/other) <-> profiles.biological_sex
--
-- Aplicar esto tal cual deja dos fuentes para el mismo hecho, que pueden
-- divergir en silencio. `age` además envejece mal: es correcta el día que se
-- escribe y falsa a partir del siguiente cumpleaños.
--
-- Recomendación: tras aplicar, poblar birth_date, deprecar
-- patient_clinical_info.age y calcular la edad al vuelo. Nada de eso se hace
-- aquí — esta migración solo añade columnas.
-- ---------------------------------------------------------------------------
