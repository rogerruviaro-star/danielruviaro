@echo off
REM Script de Deploy para Windows (PowerShell/SCP)
echo =========================================
echo   DEPLOY RUVIARO AGENT - VPS HOSTINGER
echo =========================================
echo.

set VPS_IP=76.13.70.207
set VPS_USER=root
set PROJECT_DIR=/var/www/ruviaro-agent

echo [1/8] Criando diretorio no VPS...
ssh %VPS_USER%@%VPS_IP% "mkdir -p %PROJECT_DIR%"

echo.
echo [2/8] Upload dos arquivos (isso pode demorar)...
scp -r ruviaro_agent %VPS_USER%@%VPS_IP%:%PROJECT_DIR%/
scp requirements.txt %VPS_USER%@%VPS_IP%:%PROJECT_DIR%/
scp .env %VPS_USER%@%VPS_IP%:%PROJECT_DIR%/

echo.
echo [3/8] Instalando dependencias Python...
ssh %VPS_USER%@%VPS_IP% "cd %PROJECT_DIR% && pip3 install -r requirements.txt"

echo.
echo [4/8] Instalando PM2...
ssh %VPS_USER%@%VPS_IP% "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs && npm install -g pm2"

echo.
echo [5/8] Iniciando servidor com PM2...
ssh %VPS_USER%@%VPS_IP% "cd %PROJECT_DIR% && pm2 delete ruviaro-agent 2>nul || exit 0 && pm2 start 'python3 ruviaro_agent/src/webhook_server.py' --name ruviaro-agent && pm2 save"

echo.
echo [6/8] Configurando PM2 para iniciar no boot...
ssh %VPS_USER%@%VPS_IP% "pm2 startup && pm2 save"

echo.
echo [7/8] Abrindo porta 5000 no firewall...
ssh %VPS_USER%@%VPS_IP% "ufw allow 5000/tcp"

echo.
echo [8/8] Verificando status...
ssh %VPS_USER%@%VPS_IP% "pm2 status"

echo.
echo =========================================
echo   DEPLOY CONCLUIDO!
echo =========================================
echo.
echo Webhook URL: http://76.13.70.207:5000/webhook
echo.
echo Configure este URL na Z-API!
echo.
pause
