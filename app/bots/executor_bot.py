# app/bots/executor_bot.py
import io

import httpx
from telegram import File as TgFile
from telegram import InlineKeyboardButton as Btn
from telegram import InlineKeyboardMarkup as Mk
from telegram import Update, WebAppInfo
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, ContextTypes)

from app.services.bot_auth import activate_user, cb_disagree, cb_executor_done, cb_executor_help
from app.settings import settings

# ─── пути к документам ─────────────────────────────────────────────────────
# BASE = Path(__file__).resolve().parent.parent
# EXECUTOR_OFFER = BASE / "resources" / "offer.docx"
# CLIENT_TERMS = BASE / "resources" / "client_terms.odt"
# CLIENT_PRIVACY = BASE / "resources" / "client_privacy.odt"

# ─── клавиатуры ────────────────────────────────────────────────────────────
# после отправки документов — выбор
DECISION_KB = Mk([[
    Btn("✅ Согласен",    callback_data="agree"),
    Btn("❌ Не согласен", callback_data="disagree"),
]])

# главное меню исполнителя после активации
KB_EXECUTOR = Mk([
    [
        Btn("🆘 Тех-поддержка", web_app=WebAppInfo(url=f"{settings.webapp_url}/executor/support")),
        Btn("📦 Назначенные заказы", web_app=WebAppInfo(url=f"{settings.webapp_url}/executor/orders")),
    ],
    [
        Btn("📬 Доступные заказы", web_app=WebAppInfo(url=f"{settings.webapp_url}/executor/orders-new")),
        Btn("👤 Профиль", web_app=WebAppInfo(url=f"{settings.webapp_url}/executor/profile")),
    ],
    # Расскоментить когда появятся оплаты
    # [
    #     Btn("💬 Чаты", web_app=WebAppInfo(url=f"{settings.webapp_url}/executor/chats/")),
    #     Btn("💳 Оплата", web_app=WebAppInfo(url=f"{settings.webapp_url}/executor/payments/")),
    # ],
    # [
    #     Btn("ℹ️ Инструкция", callback_data="executor_help"),
    # ]
    [
        Btn("💬 Чаты", web_app=WebAppInfo(url=f"{settings.webapp_url}/executor/chats/")),
        Btn("ℹ️ Инструкция", callback_data="executor_help"),
    ],
])


def build() -> ApplicationBuilder:
    bot = ApplicationBuilder().token(settings.tg_token_executor).build()

    async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """
        1) POST /auth/tg/ — проверяем, есть ли исполнитель
        2) при 200 → сразу меню KB_EXECUTOR
        3) при 400 → POST /auth/signup/ с promo + is_active=False, потом шлём три документа и DECISION_KB
        """
        uid = update.effective_user.id
        ctx.user_data["role"] = "executor"

        # промо-код из /start <code>
        parts = update.message.text.split(maxsplit=1)
        promo = parts[1] if len(parts) > 1 else None

        async with httpx.AsyncClient(base_url=str(settings.backend_url)) as client:
            # 1) пробуем авторизацию
            r = await client.post(
                "/auth/tg/",
                json={"telegram_id": uid, "auth_type": 2},
                timeout=5.0,
            )

            if r.status_code == 200:
                # исполнитель уже зарегистрирован и активирован
                await update.message.reply_text("Добро пожаловать 👌", reply_markup=KB_EXECUTOR)
                return

            if r.status_code != 400:
                # какая-то другая ошибка
                await update.message.reply_text("❌ Ошибка сервиса, повторите /start позже.")
                return

            # 2) 400 → надо зарегистрировать
            payload = {
                "telegram_id": uid,
                "auth_type": 2,
                "marketing_code": promo,
                "is_active": False,
            }
            # дополняем поля из Telegram
            for fld in ("first_name", "last_name"):
                val = getattr(update.effective_user, fld, None)
                if val:
                    payload[fld] = val
            # и далее, если заранее собрали birth_date/phone/email в ctx.user_data
            for fld in ("birth_date", "phone", "email"):
                if fld in ctx.user_data:
                    payload[fld] = ctx.user_data[fld]

            # Пытаемся получить фото
            photo_bytes = None
            try:
                photos = await ctx.bot.get_user_profile_photos(uid, limit=1)
                if photos.total_count > 0:
                    photo = photos.photos[0][-1]  # самое большое изображение
                    file: TgFile = await ctx.bot.get_file(photo.file_id)
                    file_data = await file.download_as_bytearray()
                    photo_bytes = io.BytesIO(file_data)
                    photo_bytes.name = "avatar.jpg"
            except Exception:
                pass

            files = {"avatar": ("avatar.jpg", photo_bytes, "image/jpeg")} if photo_bytes else None

            await client.post("/auth/signup/", data=payload, files=files, timeout=10.0)

        # 3) новый исполнитель — шлём все три документа
        # media = [
        #     InputMediaDocument(open(CLIENT_TERMS,   "rb"), filename="Пользовательское соглашение.odt"),
        #     InputMediaDocument(open(CLIENT_PRIVACY, "rb"), filename="Политика конфиденциальности.odt"),
        #     InputMediaDocument(open(EXECUTOR_OFFER, "rb"), filename="Публичная оферта.docx"),
        # ]
        # await update.message.reply_media_group(media)
        msg = (
            "Пожалуйста, ознакомьтесь с документами:\n\n"
            "📄 <a href='https://xn----ctbefqt5agebvc.xn--p1ai/user-agreement.html'>Публичная оферта</a>\n\n"
            "📄 <a href='https://xn----ctbefqt5agebvc.xn--p1ai/privacy-policy.html'>Политика конфиденциальности</a>\n\n"
            "📄 <a href='https://xn----ctbefqt5agebvc.xn--p1ai/public-offer.html'>Пользовательское соглашение</a>\n\n"
            "И выберите:"
        )
        await update.message.reply_text(msg, reply_markup=DECISION_KB, parse_mode="HTML")

    bot.add_handler(CommandHandler("start", cmd_start))
    bot.add_handler(CallbackQueryHandler(activate_user, pattern="^agree$"))
    bot.add_handler(CallbackQueryHandler(cb_disagree,    pattern="^disagree$"))
    bot.add_handler(CallbackQueryHandler(cb_executor_help,    pattern="^executor_help$"))
    bot.add_handler(CallbackQueryHandler(cb_executor_done, pattern="^executor_done$"))
    return bot
