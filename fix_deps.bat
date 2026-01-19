@echo off
echo Instalando OpenAI no servidor...
ssh root@76.13.70.207 "pip3 install openai && pm2 restart ruviaro-agent"
echo.
echo Pronto! Tente mandar mensagem no WhatsApp agora.
pause
