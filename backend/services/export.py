"""
Генерация Excel-выгрузки истории операций по ИП.
"""

from __future__ import annotations

import io
from datetime import date, datetime
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from backend.database.models import TX_LABELS, TxType


# Группы операций для отдельных листов
_INCOME_TYPES = {TxType.PRIHOD_MES, TxType.PRIHOD_FAST, TxType.PRIHOD_STO}
_EXPENSE_TYPES = {TxType.ZAKUP, TxType.STORONNIE}
_DEBT_TYPES = {TxType.ODOLZHIT, TxType.POGASIT}
_TRANSFER_TYPES = {TxType.SNYAT_RS, TxType.SNYAT_DEBIT, TxType.VNESTI_RS}

# Цвета шапки
_HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
_HEADER_FONT = Font(color="FFFFFF", bold=True)

# Цвета строк
_GREEN_FILL = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
_RED_FILL = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")


def _get_delta(tx) -> tuple[int, int, int]:
    """Возвращает (delta_cash, delta_bank, delta_debit) для транзакции."""
    t = tx.type
    a = tx.amount
    dest = tx.destination or "cash"

    if t in (TxType.ZAKUP, TxType.STORONNIE):
        return (-a, 0, 0)
    elif t in _INCOME_TYPES:
        if dest == "bank":
            return (0, a, 0)
        elif dest == "debit":
            return (0, 0, a)
        else:
            return (a, 0, 0)
    elif t == TxType.SNYAT_RS:
        return (a, -a, 0)
    elif t == TxType.SNYAT_DEBIT:
        return (a, 0, -a)
    elif t == TxType.VNESTI_RS:
        return (-a, a, 0)
    elif t in (TxType.ODOLZHIT, TxType.POGASIT):
        return (-a, 0, 0)
    return (0, 0, 0)


def _compute_rows(ip, all_transactions_asc: list) -> list[tuple]:
    """
    Вычисляет running balance для каждой транзакции.
    Начинает от текущих балансов ИП и идёт назад.
    Возвращает список (tx, bal_cash_after, bal_bank_after, bal_debit_after, dc, db, dd).
    """
    cash = ip.cash_balance
    bank = ip.bank_balance
    debit = ip.debit_balance

    rows = []
    for tx in reversed(all_transactions_asc):
        dc, db, dd = _get_delta(tx)
        rows.append((tx, cash, bank, debit, dc, db, dd))
        cash -= dc
        bank -= db
        debit -= dd

    rows.reverse()
    return rows


def _style_header(ws, headers: list[str]):
    """Записывает шапку с форматированием."""
    ws.append(headers)
    for cell in ws[1]:
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def _set_column_widths(ws, widths: list[int]):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _fmt_amount(v: int) -> str:
    if v == 0:
        return ""
    sign = "+" if v > 0 else ""
    return f"{sign}{v:,}".replace(",", " ")


def _add_rows_to_sheet(ws, rows: list[tuple], type_filter: Optional[set] = None):
    """Добавляет строки данных в лист."""
    headers = [
        "Дата", "Время", "ИП", "Тип операции", "Кто провёл", "Комментарий",
        "Изм. Нал", "Изм. Р/С", "Изм. Дебет",
        "Баланс Нал", "Баланс Р/С", "Баланс Дебет",
    ]
    _style_header(ws, headers)
    _set_column_widths(ws, [12, 8, 18, 22, 18, 24, 12, 12, 12, 14, 14, 14])

    row_num = 2
    for tx, bal_cash, bal_bank, bal_debit, dc, db, dd in rows:
        if type_filter is not None and tx.type not in type_filter:
            continue

        dt: datetime = tx.created_at
        ip_name = tx.ip.name if tx.ip else ""
        user_name = tx.user.display_name if tx.user else ""
        type_label = TX_LABELS.get(tx.type, tx.type)

        row_data = [
            dt.strftime("%d.%m.%Y"),
            dt.strftime("%H:%M"),
            ip_name,
            type_label,
            user_name,
            tx.comment or "",
            _fmt_amount(dc),
            _fmt_amount(db),
            _fmt_amount(dd),
            f"{bal_cash:,}".replace(",", " "),
            f"{bal_bank:,}".replace(",", " "),
            f"{bal_debit:,}".replace(",", " "),
        ]
        ws.append(row_data)

        # Цветовая подсветка строк
        total_delta = dc + db + dd
        fill = _GREEN_FILL if total_delta > 0 else (_RED_FILL if total_delta < 0 else None)
        if fill:
            for col in range(1, 13):
                ws.cell(row=row_num, column=col).fill = fill

        row_num += 1

    # Выравнивание числовых колонок по правому краю
    for r in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=7, max_col=12):
        for cell in r:
            cell.alignment = Alignment(horizontal="right")


def generate_excel(
    ip,
    all_transactions: list,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> bytes:
    """
    Генерирует Excel-файл с 5 листами по операциям ИП.
    all_transactions — ВСЕ транзакции ИП (отсортированные по created_at ASC) для вычисления running balance.
    date_from/date_to — фильтр дат для отображения строк (но running balance считается по всем).
    """
    # Сортируем от старого к новому для вычисления балансов
    sorted_txs = sorted(all_transactions, key=lambda t: t.created_at)

    # Вычисляем running balance для каждой транзакции
    all_rows = _compute_rows(ip, sorted_txs)

    # Применяем фильтр по датам
    def in_range(tx) -> bool:
        d = tx.created_at.date()
        if date_from and d < date_from:
            return False
        if date_to and d > date_to:
            return False
        return True

    filtered_rows = [(tx, c, b, d, dc, db, dd) for (tx, c, b, d, dc, db, dd) in all_rows if in_range(tx)]

    wb = Workbook()

    # Лист 1 — Все операции
    ws1 = wb.active
    ws1.title = "Все операции"
    _add_rows_to_sheet(ws1, filtered_rows)

    # Лист 2 — Приходы
    ws2 = wb.create_sheet("Приходы")
    _add_rows_to_sheet(ws2, filtered_rows, _INCOME_TYPES)

    # Лист 3 — Закупы
    ws3 = wb.create_sheet("Закупы")
    _add_rows_to_sheet(ws3, filtered_rows, _EXPENSE_TYPES)

    # Лист 4 — Займы
    ws4 = wb.create_sheet("Займы")
    _add_rows_to_sheet(ws4, filtered_rows, _DEBT_TYPES)

    # Лист 5 — Переводы
    ws5 = wb.create_sheet("Переводы")
    _add_rows_to_sheet(ws5, filtered_rows, _TRANSFER_TYPES)

    # Заморозить первую строку на всех листах
    for ws in [ws1, ws2, ws3, ws4, ws5]:
        ws.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
