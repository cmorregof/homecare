from __future__ import annotations

from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application

from bot.handlers import BotDependencies, register_handlers
from config import settings
from db.repository import HomecareRepository


_APPLICATION: Application | None = None


def build_application(
    *,
    token: str | None = None,
    dependencies: BotDependencies | None = None,
    repository: HomecareRepository | None = None,
) -> Application:
    bot_token = token or settings.telegram_bot_token
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required to start the Telegram bot.")
    if dependencies is None and repository is not None:
        from agents.nurse_agent import NurseAgent

        dependencies = BotDependencies(repository=repository, nurse_agent=NurseAgent(repository=repository))
    application = Application.builder().token(bot_token).build()
    register_handlers(application, dependencies=dependencies)
    return application


def get_application() -> Application:
    global _APPLICATION
    if _APPLICATION is None:
        _APPLICATION = build_application()
    return _APPLICATION


async def process_webhook_update(update_payload: dict[str, Any], application: Application | None = None) -> None:
    app = application or get_application()
    if not app.bot_data.get("homecare_initialized"):
        await app.initialize()
        app.bot_data["homecare_initialized"] = True
    update = Update.de_json(update_payload, app.bot)
    await app.process_update(update)


async def configure_webhook(application: Application | None = None, webhook_url: str | None = None) -> bool:
    app = application or get_application()
    url = webhook_url or settings.telegram_webhook_url
    if not url:
        return False
    if not app.bot_data.get("homecare_initialized"):
        await app.initialize()
        app.bot_data["homecare_initialized"] = True
    return bool(await app.bot.set_webhook(url=url))


def configure_reminders(
    application: Application,
    *,
    repository: HomecareRepository | None = None,
    scheduler: AsyncIOScheduler | None = None,
    interval_hours: int | None = None,
) -> AsyncIOScheduler:
    reminder_scheduler = scheduler or AsyncIOScheduler(timezone="America/Bogota")
    reminder_scheduler.add_job(
        send_monitoring_reminders,
        trigger="interval",
        hours=interval_hours or settings.monitoring_interval_hours,
        args=[application, repository or HomecareRepository()],
        id="homecareccv_vital_reminders",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    return reminder_scheduler


async def send_monitoring_reminders(
    application: Application,
    repository: HomecareRepository | None = None,
) -> int:
    repo = repository or HomecareRepository()
    patients = await repo.get_monitoring_patients()
    sent = 0
    for patient in patients:
        chat_id = patient.get("telegram_chat_id")
        if not chat_id:
            continue
        await application.bot.send_message(
            chat_id=int(chat_id),
            text=(
                f"Hola {patient.get('full_name') or ''}. Es hora de registrar tus signos vitales.\n"
                "Usa /vitales para iniciar el reporte guiado."
            ),
        )
        sent += 1
    return sent


def run_polling() -> None:
    application = get_application()
    scheduler = configure_reminders(application)
    scheduler.start()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_polling()
