from telegram import Update
from telegram.ext import (ApplicationBuilder,
                          CommandHandler, ContextTypes)
from telegram.request import HTTPXRequest

from app.settings import settings


def build() -> ApplicationBuilder:
    builder = ApplicationBuilder().token(settings.tg_token_client)
    if settings.TELEGRAM_PROXY:
        builder = (
            builder
            .request(HTTPXRequest(proxy=settings.TELEGRAM_PROXY))
            .get_updates_request(HTTPXRequest(proxy=settings.TELEGRAM_PROXY))
        )

    bot = builder.build()

    async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        pass

    bot.add_handler(CommandHandler("start", cmd_start))
    return bot
