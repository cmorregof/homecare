from __future__ import annotations

from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from config import settings
from db.supabase_client import get_supabase_admin_client
from rag.embeddings import DOCUMENTS_DIR, EMBEDDING_MODEL, chunk_text, load_document_text


FALLBACK_CLINICAL_CONTEXT = [
    {
        "title": "Criterios MEWS",
        "source": "fallback_clinical_rules",
        "chunk_index": 0,
        "content": (
            "MEWS prioriza presión arterial, frecuencia cardíaca, estado respiratorio, "
            "temperatura y estado neurológico para identificar deterioro clínico temprano."
        ),
        "metadata": {"fallback": True},
        "similarity": 0.0,
    },
    {
        "title": "Seguridad en monitoreo domiciliario",
        "source": "fallback_clinical_rules",
        "chunk_index": 1,
        "content": (
            "En pacientes cardio-cerebrovasculares, presión sistólica mayor a 180 mmHg, "
            "saturación menor a 88%, frecuencia cardíaca mayor a 130 o menor a 40, "
            "y glucosa mayor a 400 o menor a 50 requieren recomendación de urgencias."
        ),
        "metadata": {"fallback": True},
        "similarity": 0.0,
    },
    {
        "title": "Prevención secundaria ECV",
        "source": "fallback_clinical_rules",
        "chunk_index": 2,
        "content": (
            "Las recomendaciones no deben cambiar tratamientos. Deben reforzar adherencia, "
            "vigilancia de síntomas, contacto con el equipo tratante y activación de urgencias "
            "cuando haya signos de alarma."
        ),
        "metadata": {"fallback": True},
        "similarity": 0.0,
    },
]


class ClinicalRetriever:
    def __init__(self, client: Any | None = None, documents_dir: Path = DOCUMENTS_DIR) -> None:
        self._client = client
        self.documents_dir = documents_dir

    @property
    def client(self) -> Any | None:
        if self._client is not None:
            return self._client
        try:
            self._client = get_supabase_admin_client()
        except RuntimeError:
            self._client = None
        return self._client

    async def retrieve(self, query: str, match_count: int = 5) -> list[dict[str, Any]]:
        if settings.openai_api_key and self.client is not None:
            try:
                return await self._retrieve_from_supabase(query, match_count)
            except Exception:
                return self._retrieve_from_local_documents(query, match_count)
        return self._retrieve_from_local_documents(query, match_count)

    async def _retrieve_from_supabase(self, query: str, match_count: int) -> list[dict[str, Any]]:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        embedding_response = await client.embeddings.create(model=EMBEDDING_MODEL, input=query)
        query_embedding = embedding_response.data[0].embedding
        result = self.client.rpc(
            "match_rag_documents",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
            },
        ).execute()
        return [dict(row) for row in result.data]

    def _retrieve_from_local_documents(self, query: str, match_count: int) -> list[dict[str, Any]]:
        query_terms = set(query.lower().split())
        matches: list[dict[str, Any]] = []
        for path in sorted(self.documents_dir.glob("*")):
            if path.name.startswith(".") or path.suffix.lower() not in {".pdf", ".txt", ".md"}:
                continue
            text = load_document_text(path)
            for chunk_index, chunk in enumerate(chunk_text(text)):
                score = _lexical_score(query_terms, chunk)
                if score == 0:
                    continue
                matches.append(
                    {
                        "title": path.stem.replace("_", " ").title(),
                        "source": path.name,
                        "chunk_index": chunk_index,
                        "content": chunk,
                        "metadata": {"filename": path.name, "fallback": "local"},
                        "similarity": score,
                    }
                )
        matches.sort(key=lambda item: float(item["similarity"]), reverse=True)
        if matches:
            return matches[:match_count]
        return FALLBACK_CLINICAL_CONTEXT[:match_count]


async def retrieve_clinical_context(query: str, match_count: int = 5) -> list[dict[str, Any]]:
    return await ClinicalRetriever().retrieve(query, match_count)


def _lexical_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    text_terms = set(text.lower().split())
    return len(query_terms.intersection(text_terms)) / len(query_terms)
