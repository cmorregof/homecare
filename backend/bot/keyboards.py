from __future__ import annotations


YES_NO_LABELS = {
    "es": (["Sí", "No"], "Responde Sí o No"),
    "en": (["Yes", "No"], "Answer Yes or No"),
}


def yes_no_keyboard(language: str = "es"):
    from telegram import ReplyKeyboardMarkup

    labels, placeholder = YES_NO_LABELS.get(language, YES_NO_LABELS["es"])
    return ReplyKeyboardMarkup(
        [labels],
        one_time_keyboard=True,
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )


def language_keyboard():
    """Botones inline: llegan como callback_query, así que funcionan incluso en mitad
    del intake guiado (los estados del ConversationHandler solo escuchan texto)."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Español 🇨🇴", callback_data="lang:es"),
                InlineKeyboardButton("English 🇬🇧", callback_data="lang:en"),
            ]
        ]
    )


def remove_keyboard():
    from telegram import ReplyKeyboardRemove

    return ReplyKeyboardRemove()
