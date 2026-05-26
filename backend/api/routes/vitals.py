from fastapi import APIRouter

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.get("")
async def list_vitals() -> dict[str, str]:
    return {"status": "planned", "module": "vitals"}
