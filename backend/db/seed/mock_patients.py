"""Seed helpers for Sprint 1.

Concrete Supabase insert logic is implemented after Auth flows are defined.
"""


MOCK_PATIENTS: list[dict[str, object]] = [
    {
        "full_name": "Paciente Demo Atlántico",
        "role": "patient",
        "document_id": "1000000000",
        "phone": "+573001112233",
    }
]
