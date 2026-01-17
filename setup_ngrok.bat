@echo off
echo [INFO] Configurando Ngrok...
ngrok config add-authtoken 375h0cxN0IF40br92CqoE7NK41L_4Xnokp597au7Kd7D7pr5u
if %errorlevel% neq 0 (
    echo [ERRO] Nao foi possivel configurar o Ngrok. Verifique se ele esta instalado.
    echo Tente reiniciar o terminal se acabou de instalar.
    pause
    exit /b %errorlevel%
)
echo [SUCESSO] Ngrok autenticado!
echo Agora voce pode rodar: ngrok http 5000
pause
