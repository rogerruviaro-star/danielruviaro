@echo off
echo ========================================
echo  CONFIGURANDO WEBHOOK NA Z-API
echo ========================================
echo.
echo [1] Configurando webhook para o VPS Hostinger...
echo.
echo O webhook sera configurado para:
echo http://76.13.70.207:5000/webhook
echo.
echo [2] Configurando webhook na Z-API...
echo.

python -c "import requests; import os; from dotenv import load_dotenv; load_dotenv(); instance_id = os.getenv('ZAPI_INSTANCE_ID'); token = os.getenv('ZAPI_TOKEN'); url = f'https://api.z-api.io/instances/{instance_id}/token/{token}/update-webhook-received'; payload = {'value': 'http://76.13.70.207:5000/webhook'}; headers = {'Content-Type': 'application/json', 'Client-Token': token}; r = requests.put(url, json=payload, headers=headers); print(f'Status: {r.status_code}'); print(f'Resposta: {r.text}')"


echo.
echo [CONCLUIDO] Webhook configurado!
echo.
echo IMPORTANTE: O agente devera estar rodando no VPS!
echo Use: deploy_vps.bat ou COMANDOS_DEPLOY.md
echo.
pause
