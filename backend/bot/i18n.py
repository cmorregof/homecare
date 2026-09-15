"""Idioma de Carmen hacia el paciente (solo la voz de Carmen).

Los reportes clínicos, las alertas a médicos, los correos y el dashboard siguen en
español. Aquí solo vive lo que el paciente lee:

- el catálogo de mensajes deterministas que no pasan por la voz LLM (vinculación,
  registro, comandos, avisos de seguridad), y
- las utilidades para resolver el idioma: elección explícita (saludo o /idioma),
  `profiles.language` guardado, o el `language_code` que Telegram envía en cada mensaje.

Los borradores clínicos que sí pasan por la voz LLM siguen escribiéndose en español;
la voz recibe el idioma en el payload (`idioma`) y traduce manteniendo la personalidad.
"""
from __future__ import annotations

import unicodedata

SUPPORTED_LANGUAGES: tuple[str, ...] = ("es", "en")
DEFAULT_LANGUAGE = "es"

LANGUAGE_NAMES = {"es": "español", "en": "English"}


def normalize_language(value: str | None) -> str:
    """Reduce 'en-GB', 'es_CO' o 'EN' al idioma soportado; desconocido → español."""
    code = str(value or "").strip().lower().replace("_", "-").split("-")[0]
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def language_from_telegram(language_code: str | None) -> str:
    """`User.language_code` de Telegram (idioma del teléfono del paciente)."""
    return normalize_language(language_code)


_CHOICES = {
    "es": {"es", "espanol", "spanish", "castellano", "1"},
    "en": {"en", "english", "ingles", "2"},
}


def parse_language_choice(text: str) -> str | None:
    """Interpreta 'Español', 'english', 'inglés', '🇬🇧 English', 'en'… → 'es' | 'en' | None."""
    cleaned = _strip_accents(text).lower()
    for flag in ("🇨🇴", "🇬🇧", "🇺🇸", "🇪🇸"):
        cleaned = cleaned.replace(flag, " ")
    cleaned = " ".join(cleaned.split())
    for language, options in _CHOICES.items():
        if cleaned in options:
            return language
    return None


def t(language: str, key: str, **kwargs: object) -> str:
    """Mensaje determinista en el idioma del paciente (cae a español si falta)."""
    entry = MESSAGES[key]
    template = entry.get(normalize_language(language)) or entry[DEFAULT_LANGUAGE]
    return template.format(**kwargs)


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.strip())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


# Saludo bilingüe: se muestra antes de saber el idioma, así que va en los dos.
CHOOSE_LANGUAGE = (
    "Hola, soy Carmen, la enfermera virtual de HomecareCCV. 👵\n"
    "Hi, I'm Carmen, HomecareCCV's virtual nurse. 👵\n\n"
    "¿En qué idioma prefieres que te hable? / Which language would you like me to use?"
)

LANGUAGE_NOT_UNDERSTOOD = (
    "No te entendí. Toca un botón o escribe 'español' o 'english'.\n"
    "I didn't catch that. Tap a button or type 'español' or 'english'."
)

# Los textos en español son los que ya usaba el bot (sin cambios de contenido).
MESSAGES: dict[str, dict[str, str]] = {
    "start_linked": {
        "es": (
            "Hola {name}. Tu cuenta ya está vinculada a HomecareCCV.\n\n"
            "Cuando quieras registrar signos vitales usa /vitales. "
            "Para cambiar de idioma usa /idioma."
        ),
        "en": (
            "Hi {name}. Your account is already linked to HomecareCCV.\n\n"
            "Whenever you want to log your vital signs, use /vitales. "
            "To change language, use /idioma."
        ),
    },
    "language_set": {
        "es": "Perfecto, te hablaré en español. 👵",
        "en": "Great, I'll talk to you in English. 👵",
    },
    "ask_document": {
        "es": (
            "Para empezar, escríbeme tu número de documento de identidad. "
            "Si ya tienes cuenta la vinculo, y si no, te registro en un momento."
        ),
        "en": (
            "To get started, send me your ID (document) number. "
            "If you already have an account I'll link it; if not, I'll register you right away."
        ),
    },
    "doc_invalid": {
        "es": (
            "Ese texto no parece un número de documento. Escríbeme solo tu documento, "
            "por ejemplo: 1234567890 (o si te dieron uno tipo cc123456, tal cual)."
        ),
        "en": (
            "That doesn't look like an ID number. Send me just your document number, "
            "for example: 1234567890 (or, if you were given one like cc123456, exactly like that)."
        ),
    },
    "doc_unknown_offer_registration": {
        "es": (
            "No encontré una cuenta con ese documento, pero puedo crearla ahora mismo.\n\n"
            "Dime tu nombre completo (nombre y apellido) para registrarte, "
            "o escribe \"cancelar\" si prefieres no hacerlo."
        ),
        "en": (
            "I couldn't find an account with that document, but I can create one right now.\n\n"
            "Tell me your full name (first and last name) to register, "
            "or type \"cancel\" if you'd rather not."
        ),
    },
    "linked_ok": {
        "es": "Listo, {name}. Tu Telegram quedó vinculado.\n\nPara registrar signos vitales usa /vitales.",
        "en": "Done, {name}. Your Telegram is now linked.\n\nTo log your vital signs, use /vitales.",
    },
    "registration_cancelled": {
        "es": "Listo, no creé ninguna cuenta. Cuando quieras registrarte, envíame tu documento de nuevo.",
        "en": "All right, I didn't create any account. Whenever you want to register, send me your document again.",
    },
    "already_had_account": {
        "es": (
            "Listo, {name}. Ese documento ya tenía cuenta, "
            "así que quedaste vinculado.\n\nPara registrar signos vitales usa /vitales."
        ),
        "en": (
            "Done, {name}. That document already had an account, "
            "so you're now linked.\n\nTo log your vital signs, use /vitales."
        ),
    },
    "need_full_name": {
        "es": "Para registrarte necesito tu nombre completo, por ejemplo: Ana María Pérez.",
        "en": "To register you I need your full name, for example: Ana María Pérez.",
    },
    "account_create_failed": {
        "es": (
            "No pude crear tu cuenta en este momento. Intenta de nuevo en unos minutos "
            "o pide apoyo a tu IPS."
        ),
        "en": (
            "I couldn't create your account right now. Please try again in a few minutes "
            "or ask your clinic (IPS) for help."
        ),
    },
    "account_created": {
        "es": (
            "¡Bienvenido/a, {name}! Tu cuenta quedó creada.{doctor_note}\n\n"
            "Registra tus primeros signos vitales con /vitales."
        ),
        "en": (
            "Welcome, {name}! Your account has been created.{doctor_note}\n\n"
            "Log your first vital signs with /vitales."
        ),
    },
    "doctor_note": {
        "es": "\nTu médico asignado es {doctor}; recibirá tus alertas de riesgo.",
        "en": "\nYour assigned doctor is {doctor}; they will receive your risk alerts.",
    },
    "help": {
        "es": (
            "Comandos HomecareCCV:\n"
            "/start - vincular tu cuenta de Telegram\n"
            "/vitales - registrar signos vitales paso a paso\n"
            "/registro - iniciar el mismo registro guiado\n"
            "/estado - ver tu último nivel de riesgo\n"
            "/historial - ver tus últimas 5 mediciones\n"
            "/emergencia - avisar de inmediato al equipo de salud\n"
            "/idioma - cambiar el idioma en que te hablo\n"
            "/ayuda - ver esta lista"
        ),
        "en": (
            "HomecareCCV commands:\n"
            "/start - link your Telegram account\n"
            "/vitales - log your vital signs step by step\n"
            "/registro - start the same guided log\n"
            "/estado - see your latest risk level\n"
            "/historial - see your last 5 measurements\n"
            "/emergencia - alert your care team right away\n"
            "/idioma - change the language I speak to you\n"
            "/ayuda - show this list"
        ),
    },
    "status_none": {
        "es": "Aún no tengo predicciones registradas para tu cuenta. Puedes reportar signos con /vitales.",
        "en": "I don't have any predictions for your account yet. You can report your vitals with /vitales.",
    },
    "history_none": {
        "es": "Aún no tengo mediciones registradas. Puedes empezar con /vitales.",
        "en": "I don't have any measurements yet. You can start with /vitales.",
    },
    "emergency_reply": {
        "es": (
            "Activé una alerta inmediata para tu equipo de salud.\n\n"
            "Si tienes dolor fuerte en el pecho, dificultad marcada para respirar, debilidad en un lado "
            "del cuerpo, confusión, desmayo o presión muy alta, llama al 123 o ve a urgencias."
        ),
        "en": (
            "I've triggered an immediate alert to your care team.\n\n"
            "If you have severe chest pain, marked difficulty breathing, weakness on one side "
            "of your body, confusion, fainting or very high blood pressure, call 123 or go to the emergency room."
        ),
    },
    "analyzing": {
        "es": "¡Listo! Estoy analizando tus datos...",
        "en": "Got it! I'm analyzing your data...",
    },
    "analyzing_free_text": {
        "es": "Recibí tus signos. Estoy analizándolos...",
        "en": "I received your vitals. Analyzing them...",
    },
    "final_response_missing": {
        "es": "Recibí tus datos, pero no pude construir la respuesta final.",
        "en": "I received your data, but I couldn't build the final reply.",
    },
    "received": {
        "es": "Recibí tus datos.",
        "en": "I received your data.",
    },
    "cancelled": {
        "es": "Registro cancelado. Puedes iniciar de nuevo con /vitales.",
        "en": "Log cancelled. You can start again with /vitales.",
    },
    "need_link_first": {
        "es": "Primero necesito vincular tu cuenta. Envíame tu número de documento de identidad.",
        "en": "First I need to link your account. Send me your ID (document) number.",
    },
    "only_patients": {
        "es": "Tu cuenta está vinculada, pero este flujo está habilitado para pacientes.",
        "en": "Your account is linked, but this flow is only enabled for patients.",
    },
    "question_pulse": {
        "es": (
            "Ahora ponte el oxímetro en el dedo, espera a que la cifra se estabilice "
            "y dime tu pulso. Ejemplo: 75"
        ),
        "en": (
            "Now put the oximeter on your finger, wait for the number to settle "
            "and tell me your pulse. Example: 75"
        ),
    },
    "question_pressure": {
        "es": (
            "Ahora la presión arterial: brazo apoyado en la mesa a la altura del corazón, "
            "sin hablar durante la medición. Escríbela así: 120/80"
        ),
        "en": (
            "Now your blood pressure: arm resting on the table at heart level, "
            "no talking during the reading. Write it like this: 120/80"
        ),
    },
    # Avisos de seguridad dentro del intake: deterministas, nunca pasan por el LLM.
    "respiratory_high_warning": {
        "es": (
            "Mijo, eso equivale a {per_minute} respiraciones por minuto y es más de lo "
            "que me gusta ver. Si además sientes ahogo marcado, dolor en el pecho o mucho "
            "decaimiento, no esperes: ve a urgencias o marca el 123 ya mismo. "
            "Si te sientes bien, seguimos con calma.\n\n"
            "{next_question}"
        ),
        "en": (
            "Sweetie, that's {per_minute} breaths per minute, which is more than I like "
            "to see. If you also feel very short of breath, chest pain or very weak, "
            "don't wait: go to the emergency room or call 123 right now. "
            "If you feel fine, we'll carry on calmly.\n\n"
            "{next_question}"
        ),
    },
    "oxygen_low_warning": {
        "es": (
            "Gracias por decírmelo, mijo. Esa saturación me preocupa de verdad. "
            "Revisa primero que el oxímetro haya marcado bien; y si marcó bien, o sientes "
            "ahogo, labios morados, dolor en el pecho, confusión o mucho decaimiento, "
            "no esperes nada: urgencias o el 123 ahora mismo.\n\n"
            "{next_question}"
        ),
        "en": (
            "Thank you for telling me, sweetie. That oxygen level truly worries me. "
            "First check that the oximeter read correctly; if it did, or if you feel "
            "short of breath, blue lips, chest pain, confusion or very weak, "
            "don't wait at all: emergency room or 123 right now.\n\n"
            "{next_question}"
        ),
    },
    "free_text_emergency": {
        "es": (
            "{lead}Si esto está pasando ahora mismo, no esperes mi respuesta: "
            "llama al 123 o ve a urgencias, especialmente si hay dolor fuerte en el pecho, "
            "dificultad para respirar, desmayo, confusión, debilidad en un lado del cuerpo "
            "o problemas para hablar.\n\n"
            "Si puedes hacerlo sin retrasar la atención, usa /emergencia para avisar también a tu equipo de salud."
        ),
        "en": (
            "{lead}If this is happening right now, don't wait for my reply: "
            "call 123 or go to the emergency room, especially if there is severe chest pain, "
            "difficulty breathing, fainting, confusion, weakness on one side of the body "
            "or trouble speaking.\n\n"
            "If you can do it without delaying care, use /emergencia to alert your care team as well."
        ),
    },
    "free_text_emergency_lead": {
        "es": "{first_name}, te leo. ",
        "en": "{first_name}, I hear you. ",
    },
    "free_text_emergency_lead_anonymous": {
        "es": "Te leo. ",
        "en": "I hear you. ",
    },
    "reminder": {
        "es": (
            "Hola {name}. Es hora de registrar tus signos vitales.\n"
            "Usa /vitales para iniciar el reporte guiado."
        ),
        "en": (
            "Hi {name}. It's time to log your vital signs.\n"
            "Use /vitales to start the guided report."
        ),
    },
}
