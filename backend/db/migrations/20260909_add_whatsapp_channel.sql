-- Migración 2026-09-09: WhatsApp como segundo canal de Carmen.
-- Ejecutar una sola vez en Supabase (SQL Editor) o vía psql. Es idempotente.
--
-- Aplicar ANTES del primer reporte real por WhatsApp: sin la columna, el vínculo
-- documento↔número queda solo en memoria (WARNING en logs) y sin el CHECK ampliado
-- el INSERT en vital_signs con source='whatsapp' falla (el canal responde con el
-- mensaje seguro de "no pude procesar tu reporte" y deja el error en logs).
-- No afecta a Telegram: no cambia ninguna columna ni valor que Telegram use.

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS whatsapp_phone TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS profiles_whatsapp_phone_key
  ON profiles (whatsapp_phone)
  WHERE whatsapp_phone IS NOT NULL;

COMMENT ON COLUMN profiles.whatsapp_phone IS
  'Número de WhatsApp del paciente (wa_id de Meta: E.164 sin +, p. ej. 573001234567). Vinculado por documento desde el chat.';

-- El CHECK inline de vital_signs.source se llama vital_signs_source_check (nombre automático de Postgres).
ALTER TABLE vital_signs DROP CONSTRAINT IF EXISTS vital_signs_source_check;
ALTER TABLE vital_signs
  ADD CONSTRAINT vital_signs_source_check
  CHECK (source IN ('telegram', 'web', 'manual', 'whatsapp'));
