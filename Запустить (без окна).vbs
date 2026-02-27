' Тихий запуск бота без окна консоли.
' Создай ярлык на этот файл и помести на рабочий стол.

Dim WshShell, ScriptDir
Set WshShell = CreateObject("WScript.Shell")

' Определяем папку скрипта
ScriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Запускаем docker-compose в фоне (0 = скрытое окно)
WshShell.Run "cmd /c cd /d """ & ScriptDir & """ && docker-compose up -d --build > """ & ScriptDir & "launcher.log"" 2>&1", 0, True

' Ждём 3 сек и показываем всплывающее уведомление
WScript.Sleep 3000

Dim result
result = WshShell.Run("cmd /c docker ps --filter name=accounting-bot_bot --format ""{{.Status}}""", 0, True)

WshShell.Popup "Бот-Бухгалтер запущен!" & Chr(13) & Chr(10) & "Mini App: http://localhost:8000", 4, "Бухгалтерия ИП", 64
