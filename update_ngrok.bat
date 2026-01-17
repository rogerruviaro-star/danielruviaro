@echo off
echo [INFO] Atualizando o Ngrok para a versao mais recente...
ngrok update
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao atualizar o Ngrok automaticamente.
    echo Tente baixar a versao mais recente direto do site ngrok.com/download
    pause
    exit /b %errorlevel%
)
echo [SUCESSO] Ngrok atualizado!
echo Agora tente rodar o run_ngrok.bat novamente.
pause
