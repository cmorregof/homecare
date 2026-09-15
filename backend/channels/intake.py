"""Intake guiado de signos vitales, independiente del canal.

Es el mismo protocolo de once campos que corre en Telegram (`bot/handlers.py`), escrito
como máquina de estados pura: recibe (paso, borrador, texto del paciente) y devuelve
(respuestas, siguiente paso). Hoy lo usa el canal WhatsApp; Telegram conserva su
ConversationHandler intacto hasta que se migre sobre este motor.

Reglas de la casa que se conservan tal cual:
- Los validadores deterministas (`bot/validators.py`) tienen la última palabra sobre
  rangos y formato.
- La voz LLM solo redacta la pregunta y normaliza respuestas libres; nunca decide.
- Los avisos de seguridad (FR alta, SpO2 baja) son deterministas y no pasan por el LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from bot.handlers import RESPIRATORY_QUESTION
from bot.i18n import t
from bot.validators import (
    is_affirmative,
    is_negative,
    parse_blood_pressure,
    parse_optional_number,
    parse_required_number,
    parse_score,
)
from channels.messages import Outbound


CONFIRM_TENSIOMETER = "confirm_tensiometer"
RESPIRATORY_RATE = "respiratory_rate"
HEART_RATE = "heart_rate"
OXYGEN = "oxygen"
BLOOD_PRESSURE = "blood_pressure"
TEMPERATURE = "temperature"
WEIGHT = "weight"
GLUCOSE = "glucose"
PAIN = "pain"
DIZZINESS = "dizziness"
DYSPNEA = "dyspnea"

STEPS: tuple[str, ...] = (
    CONFIRM_TENSIOMETER,
    RESPIRATORY_RATE,
    HEART_RATE,
    OXYGEN,
    BLOOD_PRESSURE,
    TEMPERATURE,
    WEIGHT,
    GLUCOSE,
    PAIN,
    DIZZINESS,
    DYSPNEA,
)

_YES_NO_BUTTONS = {
    "es": (("yes", "Sí"), ("no", "No")),
    "en": (("yes", "Yes"), ("no", "No")),
}


def yes_no_buttons(language: str) -> tuple[tuple[str, str], ...]:
    return _YES_NO_BUTTONS.get(language, _YES_NO_BUTTONS["es"])


@dataclass
class IntakeContext:
    """Lo que el motor necesita saber del paciente y del canal."""

    language: str = "es"
    first_name: str = ""
    voice: Any | None = None


@dataclass
class IntakeResult:
    replies: list[Outbound] = field(default_factory=list)
    next_step: str | None = None
    completed: bool = False  # el borrador quedó completo y listo para el pipeline
    aborted: bool = False  # el paciente no tiene el tensiómetro: se descarta el borrador


async def speak(
    ctx: IntakeContext,
    draft: str,
    *,
    step: str,
    issue: str | None = None,
) -> str:
    """Igual que `_speak` en Telegram: la voz reformula el borrador; sin voz, va literal."""
    if ctx.voice is None:
        return draft
    return await ctx.voice(
        "pregunta_de_intake",
        {
            "idioma": ctx.language,
            "paso": step,
            "problema_con_respuesta_anterior": issue,
            "instruccion": (
                "Reformula el borrador como UNA pregunta corta y natural en tu voz, "
                "variando la redacción. Conserva intactos: las instrucciones de "
                "medición, los números y rangos, los formatos de ejemplo (como 120/80 "
                "o el conteo de 30 segundos) y la opción 'no medí' cuando aparezca."
            ),
        },
        draft,
    )


async def parse_tolerant(
    ctx: IntakeContext,
    parser: Callable[[str], Any],
    raw: str,
    field_label: str,
    expected_format: str,
) -> Any:
    """Validador determinista primero; si falla, el LLM normaliza la respuesta libre y el
    validador vuelve a tener la última palabra."""
    try:
        return parser(raw)
    except ValueError:
        if ctx.voice is None:
            raise
        from agents.nurse_voice import extract_intake_answer

        extracted = await extract_intake_answer(field_label, expected_format, raw)
        if extracted is None:
            raise
        return parser(extracted)


async def start_intake(ctx: IntakeContext) -> IntakeResult:
    greeting = f"Hola {ctx.first_name}." if ctx.first_name else "Hola."
    text = await speak(
        ctx,
        f"{greeting} Vamos a registrar tus signos vitales.\n¿Tienes tu tensiómetro a la mano?",
        step="saludo_y_tensiometro",
    )
    return IntakeResult(
        replies=[Outbound(text, yes_no_buttons(ctx.language))],
        next_step=CONFIRM_TENSIOMETER,
    )


async def advance_intake(
    ctx: IntakeContext,
    step: str,
    draft: dict[str, Any],
    text: str,
) -> IntakeResult:
    handler = _STEP_HANDLERS.get(step)
    if handler is None:
        raise ValueError(f"Paso de intake desconocido: {step}")
    return await handler(ctx, draft, text.strip())


async def _ask(ctx: IntakeContext, draft_text: str, *, step_name: str, next_step: str) -> IntakeResult:
    text = await speak(ctx, draft_text, step=step_name)
    return IntakeResult(replies=[Outbound(text)], next_step=next_step)


async def _retry(
    ctx: IntakeContext,
    exc: Exception,
    raw: str,
    *,
    step_name: str,
    current_step: str,
    buttons: tuple[tuple[str, str], ...] = (),
) -> IntakeResult:
    text = await speak(ctx, str(exc), step=step_name, issue=f"El paciente respondió: {raw}")
    return IntakeResult(replies=[Outbound(text, buttons)], next_step=current_step)


async def _confirm_tensiometer(ctx: IntakeContext, draft: dict[str, Any], answer: str) -> IntakeResult:
    decided: str | None = None
    if is_affirmative(answer):
        decided = "SI"
    elif is_negative(answer):
        decided = "NO"
    elif ctx.voice is not None:
        from agents.nurse_voice import extract_intake_answer

        interpreted = await extract_intake_answer("¿tiene el tensiómetro a la mano?", "SI o NO", answer)
        if interpreted:
            candidate = interpreted.strip().upper().replace("Í", "I")
            if candidate in {"SI", "NO"}:
                decided = candidate
    if decided == "NO":
        text = await speak(
            ctx,
            "De acuerdo. Cuando tengas el tensiómetro a la mano vuelve con /vitales.",
            step="despedida_sin_tensiometro",
        )
        return IntakeResult(replies=[Outbound(text)], next_step=None, aborted=True)
    if decided != "SI":
        return await _retry(
            ctx,
            ValueError("Respóndeme Sí o No, por favor."),
            answer,
            step_name="tensiometro_reintento",
            current_step=CONFIRM_TENSIOMETER,
            buttons=yes_no_buttons(ctx.language),
        )
    return await _ask(ctx, RESPIRATORY_QUESTION, step_name="frecuencia_respiratoria", next_step=RESPIRATORY_RATE)


async def _respiratory_rate(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        count_30s = await parse_tolerant(
            ctx,
            lambda value: parse_optional_number(
                value, label="respiraciones en 30 segundos", minimum=3, maximum=25
            ),
            raw,
            "respiraciones contadas en 30 segundos",
            "un número entero entre 3 y 25, o 'no medí'",
        )
    except ValueError as exc:
        return await _retry(
            ctx,
            ValueError(f"{exc} Recuerda: es el conteo de 30 segundos, normalmente entre 5 y 15."),
            raw,
            step_name="frecuencia_respiratoria_reintento",
            current_step=RESPIRATORY_RATE,
        )
    next_question = t(ctx.language, "question_pulse")
    if count_30s is not None:
        per_minute = int(count_30s * 2)
        draft["respiratory_rate"] = per_minute
        if per_minute < 8 or per_minute > 28:
            # Aviso de seguridad determinista: nunca pasa por el LLM.
            warning = t(
                ctx.language,
                "respiratory_high_warning",
                per_minute=per_minute,
                next_question=next_question,
            )
            return IntakeResult(replies=[Outbound(warning)], next_step=HEART_RATE)
        return await _ask(
            ctx,
            f"Anotado: {per_minute} respiraciones por minuto.\n\n{next_question}",
            step_name="pulso",
            next_step=HEART_RATE,
        )
    return await _ask(ctx, next_question, step_name="pulso", next_step=HEART_RATE)


async def _heart_rate(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        draft["heart_rate"] = await parse_tolerant(
            ctx,
            lambda value: parse_required_number(
                value, label="frecuencia cardíaca", minimum=25, maximum=220
            ),
            raw,
            "pulso (frecuencia cardíaca)",
            "un número entero como 75",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="pulso_reintento", current_step=HEART_RATE)
    return await _ask(
        ctx,
        "Sin quitarte el oxímetro, dime tu saturación de oxígeno. Ejemplo: 97. "
        "Si no tienes oxímetro, escribe 'no medí'.",
        step_name="saturacion",
        next_step=OXYGEN,
    )


async def _oxygen(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        value = await parse_tolerant(
            ctx,
            lambda text: parse_optional_number(
                text, label="saturación de oxígeno", minimum=1, maximum=100
            ),
            raw,
            "saturación de oxígeno (SpO2)",
            "un número entero como 97, o 'no medí'",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="saturacion_reintento", current_step=OXYGEN)
    if value is not None:
        draft["oxygen_saturation"] = value
    next_question = t(ctx.language, "question_pressure")
    if value is not None and float(value) < 88:
        # Aviso de seguridad determinista: nunca pasa por el LLM.
        warning = t(ctx.language, "oxygen_low_warning", next_question=next_question)
        return IntakeResult(replies=[Outbound(warning)], next_step=BLOOD_PRESSURE)
    return await _ask(ctx, next_question, step_name="presion_arterial", next_step=BLOOD_PRESSURE)


async def _blood_pressure(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        systolic, diastolic = await parse_tolerant(
            ctx, parse_blood_pressure, raw, "presión arterial", "dos números como 120/80"
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="presion_reintento", current_step=BLOOD_PRESSURE)
    draft["systolic_bp"] = systolic
    draft["diastolic_bp"] = diastolic
    return await _ask(
        ctx,
        "¿Cuál es tu temperatura en grados? Ejemplo: 36.8. Si no la mediste, escribe 'no medí'.",
        step_name="temperatura",
        next_step=TEMPERATURE,
    )


async def _temperature(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        value = await parse_tolerant(
            ctx,
            lambda text: parse_optional_number(text, label="temperatura", minimum=34, maximum=42),
            raw,
            "temperatura corporal en grados",
            "un número como 36.8, o 'no medí'",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="temperatura_reintento", current_step=TEMPERATURE)
    if value is not None:
        draft["temperature"] = value
    return await _ask(
        ctx,
        "¿Cuál es tu peso de hoy en kilos? Ejemplo: 68.5. "
        "El peso se toma una vez al día, en la mañana; si ya lo reportaste hoy o no te has pesado, "
        "escribe 'no medí'.",
        step_name="peso",
        next_step=WEIGHT,
    )


async def _weight(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        value = await parse_tolerant(
            ctx,
            lambda text: parse_optional_number(text, label="peso", minimum=25, maximum=300),
            raw,
            "peso corporal en kilos",
            "un número como 68.5, o 'no medí'",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="peso_reintento", current_step=WEIGHT)
    if value is not None:
        draft["weight_kg"] = value
    return await _ask(
        ctx,
        "¿Cómo está tu glucosa hoy? Si no la tienes, escribe 'no medí'.",
        step_name="glucosa",
        next_step=GLUCOSE,
    )


async def _glucose(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        value = await parse_tolerant(
            ctx,
            lambda text: parse_optional_number(text, label="glucosa", minimum=20, maximum=600),
            raw,
            "glucosa en sangre",
            "un número como 110, o 'no medí'",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="glucosa_reintento", current_step=GLUCOSE)
    if value is not None:
        draft["glucose"] = value
    return await _ask(
        ctx,
        "En una escala de 0 a 10, ¿tienes dolor en este momento?",
        step_name="dolor",
        next_step=PAIN,
    )


async def _pain(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        draft["pain_score"] = await parse_tolerant(
            ctx,
            lambda text: parse_score(text, label="dolor"),
            raw,
            "dolor en escala de 0 a 10",
            "un número entero de 0 a 10",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="dolor_reintento", current_step=PAIN)
    return await _ask(
        ctx,
        "¿Tienes mareos o sensación de inestabilidad? Responde de 0 a 10.",
        step_name="mareo",
        next_step=DIZZINESS,
    )


async def _dizziness(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        draft["dizziness_score"] = await parse_tolerant(
            ctx,
            lambda text: parse_score(text, label="mareo"),
            raw,
            "mareo en escala de 0 a 10",
            "un número entero de 0 a 10",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="mareo_reintento", current_step=DIZZINESS)
    return await _ask(
        ctx,
        "¿Sientes dificultad para respirar? Responde de 0 a 10.",
        step_name="disnea",
        next_step=DYSPNEA,
    )


async def _dyspnea(ctx: IntakeContext, draft: dict[str, Any], raw: str) -> IntakeResult:
    try:
        draft["dyspnea_score"] = await parse_tolerant(
            ctx,
            lambda text: parse_score(text, label="dificultad para respirar"),
            raw,
            "dificultad para respirar en escala de 0 a 10",
            "un número entero de 0 a 10",
        )
    except ValueError as exc:
        return await _retry(ctx, exc, raw, step_name="disnea_reintento", current_step=DYSPNEA)
    return IntakeResult(replies=[], next_step=None, completed=True)


StepHandler = Callable[[IntakeContext, dict[str, Any], str], Awaitable[IntakeResult]]

_STEP_HANDLERS: dict[str, StepHandler] = {
    CONFIRM_TENSIOMETER: _confirm_tensiometer,
    RESPIRATORY_RATE: _respiratory_rate,
    HEART_RATE: _heart_rate,
    OXYGEN: _oxygen,
    BLOOD_PRESSURE: _blood_pressure,
    TEMPERATURE: _temperature,
    WEIGHT: _weight,
    GLUCOSE: _glucose,
    PAIN: _pain,
    DIZZINESS: _dizziness,
    DYSPNEA: _dyspnea,
}
