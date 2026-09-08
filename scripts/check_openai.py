#!/usr/bin/env python3
"""Sonda de diagnóstico de OpenAI para HomecareCCV.

Carga OPENAI_API_KEY desde backend/.env (nunca la imprime) y verifica, en orden:
1) que la key autentica (lista de modelos),
2) si el modelo configurado (OPENAI_MODEL, por defecto gpt-6-astra) está disponible,
3) una llamada real de chat (la que hacen el médico y la voz de Carmen).

Uso, desde la raíz del repo:
    .venv/bin/python scripts/check_openai.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from config import settings  # carga backend/.env
from openai import OpenAI, OpenAIError


def main() -> None:
    key = settings.openai_api_key
    if not key:
        print("FALLO: OPENAI_API_KEY no está definida en backend/.env")
        return
    print(f"Key presente: sí (longitud {len(key)}, empieza por {key[:6]}…)")

    client = OpenAI(api_key=key)

    try:
        models = [m.id for m in client.models.list().data]
        print(f"Autenticación: OK — {len(models)} modelos visibles")
        chat_like = sorted(m for m in models if "gpt" in m or "o4" in m)[:15]
        print("Modelos de chat disponibles:", ", ".join(chat_like) or "(ninguno)")
        print(f"¿{settings.openai_model} disponible?:", "SÍ" if settings.openai_model in models else "NO")
    except OpenAIError as exc:
        print(f"FALLO autenticando (models.list): {exc}")
        return

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            reasoning_effort=settings.openai_reasoning_effort,
            max_completion_tokens=200,
            messages=[{"role": "user", "content": "Di 'hola' y nada más."}],
        )
        print(f"Chat {settings.openai_model}: OK →", (response.choices[0].message.content or "").strip())
    except OpenAIError as exc:
        print(f"FALLO en chat {settings.openai_model}: {exc}")

    try:
        emb = client.embeddings.create(model="text-embedding-3-small", input="prueba")
        print(f"Embeddings (RAG): OK — dim {len(emb.data[0].embedding)}")
    except OpenAIError as exc:
        print(f"FALLO en embeddings (RAG): {exc}")


if __name__ == "__main__":
    main()
