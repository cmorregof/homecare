from fastapi import APIRouter

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
async def list_patients() -> dict[str, str]:
    return {"status": "planned", "module": "patients"}
