@echo off
echo ==============================================
echo   ATUALIZANDO CEREBRO DO DANIEL (5 LAYERS)
echo ==============================================

echo [1/3] Enviando estrutura de pastas (Brain)...
scp -r ruviaro_agent/brain root@76.13.70.207:/var/www/ruviaro-agent/ruviaro_agent/

echo.
echo [2/3] Atualizando codigo (Carregador do Brain)...
scp ruviaro_agent/src/llm_openai.py root@76.13.70.207:/var/www/ruviaro-agent/ruviaro_agent/src/

echo.
echo [3/3] Reiniciando Daniel...
ssh root@76.13.70.207 "pm2 restart ruviaro-agent"

echo.
echo ==============================================
echo ATUALIZACAO CONCLUIDA!
echo O Daniel agora opera com a arquitetura fisica de 5 camadas.
echo ==============================================
pause
