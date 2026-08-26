-- HomecareCCV · Reset total + seed de médicos para la demo AIiH 2026
-- ================================================================
-- CÓMO USARLO (Supabase → SQL Editor):
--
--   PASO 1. Ejecuta la PARTE 1 (borra TODOS los datos de pacientes,
--           reportes, alertas y usuarios; conserva las guías RAG).
--
--   PASO 2. En Supabase → Authentication → Users → "Add user", crea
--           los 3 médicos con email + contraseña y "Auto Confirm User":
--             - Pablo Benjumea      → EMAIL_PABLO
--             - Juan Camilo Arias   → EMAIL_JUAN_CAMILO
--             - Carlos Orrego       → cmorregofranco@gmail.com
--
--   PASO 3. Reemplaza abajo EMAIL_PABLO y EMAIL_JUAN_CAMILO por los
--           emails reales y ejecuta la PARTE 2.
--
--   PASO 4. Cada médico abre t.me/project918_homecare_bot, envía
--           /start y luego su documento (cc123456 / cc1234567 /
--           cc12345678). Eso captura su telegram_chat_id y desde ahí
--           reciben alertas y avisos de nuevos pacientes.
--
-- Los pacientes NO se siembran: se registran solos desde el bot.

-- ============================ PARTE 1 ============================
TRUNCATE TABLE
  alerts,
  clinical_reports,
  risk_predictions,
  vital_signs,
  patient_clinical_info,
  profiles
CASCADE;

DELETE FROM auth.users;

-- ============================ PARTE 2 ============================
-- La tabla profiles no tiene columna email y las alertas por correo
-- (Resend) la leen de ahí: se agrega y se llena desde auth.users.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email TEXT;

INSERT INTO profiles (id, role, full_name, document_id, email)
SELECT id, 'ips', 'Pablo Benjumea', 'cc123456', email
FROM auth.users WHERE email = 'EMAIL_PABLO';

INSERT INTO profiles (id, role, full_name, document_id, email)
SELECT id, 'ips', 'Juan Camilo Arias', 'cc1234567', email
FROM auth.users WHERE email = 'EMAIL_JUAN_CAMILO';

INSERT INTO profiles (id, role, full_name, document_id, email)
SELECT id, 'ips', 'Carlos Orrego', 'cc12345678', email
FROM auth.users WHERE email = 'cmorregofranco@gmail.com';

-- Verificación: deben aparecer los 3 con role='ips'
SELECT full_name, document_id, role, telegram_chat_id, id
FROM profiles ORDER BY created_at;
