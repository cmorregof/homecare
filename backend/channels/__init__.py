"""Canales de conversación de Carmen.

El cerebro (validadores, overrides, pipeline LangGraph, agente médico, voz) es uno solo.
Cada canal es un adaptador fino: Telegram vive en `bot/` (ConversationHandler), WhatsApp
en `channels/whatsapp/`, y el chat web reutiliza `bot.handlers.carmen_web_chat_reply`.
`channels/intake.py` es el motor de intake guiado independiente del canal.
"""
