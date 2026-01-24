from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import hmac, os
import hashlib
from urllib.parse import parse_qs, unquote
from typing import Optional, Dict, Any

router_test = APIRouter()

# Замени на свой реальный токен (лучше брать из env!)
BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
    )


class TelegramInitData(
    BaseModel
    ):
    initData: str = Field(
        ...,
        description="Telegram.WebApp.initData строка",
        examples=[
            "query_id=AAHdF6wAADhdF6wAfZ3&user=...&auth_date=1737331200&hash=abcdef123..."
        ]
    )


def validate_and_parse_init_data(init_data_str: str) -> Optional[Dict[str, Any]]:
    """
    Валидация + парсинг initData по официальному алгоритму Telegram (HMAC-SHA256)
    Возвращает распарсенные данные или None при ошибке
    """
    if not init_data_str:
        return None

    # 1. Парсим как query string
    parsed = parse_qs(
        init_data_str
        )

    # Получаем hash
    received_hash = parsed.pop(
        "hash",
        [None]
        )[0]
    if not received_hash:
        return None

    # Собираем data-check-string (все ключи кроме hash, отсортированные)
    data_check_pairs = []
    for key in sorted(
            parsed.keys()
            ):
        value = parsed[key][0]  # берём первое значение (Telegram всегда одно)
        # Важно: user и другие объекты уже в URL-encoded виде → не нужно доп. quote
        data_check_pairs.append(
            f"{key}={value}"
            )

    data_check_string = "\n".join(
        data_check_pairs
        )

    # 2. Секретный ключ = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(
            "utf-8"
            ),
        hashlib.sha256
    ).digest()

    # 3. Вычисляем HMAC от data_check_string
    computed_hmac = hmac.new(
        secret_key,
        data_check_string.encode(
            "utf-8"
            ),
        hashlib.sha256
    ).hexdigest()

    # 4. Сравниваем
    if computed_hmac != received_hash:
        return None

    # 5. Дополнительно: проверка свежести (опционально, но очень рекомендуется!)
    auth_date_str = parsed.get(
        "auth_date",
        [None]
        )[0]
    if auth_date_str:
        try:
            auth_date = int(
                auth_date_str
                )
            # Например, не старше 1 дня (86400 секунд)
            from time import time
            if time() - auth_date > 86400:
                return None
        except ValueError:
            return None

    # 6. Парсим полезные данные (user обычно JSON-строка)
    result = {}
    for k, v in parsed.items():
        val = v[0]
        if val.startswith(
                "{"
                ) or val.startswith(
                "["
                ):
            try:
                import json
                result[k] = json.loads(
                    unquote(
                        val
                        )
                    )
            except:
                result[k] = val
        else:
            result[k] = unquote(
                val
                )

    return result


@router_test.post(
    "/tg/auth"
    )
async def tg_auth(data: TelegramInitData):
    user_data = validate_and_parse_init_data(
        data.initData
        )

    if not user_data or "user" not in user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Telegram initData"
        )

    user = user_data["user"]

    first_name = (user.get(
        "first_name"
        ) or "").strip()
    last_name = (user.get(
        "last_name"
        ) or "").strip()
    full_name = (first_name + " " + last_name).strip() or "friend"

    # Здесь можешь добавить создание/поиск пользователя в БД и т.д.

    return {
        "ok": True,
        "full_name": full_name,
        # Полезно возвращать ещё что-нибудь
        "telegram_id": user.get(
            "id"
            ),
        "username": user.get(
            "username"
            ),
        "is_premium": user.get(
            "is_premium",
            False
            ),
    }