@echo off
echo ========================================
echo  RECONFIGURANDO NGROK PARA PORTA 5000
echo ========================================
echo.
echo [INFO] O servidor Flask roda na porta 5000
echo [INFO] O ngrok precisa redirecionar para localhost:5000
echo.
echo [1] Fechando ngrok anterior...
taskkill /F /IM ngrok.exe 2>nul
timeout /t 2 >nul
echo.
echo [2] Iniciando ngrok na porta 5000...
start "Ngrok Tunnel" ngrok http 5000
echo.
echo [AGUARDE] O ngrok vai abrir em uma nova janela...
timeout /t 5 >nul
echo.
echo [3] Abrindo interface do ngrok para copiar o URL...
start http://127.0.0.1:4040
echo.
echo ========================================
echo  PROXIMOS PASSOS:
echo ========================================
echo.
echo 1. Copie o URL do ngrok (ex: https://xxxxx.ngrok-free.dev)
echo 2. Acesse: https://api.z-api.io/instances/
echo 3. Va em "Webhooks e configuracoes gerais"
echo 4. Cole o URL com /webhook no final
echo    Exemplo: https://xxxxx.ngrok-free.dev/webhook
echo 5. Salve a configuracao
echo 6. Execute: run_agent.bat
echo.
pause
