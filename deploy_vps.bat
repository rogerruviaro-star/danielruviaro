@echo off
echo ==============================================
echo   ATUALIZANDO VPS (PULL FROM GITHUB)
echo ==============================================

echo [1/2] Conectando no VPS e puxando codigo novo...
ssh root@76.13.70.207 "cd /var/www/ruviaro-agent && git pull origin main"

echo.
echo [2/2] Reiniciando o Daniel...
ssh root@76.13.70.207 "pm2 restart ruviaro-agent"

echo.
echo ==============================================
echo   DANIEL ATUALIZADO COM SUCESSO!
echo ==============================================
pause
