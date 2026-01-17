@echo off
echo [INFO] Tentando buscar o QR Code via API...
python -c "import requests; headers={'apikey': 'E52CB331B29B-43EE-BB95-92BB8441B73E'}; r = requests.get('http://76.13.70.207:8080/instance/connect/ruviaro', headers=headers); print(r.text);"
pause
