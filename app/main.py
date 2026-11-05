import json

from fastapi import (APIRouter, Body, Depends, FastAPI, Header, HTTPException,
                     Request)
from pydantic import BaseModel, Field

from app.settings import settings
from app import bots

app = FastAPI(title="Alert Manager Service")

router = APIRouter()


def check_api_token(x_api_key: str = Header()):
    if x_api_key != settings.AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    
async def send_message(message):
    application = bots.client_app
    try:
        await application.bot.send_message(
            settings.TARGET_CHAT_ID,
            message,
            parse_mode=None,
            reply_markup=None
        )
    except Exception as e:
        print(f"simple_alert send Exception: {str(e)}")
    

# Модель данных для принятия payload-а
class SimpleAlertPayload(BaseModel):
    message: str


# ---------- webhook endpoint ----------
@app.post("/tg/callback/", status_code=204)
async def tg_callback(
    request: Request,
    update: dict = Body(...),
):
    print('--- Детали входящего запроса Telegram Webhook ---')
    print(f'Путь (Path): /tg/callback/')
    print(f'Метод (Method): {request.method}')

    # Выводим все заголовки запроса
    print('\nЗаголовки (Headers):')
    for header_name, header_value in request.headers.items():
        print(f'  {header_name}: {header_value}')

    # Выводим тело запроса (payload)
    print('\nТело запроса (Body - "update" payload):')
    # Используем json.dumps для форматированного вывода словаря update
    print(json.dumps(update, indent=4, ensure_ascii=False))
    return {}


@app.post("/live/", status_code=200)
async def tg_callback(
    request: Request,
):
    print("OK")
    return {"status": "OK"}


@app.post(
        "/alerts/metabase/",
        dependencies=[Depends(check_api_token)],
        status_code=200
)
async def metabase_alert(
    request: Request,
):
    # Выводим тело запроса (payload)
    metabase_raw_data = await request.body()
    metabase_raw_data = metabase_raw_data.decode()
    print("metabase_raw_data:", str(metabase_raw_data))
    if not metabase_raw_data:
        return {"status": "OK"}
    metabase_data = json.loads(metabase_raw_data)
    question_name = metabase_data.get("data", {}).get("question_name")
    col_names = metabase_data.get("data", {}).get("raw_data", {}).get("cols", [])
    data_rows = metabase_data.get("data", {}).get("raw_data", {}).get("rows", [])
    message_lines = [question_name]
    for row in data_rows:
        message_lines.append(str({col_names[i]:x for i, x in enumerate(row)}))
    message = "\n".join(message_lines)
    print(f"Metabase message: {message}")
    await send_message(message)
    return {"status": "OK"}


@app.post(
    "/alerts/backup/",
    dependencies=[Depends(check_api_token)],
    status_code=200,
    openapi_extra={
        "requestBody": {
            "required": False,
            "content": {
                "application/json": {
                    "schema": {"type": "object"},
                    "example": {
                        "database": "qrm_db",
                        "task_id": 12,
                        "operation_id": 345,
                        "status": "error",
                        "dump_path": "/dumps/qrm_db.sql.gz",
                        "error": "pg_dump failed",
                    },
                }
            },
        }
    },
)
async def backup_alert(
    request: Request,
):
    backup_raw_data = await request.body()
    backup_raw_data = backup_raw_data.decode()
    print("backup_raw_data:", backup_raw_data)
    if not backup_raw_data:
        return {"status": "OK"}

    backup_data = json.loads(backup_raw_data)

    database = backup_data.get("database")
    task_id = backup_data.get("task_id")
    operation_id = backup_data.get("operation_id")
    status = backup_data.get("status")
    dump_path = backup_data.get("dump_path")
    error = backup_data.get("error")

    if status == "success":
        message_lines = [
            f"✅ Дамп БД «{database}» создан успешно",
            f"Операция: #{operation_id} (задача #{task_id})",
        ]
        if dump_path:
            message_lines.append(f"Файл: {dump_path}")
    else:
        message_lines = [
            f"❌ Дамп БД «{database}» завершился с ошибкой",
            f"Операция: #{operation_id} (задача #{task_id})",
            f"Ошибка: {(error or 'неизвестная ошибка')[:1000]}",
        ]

    message = "\n".join(message_lines)
    print(f"Backup message: {message}")
    await send_message(message)
    return {"status": "OK"}


@app.post(
        "/alerts/simple/",
        dependencies=[Depends(check_api_token)],
        status_code=200
)
async def simple_alert(
    payload: SimpleAlertPayload,

):
    print(f"Received Message: {payload.message}")
    await send_message(payload.message)
    return {"status": "OK"}


# ---------- startup: выставляем web-hookи ----------
@app.on_event("startup")
async def startup():
    try:
        # достаточно initialize(); start() не нужен при webhook-режиме
        await bots.client_app.initialize()

        # # 2. сбрасываем старый веб-хук, чтобы Telegram «забыл» прежний secret
        await bots.client_app.bot.delete_webhook(drop_pending_updates=True)

        await bots.client_app.bot.set_webhook(
            f"{settings.webhook_base}/tg/callback/",
            secret_token=settings.bot_secret,
        )
    except Exception as e:
        print(f"startup error: {str(e)}")
