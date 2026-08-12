-- Migración 2026-08-12: frecuencia respiratoria en el registro de signos vitales.
-- Alinea la base de datos con el Protocolo de medición domiciliaria v1.0.
-- Ejecutar una sola vez en Supabase (SQL Editor) o vía psql contra producción.
-- Es idempotente: puede correrse de nuevo sin efecto.

ALTER TABLE vital_signs
  ADD COLUMN IF NOT EXISTS respiratory_rate NUMERIC;

COMMENT ON COLUMN vital_signs.respiratory_rate IS
  'Respiraciones por minuto. Conteo guiado de 30 s multiplicado por 2 (Protocolo v1.0). Rango reportable: 6-50.';
