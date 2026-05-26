from fastapi import APIRouter

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("")
async def list_predictions() -> dict[str, str]:
    return {"status": "planned", "module": "predictions"}
