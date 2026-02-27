"""
FastAPI-приложение для Mini App.
Раздаёт REST API (/api/...) и статические файлы фронтенда (/).
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import admin, balance, debts, me, operations, reports, users

logger = logging.getLogger(__name__)

app = FastAPI(title="Accounting Bot API", docs_url="/api/docs")

# CORS — разрешаем Telegram-домены и localhost для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры API
app.include_router(me.router, prefix="/api", tags=["me"])
app.include_router(balance.router, prefix="/api", tags=["balance"])
app.include_router(operations.router, prefix="/api", tags=["operations"])
app.include_router(debts.router, prefix="/api", tags=["debts"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Раздача статических файлов фронтенда (монтируем ПОСЛЕ всех API-роутеров)
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
    logger.info("Фронтенд раздаётся из: %s", _static_dir)
else:
    logger.warning("Папка static/ не найдена — фронтенд недоступен (запусти npm run build)")
