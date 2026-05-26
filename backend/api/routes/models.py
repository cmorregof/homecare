from fastapi import APIRouter

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def list_models() -> dict[str, str]:
    return {"status": "planned", "module": "models"}
