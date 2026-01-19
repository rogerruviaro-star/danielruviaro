@echo off
echo Buscando logs de erro do servidor...
ssh root@76.13.70.207 "pm2 logs ruviaro-agent --lines 50 --err"
pause
