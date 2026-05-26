# Operacion en produccion

## Rutina diaria

- Revisar `/health` del backend.
- Revisar errores de Railway.
- Revisar deploy activo en Vercel.
- Confirmar que el bot responde `/ayuda`.
- Revisar alertas no reconocidas en `/ips/alerts`.

## Monitoreo minimo

| Superficie | Indicador | Umbral de accion |
| --- | --- | --- |
| Backend | `/health` no responde | Revisar logs Railway |
| Bot | Telegram `getMe` falla | Rotar token o revisar variable |
| ML | `model_used=clinical_rules_fallback` repetido | Revisar `ML_MODEL_PATH` |
| Supabase | inserts fallidos | Revisar service key y RLS |
| Email | `email_sent=false` en alertas alto/critico | Revisar Resend |

## Comandos utiles

Backend local:

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend local:

```bash
cd frontend
npm run dev
```

Tests:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
cd frontend
npm run lint
npm run build
npm run typecheck
```

Smoke remoto:

```bash
python scripts/smoke_deployment.py \
  --backend-url "$BACKEND_PUBLIC_URL" \
  --frontend-url "$FRONTEND_PUBLIC_URL"
```

## Respuesta a incidentes

### ML no carga

1. Confirmar que `backend/ml/models/best_model.pkl` existe en el build.
2. Confirmar `ML_MODEL_PATH=ml/models/best_model.pkl` en Railway.
3. Probar `/ml/predict`.
4. Si persiste, el sistema usa reglas clinicas fallback.

### Bot no responde

1. Validar `TELEGRAM_BOT_TOKEN`.
2. Validar `TELEGRAM_WEBHOOK_URL=https://<railway-domain>/webhook`.
3. Ejecutar `POST /telegram/webhook/setup`.
4. Revisar logs Railway.

### Alertas no salen

1. Revisar `alerts` en Supabase.
2. Confirmar `telegram_chat_id` de paciente y medico.
3. Confirmar `RESEND_API_KEY` y `FROM_EMAIL`.
4. Revisar `email_sent` y `telegram_sent`.

## Criterios de salida Sprint 6

- Backend Docker build OK.
- Backend tests OK.
- Frontend lint/build/typecheck OK.
- GitHub Actions configurado.
- Railway y Vercel documentados.
- Smoke script disponible.
- Token Telegram rotado antes de produccion real.
