-- Migración 2026-09-08: idioma en que Carmen habla a cada paciente (es | en).
-- Solo cambia la voz de Carmen hacia el paciente; reportes clínicos, alertas a médicos,
-- correos y dashboard siguen en español.
-- Ejecutar una sola vez en Supabase (SQL Editor) o vía psql contra producción.
-- Es idempotente: puede correrse de nuevo sin efecto.
-- Mientras no se aplique, el bot conserva el idioma en memoria (se pierde al reiniciar
-- el servicio) y deja un WARNING en logs cada vez que intenta guardarlo.

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS language TEXT NOT NULL DEFAULT 'es'
  CHECK (language IN ('es', 'en'));

COMMENT ON COLUMN profiles.language IS
  'Idioma de la voz de Carmen hacia el paciente (es|en). Origen: language_code de Telegram, confirmado en el saludo o cambiado con /idioma.';
