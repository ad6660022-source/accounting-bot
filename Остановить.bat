@echo off
title Accounting Bot - Stop

cd /d "%~dp0"
echo Stopping bot...
docker-compose down
echo.
echo Bot stopped.
pause
