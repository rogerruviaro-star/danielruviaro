@echo off
echo [INFO] Iniciando o tunel Ngrok na porta 5000...
ngrok http 5000
if %errorlevel% neq 0 (
    echo [ERRO] O comando ngrok falhou.
    echo Tente fechar e abrir esta janela para atualizar o PATH do Windows.
    echo Ou verifique se a instalacao terminou corretamente.
    pause
    exit /b %errorlevel%
)
pause
