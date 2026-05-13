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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Константы типов операций ──────────────────────────────────────────────────

class TxType:
    ZAKUP            = "zakup"
    STORONNIE        = "storonnie"
    PRIHOD_MES       = "prihod_mes"
    PRIHOD_FAST      = "prihod_fast"
    PRIHOD_STO       = "prihod_sto"
    SNYAT_RS         = "snyat_rs"
    SNYAT_DEBIT      = "snyat_debit"
    VNESTI_RS        = "vnesti_rs"
    ODOLZHIT         = "odolzhit"
    POGASIT          = "pogasit"
    EXPENSE_WRITEOFF = "expense_writeoff"


INCOME_TYPES: frozenset[str] = frozenset({
    TxType.PRIHOD_MES,
    TxType.PRIHOD_FAST,
    TxType.PRIHOD_STO,
})
EXPENSE_TYPES: frozenset[str] = frozenset({
    TxType.ZAKUP,
    TxType.STORONNIE,
})

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

# Лимиты тарифных планов
PLAN_LIMITS: dict[str, dict] = {
    "free":     {"ips": 1,  "members": 2,   "label": "Free",     "stars": 0},
    "pro":      {"ips": 5,  "members": 10,  "label": "Pro ⭐",   "stars": 199},
    "business": {"ips": 99, "members": 999, "label": "Business 💎", "stars": 499},
}


# ── Базовый класс ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Рабочие пространства (воркспейсы) ─────────────────────────────────────────

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Telegram ID владельца
    plan: Mapped[str] = mapped_column(String(20), default="free")
    sub_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members: Mapped[list["User"]] = relationship(back_populates="workspace", foreign_keys="User.workspace_id")
    ips: Mapped[list["IP"]] = relationship(back_populates="workspace")

    @property
    def plan_label(self) -> str:
        return PLAN_LIMITS.get(self.plan, {}).get("label", self.plan)

    @property
    def is_sub_active(self) -> bool:
        from datetime import timezone
        if self.plan == "free":
            return True
        if self.sub_end is None:
            return False
        now = datetime.now(timezone.utc)
        end = self.sub_end
        if end.tzinfo is None:
            from datetime import timezone as tz
            end = end.replace(tzinfo=tz.utc)
        return end > now


# ── Пользователи ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="junior")
    cash_balance: Mapped[int] = mapped_column(Integer, default=0)
    workspace_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
    workspace: Mapped["Workspace | None"] = relationship(back_populates="members", foreign_keys=[workspace_id])

    @property
    def display_name(self) -> str:
        return f"@{self.username}" if self.username else f"ID:{self.id}"


# ── Индивидуальные предприниматели ────────────────────────────────────────────

class IP(Base):
    __tablename__ = "ips"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_ip_workspace_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    workspace_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=True)
    bank_balance: Mapped[int] = mapped_column(Integer, default=0)
    debit_balance: Mapped[int] = mapped_column(Integer, default=0)
    cash_balance: Mapped[int] = mapped_column(Integer, default=0)
    initial_capital: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="ip")
    workspace: Mapped["Workspace | None"] = relationship(back_populates="ips")


# ── Транзакции ────────────────────────────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    ip_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ips.id"), nullable=True)
    workspace_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expense_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("expenses.id"), nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_by_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions")
    ip: Mapped["IP | None"] = relationship(back_populates="transactions")


# ── Расходы ───────────────────────────────────────────────────────────────────

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text)
    amount: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    workspace_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()


# ── Долги между ИП ────────────────────────────────────────────────────────────

class IpDebt(Base):
    __tablename__ = "ip_debts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creditor_ip_id: Mapped[int] = mapped_column(Integer, ForeignKey("ips.id"))
    debtor_ip_id: Mapped[int] = mapped_column(Integer, ForeignKey("ips.id"))
    workspace_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    creditor_ip: Mapped["IP"] = relationship(foreign_keys=[creditor_ip_id])
    debtor_ip: Mapped["IP"] = relationship(foreign_keys=[debtor_ip_id])
