from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Outbound:
    """Mensaje hacia el paciente, independiente del canal.

    `buttons` son pares (id, título). WhatsApp acepta hasta 3 botones de respuesta con
    títulos de máximo 20 caracteres; el cliente del canal aplica esos límites.
    """

    text: str
    buttons: tuple[tuple[str, str], ...] = ()
