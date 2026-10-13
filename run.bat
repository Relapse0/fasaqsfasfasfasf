@echo off
REM Запуск бота: использует Python 3.12 (из окружения DSH) и зависимости из deps/
cd /d "%~dp0"
set PYTHONPATH=%CD%\deps
"C:\Users\ggarb\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" -m main
pause
