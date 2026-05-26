from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts() -> dict[str, str]:
    return {"status": "planned", "module": "alerts"}
