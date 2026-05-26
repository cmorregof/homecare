from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from config import settings
from db.supabase_client import get_supabase_admin_client


DOCUMENTS_DIR = Path(__file__).resolve().parent / "documents"
EMBEDDING_MODEL = "text-embedding-3-small"


@dataclass(frozen=True)
class DocumentChunk:
    title: str
    source: str
    chunk_index: int
    content: str
    metadata: dict[str, Any]


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or settings.rag_chunk_size
    overlap = overlap if overlap is not None else settings.rag_overlap
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def load_document_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    return ""


def build_document_chunks(documents_dir: Path = DOCUMENTS_DIR) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for path in sorted(documents_dir.glob("*")):
        if path.name.startswith(".") or path.suffix.lower() not in {".pdf", ".txt", ".md"}:
            continue
        text = load_document_text(path).strip()
        for chunk_index, chunk in enumerate(chunk_text(text)):
            chunks.append(
                DocumentChunk(
                    title=path.stem.replace("_", " ").title(),
                    source=path.name,
                    chunk_index=chunk_index,
                    content=chunk,
                    metadata={
                        "filename": path.name,
                        "extension": path.suffix.lower(),
                    },
                )
            )
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to generate RAG embeddings.")
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def index_documents(documents_dir: Path = DOCUMENTS_DIR) -> int:
    chunks = build_document_chunks(documents_dir)
    if not chunks:
        return 0

    embeddings = embed_texts([chunk.content for chunk in chunks])
    client = get_supabase_admin_client()
    rows = [
        {
            "title": chunk.title,
            "source": chunk.source,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "embedding": embedding,
            "metadata": chunk.metadata,
        }
        for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]
    client.table("rag_documents").insert(rows).execute()
    return len(rows)
