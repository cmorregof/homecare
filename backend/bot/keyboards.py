from __future__ import annotations


def yes_no_keyboard():
    from telegram import ReplyKeyboardMarkup

    return ReplyKeyboardMarkup(
        [["Sí", "No"]],
        one_time_keyboard=True,
        resize_keyboard=True,
        input_field_placeholder="Responde Sí o No",
    )


def remove_keyboard():
    from telegram import ReplyKeyboardRemove

    return ReplyKeyboardRemove()
