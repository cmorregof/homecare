"""Inline keyboard builders for Telegram conversations."""


def yes_no_keyboard() -> list[list[dict[str, str]]]:
    return [
        [{"text": "Sí", "callback_data": "yes"}],
        [{"text": "No", "callback_data": "no"}],
    ]
