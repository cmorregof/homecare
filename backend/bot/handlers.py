from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from agents.nurse_agent import NurseAgent, parse_vital_signs_message
from bot.keyboards import remove_keyboard, yes_no_keyboard
from bot.validators import (
    is_affirmative,
    is_negative,
    parse_blood_pressure,
    parse_optional_number,
    parse_required_number,
    parse_score,
)
from db.repository import HomecareRepository
from notifications.email import send_risk_email_alert
from notifications.telegram_alerts import send_telegram_risk_alert
from utils.risk_levels import RISK_LEVELS, normalize_risk_level


SUPPORTED_COMMANDS = [
    "/start",
    "/registro",
    "/vitales",
    "/estado",
    "/historial",
    "/ayuda",
    "/emergencia",
]

CONFIRM_TENSIOMETER, BLOOD_PRESSURE, HEART_RATE, OXYGEN, GLUCOSE, PAIN, DIZZINESS, DYSPNEA = range(8)


@dataclass
class BotDependencies:
    repository: HomecareRepository
    nurse_agent: NurseAgent


def default_dependencies() -> BotDependencies:
    repository = HomecareRepository()
    return BotDependencies(repository=repository, nurse_agent=NurseAgent(repository=repository))


def register_handlers(application: Any, dependencies: BotDependencies | None = None) -> None:
    application.bot_data["homecare_dependencies"] = dependencies or default_dependencies()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ayuda", help_command))
    application.add_handler(CommandHandler("estado", status_command))
    application.add_handler(CommandHandler("historial", history_command))
    application.add_handler(CommandHandler("emergencia", emergency_command))
    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("registro", start_vitals_conversation),
                CommandHandler("vitales", start_vitals_conversation),
            ],
            states={
                CONFIRM_TENSIOMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_tensiometer_step)],
                BLOOD_PRESSURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, blood_pressure_step)],
                HEART_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, heart_rate_step)],
                OXYGEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, oxygen_step)],
                GLUCOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, glucose_step)],
                PAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, pain_step)],
                DIZZINESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, dizziness_step)],
                DYSPNEA: [MessageHandler(filters.TEXT & ~filters.COMMAND, dyspnea_step)],
            },
            fallbacks=[
                CommandHandler("cancelar", cancel_command),
                CommandHandler("ayuda", help_command),
            ],
        )
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, document_or_free_text_message))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deps = _deps(context)
    chat_id = _chat_id(update)
    profile = await _profile_by_chat(deps.repository, chat_id)
    if profile:
        _cache_profile(context, profile)
        await _reply(
            update,
            f"Hola {profile.get('full_name', '')}. Tu cuenta ya está vinculada a HomecareCCV.\n\n"
            "Cuando quieras registrar signos vitales usa /vitales.",
        )
        return
    context.user_data["awaiting_document"] = True
    await _reply(
        update,
        "Hola, soy Carmen, la enfermera virtual de HomecareCCV.\n\n"
        "Para vincular tu cuenta de Telegram, escríbeme tu número de documento de identidad.",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    await _reply(update, help_message())
    return ConversationHandler.END


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deps = _deps(context)
    profile = await ensure_linked_patient(update, context, deps)
    if not profile:
        return
    prediction = await deps.repository.get_latest_risk_prediction(str(profile["id"]))
    await _reply(update, format_latest_status_message(prediction))


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deps = _deps(context)
    profile = await ensure_linked_patient(update, context, deps)
    if not profile:
        return
    rows = await deps.repository.get_recent_vital_signs(str(profile["id"]), limit=5)
    await _reply(update, format_vital_history_message(rows))


async def emergency_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deps = _deps(context)
    profile = await ensure_linked_patient(update, context, deps)
    if not profile:
        return
    patient_id = str(profile["id"])
    message = (
        f"Alerta manual HomecareCCV: el paciente {profile.get('full_name') or patient_id} "
        "activó /emergencia desde Telegram."
    )
    recipients = await _alert_recipients(deps.repository, patient_id)
    payload = {
        **recipients,
        "patient_id": patient_id,
        "patient_name": profile.get("full_name"),
        "risk_level": "critical",
        "message": message,
        "recommendations": "Contactar al paciente de inmediato y orientar urgencias si hay signos de alarma.",
        "vital_signs": {},
    }
    telegram_sent = await send_telegram_risk_alert(payload)
    email_sent = await send_risk_email_alert(payload)
    await deps.repository.save_alert(
        {
            "patient_id": patient_id,
            "risk_level": "critical",
            "message": message,
            "sent_to_patient": bool(recipients.get("patient_telegram_chat_id") and telegram_sent),
            "sent_to_doctor": bool(
                (recipients.get("doctor_telegram_chat_id") and telegram_sent)
                or (recipients.get("doctor_email") and email_sent)
            ),
            "email_sent": email_sent,
            "telegram_sent": telegram_sent,
        }
    )
    await _reply(
        update,
        "Activé una alerta inmediata para tu equipo de salud.\n\n"
        "Si tienes dolor fuerte en el pecho, dificultad marcada para respirar, debilidad en un lado "
        "del cuerpo, confusión, desmayo o presión muy alta, llama al 123 o ve a urgencias.",
    )


async def start_vitals_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    deps = _deps(context)
    profile = await ensure_linked_patient(update, context, deps)
    if not profile:
        return ConversationHandler.END
    context.user_data["vitals_draft"] = {}
    await _reply(
        update,
        f"Hola {profile.get('full_name', '')}. Vamos a registrar tus signos vitales.\n"
        "¿Tienes tu tensiómetro a la mano?",
        reply_markup=yes_no_keyboard(),
    )
    return CONFIRM_TENSIOMETER


async def confirm_tensiometer_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = _message_text(update)
    if is_negative(answer):
        await _reply(
            update,
            "De acuerdo. Cuando tengas el tensiómetro a la mano vuelve con /vitales.",
            reply_markup=remove_keyboard(),
        )
        return ConversationHandler.END
    if not is_affirmative(answer):
        await _reply(update, "Respóndeme Sí o No, por favor.", reply_markup=yes_no_keyboard())
        return CONFIRM_TENSIOMETER
    await _reply(
        update,
        "Perfecto. ¿Cuál es tu presión arterial? Escríbela así: 120/80",
        reply_markup=remove_keyboard(),
    )
    return BLOOD_PRESSURE


async def blood_pressure_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        systolic, diastolic = parse_blood_pressure(_message_text(update))
    except ValueError as exc:
        await _reply(update, str(exc))
        return BLOOD_PRESSURE
    draft = _draft(context)
    draft["systolic_bp"] = systolic
    draft["diastolic_bp"] = diastolic
    await _reply(update, "¿Cuál es tu frecuencia cardíaca o pulso? Ejemplo: 75")
    return HEART_RATE


async def heart_rate_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        _draft(context)["heart_rate"] = parse_required_number(
            _message_text(update),
            label="frecuencia cardíaca",
            minimum=25,
            maximum=220,
        )
    except ValueError as exc:
        await _reply(update, str(exc))
        return HEART_RATE
    await _reply(update, "¿Tienes oxímetro? Si lo tienes, dime tu saturación. Ejemplo: 97. Si no, escribe 'no medí'.")
    return OXYGEN


async def oxygen_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        value = parse_optional_number(
            _message_text(update),
            label="saturación de oxígeno",
            minimum=1,
            maximum=100,
        )
    except ValueError as exc:
        await _reply(update, str(exc))
        return OXYGEN
    if value is not None:
        _draft(context)["oxygen_saturation"] = value
    next_question = "¿Cómo está tu glucosa hoy? Si no la tienes, escribe 'no medí'."
    if value is not None and float(value) < 88:
        await _reply(
            update,
            "Gracias por decírmelo. Esa saturación está en rango de alarma. "
            "Si el oxímetro marcó bien o tienes ahogo, labios morados, dolor en el pecho, "
            "confusión o mucho decaimiento, llama al 123 o ve a urgencias ahora.\n\n"
            f"{next_question}",
        )
        return GLUCOSE
    await _reply(update, next_question)
    return GLUCOSE


async def glucose_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        value = parse_optional_number(_message_text(update), label="glucosa", minimum=20, maximum=600)
    except ValueError as exc:
        await _reply(update, str(exc))
        return GLUCOSE
    if value is not None:
        _draft(context)["glucose"] = value
    await _reply(update, "En una escala de 0 a 10, ¿tienes dolor en este momento?")
    return PAIN


async def pain_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        _draft(context)["pain_score"] = parse_score(_message_text(update), label="dolor")
    except ValueError as exc:
        await _reply(update, str(exc))
        return PAIN
    await _reply(update, "¿Tienes mareos o sensación de inestabilidad? Responde de 0 a 10.")
    return DIZZINESS


async def dizziness_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        _draft(context)["dizziness_score"] = parse_score(_message_text(update), label="mareo")
    except ValueError as exc:
        await _reply(update, str(exc))
        return DIZZINESS
    await _reply(update, "¿Sientes dificultad para respirar? Responde de 0 a 10.")
    return DYSPNEA


async def dyspnea_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        _draft(context)["dyspnea_score"] = parse_score(_message_text(update), label="dificultad para respirar")
    except ValueError as exc:
        await _reply(update, str(exc))
        return DYSPNEA

    deps = _deps(context)
    profile = await ensure_linked_patient(update, context, deps)
    if not profile:
        return ConversationHandler.END
    draft = dict(_draft(context))
    await _reply(update, "¡Listo! Estoy analizando tus datos...")
    state = await process_vital_report(
        patient_id=str(profile["id"]),
        raw_message=build_raw_message_from_draft(draft),
        vital_signs=draft,
        dependencies=deps,
    )
    context.user_data.pop("vitals_draft", None)
    await _reply(update, state.get("final_response", "Recibí tus datos, pero no pude construir la respuesta final."))
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("vitals_draft", None)
    await _reply(update, "Registro cancelado. Puedes iniciar de nuevo con /vitales.", reply_markup=remove_keyboard())
    return ConversationHandler.END


async def document_or_free_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deps = _deps(context)
    if context.user_data.get("awaiting_document"):
        await link_document_message(update, context, deps)
        return
    text = _message_text(update)
    profile = await _linked_profile(update, context, deps)
    if not profile and looks_like_document_id(text):
        context.user_data["awaiting_document"] = True
        await link_document_message(update, context, deps)
        return
    if profile and looks_like_vital_report(text):
        await _reply(update, "Recibí tus signos. Estoy analizándolos...")
        state = await process_vital_report(
            patient_id=str(profile["id"]),
            raw_message=text,
            vital_signs={},
            dependencies=deps,
        )
        await _reply(update, state.get("final_response", "Recibí tus datos."))
        return
    latest_prediction = None
    recent_vitals: list[dict[str, Any]] = []
    if profile and wants_status_context(text):
        latest_prediction = await deps.repository.get_latest_risk_prediction(str(profile["id"]))
    if profile and wants_history_context(text):
        recent_vitals = await deps.repository.get_recent_vital_signs(str(profile["id"]), limit=5)
    await _reply(update, build_carmen_free_text_response(text, profile, latest_prediction, recent_vitals))


async def link_document_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dependencies: BotDependencies,
) -> None:
    chat_id = _chat_id(update)
    document_id = _message_text(update).strip()
    profile = await dependencies.repository.link_telegram_account(document_id, chat_id)
    if not profile:
        await _reply(
            update,
            "No encontré una cuenta con ese documento. Revisa el número o pide apoyo a tu IPS para registrar tu perfil.",
        )
        return
    context.user_data["awaiting_document"] = False
    _cache_profile(context, profile)
    await _reply(
        update,
        f"Listo, {profile.get('full_name', '')}. Tu Telegram quedó vinculado.\n\n"
        "Para registrar signos vitales usa /vitales.",
    )


async def process_vital_report(
    *,
    patient_id: str,
    raw_message: str,
    vital_signs: dict[str, Any],
    dependencies: BotDependencies,
) -> dict[str, Any]:
    return await dependencies.nurse_agent.process_vital_report(
        {
            "patient_id": patient_id,
            "raw_message": raw_message,
            "vital_signs": vital_signs,
            "source": "telegram",
        }
    )


async def ensure_linked_patient(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dependencies: BotDependencies,
) -> dict[str, Any] | None:
    profile = await _linked_profile(update, context, dependencies)
    if profile and profile.get("role") == "patient":
        return profile
    if profile:
        await _reply(update, "Tu cuenta está vinculada, pero este flujo está habilitado para pacientes.")
        return None
    context.user_data["awaiting_document"] = True
    await _reply(update, "Primero necesito vincular tu cuenta. Envíame tu número de documento de identidad.")
    return None


def help_message() -> str:
    return (
        "Comandos HomecareCCV:\n"
        "/start - vincular tu cuenta de Telegram\n"
        "/vitales - registrar signos vitales paso a paso\n"
        "/registro - iniciar el mismo registro guiado\n"
        "/estado - ver tu último nivel de riesgo\n"
        "/historial - ver tus últimas 5 mediciones\n"
        "/emergencia - avisar de inmediato al equipo de salud\n"
        "/ayuda - ver esta lista"
    )


def format_latest_status_message(prediction: dict[str, Any] | None) -> str:
    if not prediction:
        return "Aún no tengo predicciones registradas para tu cuenta. Puedes reportar signos con /vitales."
    risk_level = normalize_risk_level(prediction.get("risk_level"))
    risk = RISK_LEVELS[risk_level]
    probability = float(prediction.get("risk_probability") or 0)
    model = prediction.get("model_used") or "modelo clínico"
    predicted_at = prediction.get("predicted_at") or "fecha no disponible"
    return (
        f"Tu último nivel de riesgo es {risk['label']} ({probability:.0%}).\n"
        f"Modelo: {model}\n"
        f"Fecha: {predicted_at}\n\n"
        f"{risk['description']}"
    )


def format_vital_history_message(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Aún no tengo mediciones registradas. Puedes empezar con /vitales."
    lines = ["Tus últimas mediciones:"]
    for index, row in enumerate(rows, start=1):
        pressure = _format_pressure(row)
        heart_rate = row.get("heart_rate", "sin pulso")
        oxygen = row.get("oxygen_saturation")
        glucose = row.get("glucose")
        extras = []
        if oxygen is not None:
            extras.append(f"SpO2 {oxygen}")
        if glucose is not None:
            extras.append(f"glucosa {glucose}")
        suffix = f", {', '.join(extras)}" if extras else ""
        lines.append(f"{index}. {row.get('recorded_at', 'sin fecha')}: PA {pressure}, FC {heart_rate}{suffix}")
    return "\n".join(lines)


def build_raw_message_from_draft(draft: dict[str, Any]) -> str:
    parts = [
        f"Presión {draft.get('systolic_bp')}/{draft.get('diastolic_bp')}",
        f"pulso {draft.get('heart_rate')}",
    ]
    optional_labels = {
        "oxygen_saturation": "saturación",
        "glucose": "glucosa",
        "pain_score": "dolor",
        "dizziness_score": "mareo",
        "dyspnea_score": "dificultad para respirar",
    }
    for field, label in optional_labels.items():
        if field in draft:
            parts.append(f"{label} {draft[field]}")
    return ", ".join(parts)


def looks_like_vital_report(text: str) -> bool:
    parsed = parse_vital_signs_message(text)
    return bool(parsed) and (
        "systolic_bp" in parsed
        or any(keyword in text.lower() for keyword in ("presion", "presión", "pulso", "saturación", "glucosa"))
    )


def looks_like_document_id(text: str) -> bool:
    compact = text.strip().replace(".", "").replace("-", "").replace(" ", "")
    return compact.isdigit() and 5 <= len(compact) <= 15


def wants_status_context(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(
        phrase in normalized
        for phrase in (
            "como estoy",
            "como voy",
            "mi estado",
            "estado",
            "riesgo",
            "nivel",
            "resultado",
            "ultima prediccion",
            "ultima medicion",
        )
    )


def wants_history_context(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(phrase in normalized for phrase in ("historial", "ultimas", "mediciones", "registros anteriores"))


def build_carmen_free_text_response(
    text: str,
    profile: dict[str, Any] | None = None,
    latest_prediction: dict[str, Any] | None = None,
    recent_vitals: list[dict[str, Any]] | None = None,
) -> str:
    normalized = _normalize_text(text)
    first_name = _first_name(profile)
    emergency_lead = f"{first_name}, te leo." if first_name else "Te leo."

    if _mentions_emergency(normalized):
        return (
            f"{emergency_lead} Si esto está pasando ahora mismo, no esperes mi respuesta: "
            "llama al 123 o ve a urgencias, especialmente si hay dolor fuerte en el pecho, "
            "dificultad para respirar, desmayo, confusión, debilidad en un lado del cuerpo "
            "o problemas para hablar.\n\n"
            "Si puedes hacerlo sin retrasar la atención, usa /emergencia para avisar también a tu equipo de salud."
        )

    if _contains_any(normalized, ("eres carmen", "sos carmen", "quien eres", "quien sos", "como te llamas")):
        account_note = (
            " Ya tengo tu cuenta vinculada, así que puedo mirar tu historial cuando lo necesites."
            if profile
            else " Para mirar tu historial real, primero necesito vincular tu cuenta con /start."
        )
        return (
            f"Sí{', ' + first_name if first_name else ''}, soy Carmen, la enfermera virtual de HomecareCCV. "
            "Estoy aquí para acompañarte con el monitoreo en casa, ayudarte a registrar signos vitales "
            "y explicarte las alertas en palabras claras. No reemplazo a tu médico, pero sí puedo ayudarte "
            f"a ordenar la información y avisar cuando algo requiere atención.{account_note}"
        )

    if profile is None:
        return (
            "Hola, soy Carmen, la enfermera virtual de HomecareCCV. "
            "Para cuidar tus datos y acompañarte con tu historial real, primero necesito vincular tu cuenta. "
            "Envíame tu número de documento o usa /start y lo hacemos juntos."
        )

    if recent_vitals:
        return (
            f"Claro, {first_name}. Esto es lo último que tengo registrado:\n\n"
            f"{format_vital_history_message(recent_vitals)}\n\n"
            "Si quieres, también podemos actualizar tus datos de hoy."
        )

    if wants_status_context(text):
        if latest_prediction:
            return (
                f"Claro, {first_name}. Te cuento lo último que tengo:\n\n"
                f"{format_latest_status_message(latest_prediction)}\n\n"
                "Si algo cambió en cómo te sientes, cuéntamelo o registra nuevos signos."
            )
        return (
            f"{first_name}, todavía no tengo una predicción reciente para tu cuenta. "
            "Si tienes tus signos a la mano, me los puedes escribir en una frase, por ejemplo: "
            "presión 120/80, pulso 75, saturación 97, glucosa 110. También puedo guiarte paso a paso con /vitales."
        )

    if _is_greeting(normalized):
        return (
            f"Hola, {first_name}. Soy Carmen. Me alegra leerte.\n\n"
            "Cuéntame cómo te sientes hoy o mándame tus signos vitales si ya los tienes. "
            "Si prefieres que te acompañe paso a paso, empezamos con /vitales."
        )

    if _contains_any(normalized, ("gracias", "muchas gracias", "mil gracias")):
        return (
            f"Con gusto, {first_name}. Aquí estoy para acompañarte. "
            "Cuando quieras revisar tus signos, tu estado o registrar una nueva medición, me escribes."
        )

    if _contains_any(normalized, ("que puedes hacer", "que haces", "ayudame", "ayuda", "comandos")):
        return (
            f"Puedo ayudarte con varias cosas, {first_name}: registrar signos vitales, revisar tu último riesgo, "
            "mostrar mediciones recientes y activar una alerta si te sientes en emergencia.\n\n"
            "También puedes hablarme en lenguaje natural. Por ejemplo: "
            "\"me siento mareado\" o \"presión 130/85, pulso 78\"."
        )

    return (
        f"Te leo, {first_name}. Puedo conversar contigo sobre cómo te sientes y ayudarte a registrar tus signos, "
        "pero no debo diagnosticar ni cambiar tratamientos.\n\n"
        "Si tienes una medición, escríbemela en una frase: presión 120/80, pulso 75, saturación 97. "
        "Si lo que tienes es un síntoma, cuéntamelo con tus palabras."
    )


async def _linked_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dependencies: BotDependencies,
) -> dict[str, Any] | None:
    cached = context.user_data.get("profile")
    if cached:
        return cached
    profile = await _profile_by_chat(dependencies.repository, _chat_id(update))
    if profile:
        _cache_profile(context, profile)
    return profile


async def _profile_by_chat(repository: HomecareRepository, chat_id: int) -> dict[str, Any] | None:
    if chat_id is None:
        return None
    return await repository.find_profile_by_telegram_chat_id(chat_id)


async def _alert_recipients(repository: HomecareRepository, patient_id: str) -> dict[str, Any]:
    if hasattr(repository, "get_alert_recipients"):
        return await repository.get_alert_recipients(patient_id)
    return {}


def _cache_profile(context: ContextTypes.DEFAULT_TYPE, profile: dict[str, Any]) -> None:
    context.user_data["profile"] = profile
    context.user_data["patient_id"] = profile.get("id")


def _deps(context: ContextTypes.DEFAULT_TYPE) -> BotDependencies:
    dependencies = context.application.bot_data.get("homecare_dependencies")
    if dependencies is None:
        dependencies = default_dependencies()
        context.application.bot_data["homecare_dependencies"] = dependencies
    return dependencies


def _draft(context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any]:
    return context.user_data.setdefault("vitals_draft", {})


async def _reply(update: Update, text: str, **kwargs: Any) -> None:
    if update.effective_message is not None:
        await update.effective_message.reply_text(text, **kwargs)


def _message_text(update: Update) -> str:
    if update.effective_message and update.effective_message.text:
        return update.effective_message.text.strip()
    return ""


def _chat_id(update: Update) -> int:
    if update.effective_chat is None:
        raise ValueError("Telegram update without chat.")
    return int(update.effective_chat.id)


def _first_name(profile: dict[str, Any] | None) -> str:
    if not profile:
        return ""
    full_name = str(profile.get("full_name") or "").strip()
    return full_name.split()[0] if full_name else ""


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.strip().lower())
    return "".join(character for character in normalized if unicodedata.category(character) != "Mn")


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _is_greeting(text: str) -> bool:
    return text in {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hey", "holi"}


def _mentions_emergency(text: str) -> bool:
    emergency_phrases = (
        "dolor en el pecho",
        "pecho apretado",
        "no puedo respirar",
        "me ahogo",
        "ahogo",
        "desmayo",
        "me desmaye",
        "confusion",
        "cara torcida",
        "no puedo hablar",
        "hablo raro",
        "debilidad en un lado",
        "se me durmio un lado",
        "convulsion",
        "labios morados",
    )
    return _contains_any(text, emergency_phrases)


def _format_pressure(row: dict[str, Any]) -> str:
    systolic = row.get("systolic_bp")
    diastolic = row.get("diastolic_bp")
    if systolic is None or diastolic is None:
        return "sin presión"
    return f"{systolic}/{diastolic}"
