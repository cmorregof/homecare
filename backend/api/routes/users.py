from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users() -> dict[str, str]:
    return {"status": "planned", "module": "users"}
