"""
FSM-состояния для всех диалоговых потоков бота.
"""

from aiogram.fsm.state import State, StatesGroup


class OperationStates(StatesGroup):
    """Поток ввода финансовой операции."""
    choosing_type    = State()  # выбор типа операции
    choosing_ip      = State()  # выбор ИП
    choosing_user    = State()  # выбор пользователя (для «одолжить»)
    entering_amount  = State()  # ввод суммы
    entering_comment = State()  # ввод комментария (для некоторых типов)
    confirming       = State()  # подтверждение перед проведением


class RepayStates(StatesGroup):
    """Поток погашения долга."""
    choosing_debt    = State()  # выбор долга
    entering_amount  = State()  # ввод суммы погашения
    confirming       = State()


class AdminStates(StatesGroup):
    """Поток создания/управления ИП."""
    entering_ip_name    = State()  # ввод имени нового ИП
    entering_ip_capital = State()  # ввод начального капитала
