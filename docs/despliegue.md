# Despliegue Sprint 6

Esta guia deja HomecareCCV listo para produccion con backend en Railway, frontend en Vercel y datos en Supabase.

## 1. Supabase

1. Crear un proyecto Supabase.
2. Abrir SQL Editor.
3. Ejecutar `backend/db/schemas.sql`.
4. Confirmar que `pgvector` quedo habilitado.
5. Activar Realtime para `alerts` si se requiere actualizacion en vivo en el dashboard IPS.
6. Crear usuarios en Supabase Auth.
7. Crear filas correspondientes en `profiles` con `role` en `patient`, `ips` o `admin`.

Variables necesarias:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=...
SUPABASE_ANON_KEY=...
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## 2. Backend en Railway

Railway debe apuntar al directorio `backend/`. El servicio usa `backend/Dockerfile` y `backend/railway.json`.

Variables de Railway:

```env
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
SUPABASE_ANON_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_URL=https://<railway-domain>/webhook
RESEND_API_KEY=...
FROM_EMAIL=alertas@homecareccv.co
ENVIRONMENT=production
ML_API_URL=https://<railway-domain>
ML_MODEL_PATH=ml/models/best_model.pkl
RAG_CHUNK_SIZE=500
RAG_OVERLAP=50
MONITORING_INTERVAL_HOURS=6
```

El contenedor escucha el `PORT` que Railway inyecta. Si `PORT` no existe, usa `8000`.

Validaciones:

```bash
curl https://<railway-domain>/health
curl -X POST https://<railway-domain>/telegram/webhook/setup
```

## 3. Frontend en Vercel

Vercel debe usar `frontend/` como root directory. El archivo `frontend/vercel.json` define `npm ci` y `npm run build`.

Variables de Vercel:

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=https://<railway-domain>
NEXT_PUBLIC_TELEGRAM_BOT_URL=https://t.me/project918_homecare_bot
```

Validaciones:

```bash
curl https://<vercel-domain>
```

## 4. GitHub Actions

Los workflows quedan en:

- `.github/workflows/backend_deploy.yml`
- `.github/workflows/frontend_deploy.yml`

Secrets requeridos para desplegar:

```text
RAILWAY_TOKEN
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
```

Variables opcionales de GitHub Actions:

```text
RAILWAY_SERVICE_NAME=backend
BACKEND_PUBLIC_URL=https://<railway-domain>
```

Si los secrets no existen, los workflows ejecutan checks y omiten el deploy.

## 5. Smoke tests post-deploy

```bash
python scripts/smoke_deployment.py \
  --backend-url https://<railway-domain> \
  --frontend-url https://<vercel-domain>
```

Para validar Telegram:

```bash
TELEGRAM_BOT_TOKEN=... python scripts/smoke_deployment.py
```

## 6. Prueba end-to-end

1. Entrar al bot: `https://t.me/project918_homecare_bot`.
2. Ejecutar `/start`.
3. Vincular documento de un paciente existente en `profiles.document_id`.
4. Ejecutar `/vitales`.
5. Reportar presion, pulso, saturacion, glucosa y sintomas.
6. Confirmar en Supabase:
   - `vital_signs`
   - `risk_predictions`
   - `clinical_reports`
   - `alerts` si riesgo alto o critico
7. Abrir Vercel:
   - `/patient/dashboard`
   - `/ips/alerts`
   - `/admin/models`

## 7. Rotacion de secretos

El token de Telegram fue compartido durante desarrollo. Antes de produccion:

1. Abrir BotFather.
2. Ejecutar `/revoke`.
3. Copiar el nuevo token.
4. Actualizar Railway `TELEGRAM_BOT_TOKEN`.
5. Ejecutar `/telegram/webhook/setup`.

Nunca commitear `.env`, `.env.local` ni tokens en mensajes publicos.

## Referencias operativas

- Railway CLI `railway up` soporta `--service` y `--detach`: https://docs.railway.com/cli/up
- Railway recomienda tokens de proyecto para CI/CD: https://docs.railway.com/cli/deploying
- Vercel CLI permite `vercel build` y `vercel deploy --prebuilt`: https://vercel.com/docs/deployments/git/vercel-for-github
