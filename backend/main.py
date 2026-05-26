from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.agents import router as agents_router
from config import settings


app = FastAPI(
    title="HomecareCCV API",
    description="Backend para monitoreo domiciliario de pacientes cardio-cerebrovasculares.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
    }
