import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def list_models() -> dict[str, Any]:
    results_path = Path(__file__).resolve().parents[2] / "ml" / "models" / "comparison_results.json"
    if not results_path.exists():
        return {"status": "not_trained", "module": "models", "results": []}
    return json.loads(results_path.read_text(encoding="utf-8"))
