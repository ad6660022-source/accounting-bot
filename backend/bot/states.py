"""FSM-состояния для всех диалоговых потоков бота."""

from aiogram.fsm.state import State, StatesGroup


class OperationStates(StatesGroup):
    choosing_type    = State()
    choosing_ip      = State()
    choosing_user    = State()
    entering_amount  = State()
    entering_comment = State()
    confirming       = State()


class RepayStates(StatesGroup):
    choosing_debt    = State()
    entering_amount  = State()
    confirming       = State()


class AdminStates(StatesGroup):
    entering_ip_name    = State()
    entering_ip_capital = State()


class WorkspaceStates(StatesGroup):
    entering_name        = State()  # создание воркспейса — ввод названия
    entering_invite_code = State()  # присоединение — ввод кода
