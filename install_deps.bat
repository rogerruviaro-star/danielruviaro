@echo off
echo [INFO] Instalando dependencias do projeto...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Nao foi possivel rodar o pip. Verifique se o Python esta instalado e adicionado ao PATH.
    pause
    exit /b %errorlevel%
)
echo [SUCESSO] Dependencias instaladas!
pause
