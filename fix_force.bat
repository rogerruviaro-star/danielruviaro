@echo off
echo ==============================================
echo   CORRECAO FORCADA - RUVIARO AGENT
echo ==============================================

echo [1/4] Atualizando Codigo e .env...
scp .env root@76.13.70.207:/var/www/ruviaro-agent/
scp -r ruviaro_agent/src/*.py root@76.13.70.207:/var/www/ruviaro-agent/ruviaro_agent/src/

echo.
echo [2/4] Reinstalando TODAS as dependencias...
ssh root@76.13.70.207 "cd /var/www/ruviaro-agent && pip3 install openai flask requests python-dotenv gunicorn --break-system-packages"

echo.
echo [3/4] Reiniciando o Robo...
ssh root@76.13.70.207 "pm2 restart ruviaro-agent --update-env"

echo.
echo [4/4] Mostrando ultimos erros (se houver)...
echo.
ssh root@76.13.70.207 "pm2 logs ruviaro-agent --lines 30 --err"

echo.
echo ==============================================
echo AGORA TEM QUE IR!
echo Se aparecer texto vermelho acima, me mande.
echo ==============================================
pause
