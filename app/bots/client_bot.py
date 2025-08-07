from telegram import Update
from telegram.ext import (ApplicationBuilder,
                          CommandHandler, ContextTypes)

from app.settings import settings


def build() -> ApplicationBuilder:
    bot = ApplicationBuilder().token(settings.tg_token_client).build()

    async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        pass

    bot.add_handler(CommandHandler("start", cmd_start))
    return bot
