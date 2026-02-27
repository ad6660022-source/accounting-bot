"""
Валидация Telegram Web App initData.
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs, unquote_plus


def validate_init_data(init_data: str, bot_token: str) -> dict:
    """
    Проверяет подпись initData от Telegram и возвращает словарь с данными пользователя.
    Бросает ValueError при невалидных данных.
    """
    if not init_data:
        raise ValueError("Пустой initData")

    # Парсим строку вида key=value&key2=value2...
    parsed = parse_qs(init_data, keep_blank_values=True)
    params = {k: v[0] for k, v in parsed.items()}

    hash_val = params.pop("hash", None)
    if not hash_val:
        raise ValueError("Отсутствует hash")

    # Строим data-check-string: отсортированные пары key=value через \n
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

    # HMAC-SHA256: ключ = HMAC("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, hash_val):
        raise ValueError("Неверная подпись initData")

    # Проверяем свежесть данных (не старше 24 часов)
    auth_date = int(params.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise ValueError("initData устарел")

    # Декодируем JSON с данными пользователя
    user_raw = unquote_plus(params.get("user", "{}"))
    return json.loads(user_raw)
