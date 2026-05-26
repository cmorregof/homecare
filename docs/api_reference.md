# API Reference

Base local: `http://localhost:8000`

## Sistema

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check del backend |
| GET | `/` | Metadatos básicos del servicio |

## Endpoints planeados

| Módulo | Ruta base | Estado |
|---|---|---|
| Pacientes | `/patients` | Sprint 5 |
| Signos vitales | `/vitals` | Sprint 3-4 |
| Predicciones | `/predictions` | Sprint 2 |
| Alertas | `/alerts` | Sprint 4 |
| Reportes | `/reports` | Sprint 3 |
| Usuarios | `/users` | Sprint 5 |
| Modelos ML | `/models` | Sprint 2 y 5 |
| ML predict | `/ml/predict` | Sprint 2 |

## Health check

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "homecare-ccv-backend",
  "environment": "development"
}
```
