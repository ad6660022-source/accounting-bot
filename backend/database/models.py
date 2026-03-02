"""
SQLAlchemy ORM-модели для базы данных бота-бухгалтера.
Все суммы хранятся в целых рублях (INTEGER).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Константы типов операций ──────────────────────────────────────────────────

class TxType:
    ZAKUP            = "zakup"            # Закуп (нал ИП → -)
    STORONNIE        = "storonnie"        # Посторонние траты (нал ИП → -)
    PRIHOD_MES       = "prihod_mes"       # Приход ежемесячный (+ нал ИП)
    PRIHOD_FAST      = "prihod_fast"      # Приход быстрый (+ нал ИП)
    PRIHOD_STO       = "prihod_sto"       # Приход сторонний (+ нал ИП)
    SNYAT_RS         = "snyat_rs"         # Снять с Р/С → дебет ИП
    SNYAT_DEBIT      = "snyat_debit"      # Снять с дебета → наличные ИП
    VNESTI_RS        = "vnesti_rs"        # Внести на Р/С ← наличные ИП
    ODOLZHIT         = "odolzhit"         # Одолжить (нал ИП → нал другого ИП)
    POGASIT          = "pogasit"          # Погашение долга между ИП
    EXPENSE_WRITEOFF = "expense_writeoff" # Расход (списание с ИП)


# Группы типов для отчётов
INCOME_TYPES: frozenset[str] = frozenset({
    TxType.PRIHOD_MES,
    TxType.PRIHOD_FAST,
    TxType.PRIHOD_STO,
})
EXPENSE_TYPES: frozenset[str] = frozenset({
    TxType.ZAKUP,
    TxType.STORONNIE,
})

# Человекочитаемые названия операций
TX_LABELS: dict[str, str] = {
    TxType.ZAKUP:            "🛒 Закуп",
    TxType.STORONNIE:        "💸 Посторонние траты",
    TxType.PRIHOD_MES:       "📥 Приход ежемесячный",
    TxType.PRIHOD_FAST:      "⚡ Приход быстрый",
    TxType.PRIHOD_STO:       "🏦 Приход сторонний",
    TxType.SNYAT_RS:         "💴 Снять с Р/С → Дебет",
    TxType.SNYAT_DEBIT:      "💵 Снять с Дебета → Нал",
    TxType.VNESTI_RS:        "🏛 Внести на Р/С",
    TxType.ODOLZHIT:         "🤝 Одолжить",
    TxType.POGASIT:          "✅ Погашение долга",
    TxType.EXPENSE_WRITEOFF: "💰 Расход (списание)",
}


# ── Базовый класс ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Пользователи ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="junior")  # admin / user / junior
    cash_balance: Mapped[int] = mapped_column(Integer, default=0)  # личные наличные (для долгов)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")

    @property
    def display_name(self) -> str:
        return f"@{self.username}" if self.username else f"ID:{self.id}"


# ── Индивидуальные предприниматели ────────────────────────────────────────────

class IP(Base):
    __tablename__ = "ips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    bank_balance: Mapped[int] = mapped_column(Integer, default=0)   # расчётный счёт
    debit_balance: Mapped[int] = mapped_column(Integer, default=0)  # дебет (промежуточный)
    cash_balance: Mapped[int] = mapped_column(Integer, default=0)   # наличные ИП
    initial_capital: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="ip")


# ── Транзакции ────────────────────────────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    ip_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ips.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(20), nullable=True)  # cash / bank / debit (для приходов)
    expense_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("expenses.id"), nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_by_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions")
    ip: Mapped["IP | None"] = relationship(back_populates="transactions")


# ── Расходы (журнал расходов) ─────────────────────────────────────────────────

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text)
    amount: Mapped[int] = mapped_column(Integer)  # заявленная сумма (информационно)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()


# ── Долги между ИП ────────────────────────────────────────────────────────────

class IpDebt(Base):
    __tablename__ = "ip_debts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creditor_ip_id: Mapped[int] = mapped_column(Integer, ForeignKey("ips.id"))
    debtor_ip_id: Mapped[int] = mapped_column(Integer, ForeignKey("ips.id"))
    amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    creditor_ip: Mapped["IP"] = relationship(foreign_keys=[creditor_ip_id])
    debtor_ip: Mapped["IP"] = relationship(foreign_keys=[debtor_ip_id])
