-- HomecareCCV Supabase schema
-- Execute this file in the Supabase SQL editor or through the local pgvector container.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Supabase Cloud already owns auth.users and auth.uid(); do not create them
-- there. The guarded block below only creates minimal local stubs when this
-- schema runs against the plain pgvector PostgreSQL image from docker-compose.
DO $$
BEGIN
  CREATE SCHEMA IF NOT EXISTS auth;

  IF to_regclass('auth.users') IS NULL THEN
    CREATE TABLE auth.users (
      id UUID PRIMARY KEY
    );
  END IF;

  IF to_regprocedure('auth.uid()') IS NULL THEN
    CREATE FUNCTION auth.uid()
    RETURNS UUID
    LANGUAGE SQL
    STABLE
    AS 'SELECT NULL::UUID';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role;
  END IF;
EXCEPTION
  WHEN insufficient_privilege THEN
    -- Supabase manages auth schema objects and platform roles.
    -- If this branch runs in Supabase Cloud, auth.users/auth.uid already exist.
    NULL;
END
$$;

CREATE TABLE IF NOT EXISTS ips (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT,
  department TEXT,
  contact_email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  role TEXT NOT NULL CHECK (role IN ('patient', 'ips', 'admin')),
  full_name TEXT NOT NULL,
  document_id TEXT,
  phone TEXT,
  telegram_chat_id BIGINT UNIQUE,
  ips_id UUID REFERENCES ips(id),
  assigned_doctor_id UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patient_clinical_info (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES profiles(id) NOT NULL,
  age INTEGER,
  gender TEXT CHECK (gender IN ('male', 'female', 'other')),
  height_cm NUMERIC,
  weight_kg NUMERIC,
  bmi NUMERIC GENERATED ALWAYS AS (weight_kg / ((height_cm / 100) ^ 2)) STORED,
  hypertension_history BOOLEAN DEFAULT FALSE,
  heart_disease_history BOOLEAN DEFAULT FALSE,
  stroke_history BOOLEAN DEFAULT FALSE,
  diabetes_history BOOLEAN DEFAULT FALSE,
  smoking TEXT CHECK (smoking IN ('never', 'former', 'current')),
  alcohol_intake BOOLEAN DEFAULT FALSE,
  physical_activity BOOLEAN DEFAULT TRUE,
  ever_married BOOLEAN,
  work_type TEXT,
  residence_type TEXT CHECK (residence_type IN ('urban', 'rural')),
  baseline_systolic NUMERIC,
  baseline_diastolic NUMERIC,
  baseline_heart_rate NUMERIC,
  cholesterol_level INTEGER CHECK (cholesterol_level IN (1, 2, 3)),
  glucose_level INTEGER CHECK (glucose_level IN (1, 2, 3)),
  diagnosis TEXT,
  treatment_notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vital_signs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES profiles(id) NOT NULL,
  recorded_at TIMESTAMPTZ DEFAULT NOW(),
  source TEXT DEFAULT 'telegram' CHECK (source IN ('telegram', 'web', 'manual')),
  systolic_bp NUMERIC,
  diastolic_bp NUMERIC,
  heart_rate NUMERIC,
  oxygen_saturation NUMERIC,
  temperature NUMERIC,
  glucose NUMERIC,
  weight_kg NUMERIC,
  pain_score INTEGER CHECK (pain_score BETWEEN 0 AND 10),
  dizziness_score INTEGER CHECK (dizziness_score BETWEEN 0 AND 10),
  dyspnea_score INTEGER CHECK (dyspnea_score BETWEEN 0 AND 10),
  raw_message TEXT,
  validated BOOLEAN DEFAULT FALSE,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS risk_predictions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES profiles(id) NOT NULL,
  vital_sign_id UUID REFERENCES vital_signs(id),
  predicted_at TIMESTAMPTZ DEFAULT NOW(),
  risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
  risk_probability NUMERIC NOT NULL,
  model_used TEXT NOT NULL,
  shap_values JSONB,
  top_risk_factors JSONB,
  confidence_score NUMERIC
);

CREATE TABLE IF NOT EXISTS clinical_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES profiles(id) NOT NULL,
  vital_sign_id UUID REFERENCES vital_signs(id),
  prediction_id UUID REFERENCES risk_predictions(id),
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  interpretation TEXT NOT NULL,
  recommendations TEXT NOT NULL,
  follow_up_actions TEXT,
  rag_sources JSONB,
  agent_response_full TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES profiles(id) NOT NULL,
  prediction_id UUID REFERENCES risk_predictions(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
  message TEXT NOT NULL,
  sent_to_patient BOOLEAN DEFAULT FALSE,
  sent_to_doctor BOOLEAN DEFAULT FALSE,
  email_sent BOOLEAN DEFAULT FALSE,
  telegram_sent BOOLEAN DEFAULT FALSE,
  acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_by UUID REFERENCES profiles(id),
  acknowledged_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS rag_documents (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  source TEXT NOT NULL,
  chunk_index INTEGER,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_ips_id ON profiles(ips_id);
CREATE INDEX IF NOT EXISTS idx_vital_signs_patient_recorded ON vital_signs(patient_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_predictions_patient_predicted ON risk_predictions(patient_id, predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_patient_created ON alerts(patient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding
  ON rag_documents USING ivfflat (embedding vector_cosine_ops);

CREATE OR REPLACE FUNCTION match_rag_documents(
  query_embedding vector(1536),
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  source TEXT,
  chunk_index INTEGER,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    rag_documents.id,
    rag_documents.title,
    rag_documents.source,
    rag_documents.chunk_index,
    rag_documents.content,
    rag_documents.metadata,
    1 - (rag_documents.embedding <=> query_embedding) AS similarity
  FROM rag_documents
  WHERE rag_documents.embedding IS NOT NULL
  ORDER BY rag_documents.embedding <=> query_embedding
  LIMIT match_count;
$$;

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION match_rag_documents(vector, INT) TO authenticated, service_role;

ALTER TABLE ips ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_clinical_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE vital_signs ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'ips' AND policyname = 'ips_select_authenticated'
  ) THEN
    CREATE POLICY ips_select_authenticated
      ON ips FOR SELECT TO authenticated
      USING (TRUE);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'profiles' AND policyname = 'profiles_select_own'
  ) THEN
    CREATE POLICY profiles_select_own
      ON profiles FOR SELECT TO authenticated
      USING (id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'profiles' AND policyname = 'profiles_insert_own'
  ) THEN
    CREATE POLICY profiles_insert_own
      ON profiles FOR INSERT TO authenticated
      WITH CHECK (id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'profiles' AND policyname = 'profiles_update_own'
  ) THEN
    CREATE POLICY profiles_update_own
      ON profiles FOR UPDATE TO authenticated
      USING (id = auth.uid())
      WITH CHECK (id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'patient_clinical_info' AND policyname = 'patient_clinical_info_select_own'
  ) THEN
    CREATE POLICY patient_clinical_info_select_own
      ON patient_clinical_info FOR SELECT TO authenticated
      USING (patient_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'vital_signs' AND policyname = 'vital_signs_select_own'
  ) THEN
    CREATE POLICY vital_signs_select_own
      ON vital_signs FOR SELECT TO authenticated
      USING (patient_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'vital_signs' AND policyname = 'vital_signs_insert_own'
  ) THEN
    CREATE POLICY vital_signs_insert_own
      ON vital_signs FOR INSERT TO authenticated
      WITH CHECK (patient_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'risk_predictions' AND policyname = 'risk_predictions_select_own'
  ) THEN
    CREATE POLICY risk_predictions_select_own
      ON risk_predictions FOR SELECT TO authenticated
      USING (patient_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'clinical_reports' AND policyname = 'clinical_reports_select_own'
  ) THEN
    CREATE POLICY clinical_reports_select_own
      ON clinical_reports FOR SELECT TO authenticated
      USING (patient_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'alerts' AND policyname = 'alerts_select_own'
  ) THEN
    CREATE POLICY alerts_select_own
      ON alerts FOR SELECT TO authenticated
      USING (patient_id = auth.uid() OR acknowledged_by = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'alerts' AND policyname = 'alerts_update_acknowledgement'
  ) THEN
    CREATE POLICY alerts_update_acknowledgement
      ON alerts FOR UPDATE TO authenticated
      USING (patient_id = auth.uid() OR acknowledged_by = auth.uid())
      WITH CHECK (patient_id = auth.uid() OR acknowledged_by = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'rag_documents' AND policyname = 'rag_documents_select_authenticated'
  ) THEN
    CREATE POLICY rag_documents_select_authenticated
      ON rag_documents FOR SELECT TO authenticated
      USING (TRUE);
  END IF;
END
$$;
