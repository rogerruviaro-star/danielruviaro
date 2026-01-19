@echo off
set VPS_IP=76.13.70.207
set VPS_USER=root
set REMOTE_PATH=/var/www/ruviaro-agent

echo ==============================================
echo      IMPORTADOR DE ESTOQUE - DANIEL
echo ==============================================
echo.

if "%~1"=="" (
    echo ARRASTE E SOLTE O ARQUIVO .CSV EM CIMA DESTE SCRIPT!
    echo.
    echo Exemplo:
    echo 1. Pegue seu arquivo 'estoque.csv'
    echo 2. Arraste ele com o mouse para cima do icone 'import_stock.bat'
    echo.
    pause
    exit
)

echo [1/3] Enviando arquivo %~nx1 para o servidor...
scp "%~1" %VPS_USER%@%VPS_IP%:%REMOTE_PATH%/import_data.csv

echo.
echo [2/3] Processando importacao no servidor...
ssh %VPS_USER%@%VPS_IP% "cd %REMOTE_PATH% && python3 ruviaro_agent/src/importer.py import_data.csv"

echo.
echo [3/3] Reiniciando Daniel para pegar dados novos...
ssh %VPS_USER%@%VPS_IP% "pm2 restart ruviaro-agent"

echo.
echo ==============================================
echo ESTOQUE ATUALIZADO COM SUCESSO!
echo ==============================================
pause
