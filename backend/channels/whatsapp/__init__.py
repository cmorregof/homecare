"""Canal WhatsApp de Carmen (WhatsApp Cloud API de Meta).

Segundo canal sobre el mismo cerebro. Se activa solo si `WHATSAPP_ACCESS_TOKEN` y
`WHATSAPP_PHONE_NUMBER_ID` están configurados; sin ellos, las rutas `/whatsapp/*`
responden 503 y el resto del servicio (Telegram, web, ML) no cambia.
"""
