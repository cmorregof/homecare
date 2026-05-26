# Documentos clinicos RAG

Ubicar aqui los documentos fuente en PDF, TXT o Markdown:

- `minsalud_ecv_2022.pdf`
- `framingham_colombia.pdf`
- `aha_stroke_guidelines_2024.pdf`
- guia colombiana de hipertension arterial
- definicion y aplicacion del MEWS

El indexador `backend/rag/embeddings.py` divide cada documento en chunks de 500 tokens aproximados con overlap de 50 y los almacena en Supabase `rag_documents`.
