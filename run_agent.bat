@echo off
echo [INFO] Iniciando Ruviaro Agent (Z-API Mode)...
python ruviaro_agent/src/webhook_server.py
if %errorlevel% neq 0 (
    echo [ERRO] O agente parou com erro. Verifique se as dependencias estao instaladas (rode install_deps.bat).
    pause
    exit /b %errorlevel%
)
pause
