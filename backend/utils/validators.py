"""
Валидация данных, вводимых пользователем.
"""


def validate_amount(text: str) -> int:
    """
    Парсит и валидирует введённую сумму.
    Принимает целые числа (рубли без копеек).
    Возвращает int или бросает ValueError с понятным сообщением.
    """
    text = text.strip().replace(" ", "").replace(",", "").replace("₽", "")
    if not text.isdigit():
        raise ValueError("❌ Введите целое число (например: 5000)")
    amount = int(text)
    if amount <= 0:
        raise ValueError("❌ Сумма должна быть больше нуля")
    if amount > 100_000_000:
        raise ValueError("❌ Слишком большая сумма (максимум 100 млн ₽)")
    return amount


def format_money(amount: int) -> str:
    """Форматирует число в читаемую строку: 12500 → '12 500 ₽'"""
    return f"{amount:,} ₽".replace(",", "\u202f")  # неразрывный пробел
