#!/bin/bash
# Script de Deploy Automático para VPS Hostinger

VPS_IP="76.13.70.207"
VPS_USER="root"
PROJECT_DIR="/var/www/ruviaro-agent"

echo "========================================="
echo "  DEPLOY RUVIARO AGENT - VPS HOSTINGER"
echo "========================================="
echo ""

# 1. Verificar ambiente no VPS
echo "[1/8] Verificando ambiente Python no VPS..."
ssh $VPS_USER@$VPS_IP "python3 --version && pip3 --version"

# 2. Criar diretório do projeto
echo ""
echo "[2/8] Criando diretório do projeto..."
ssh $VPS_USER@$VPS_IP "mkdir -p $PROJECT_DIR"

# 3. Upload dos arquivos
echo ""
echo "[3/8] Fazendo upload dos arquivos..."
scp -r ruviaro_agent/ $VPS_USER@$VPS_IP:$PROJECT_DIR/
scp requirements.txt $VPS_USER@$VPS_IP:$PROJECT_DIR/
scp .env $VPS_USER@$VPS_IP:$PROJECT_DIR/

# 4. Instalar dependências
echo ""
echo "[4/8] Instalando dependências Python..."
ssh $VPS_USER@$VPS_IP "cd $PROJECT_DIR && pip3 install -r requirements.txt"

# 5. Testar servidor
echo ""
echo "[5/8] Testando servidor (5 segundos)..."
ssh $VPS_USER@$VPS_IP "cd $PROJECT_DIR && timeout 5 python3 ruviaro_agent/src/webhook_server.py || true"

# 6. Instalar PM2
echo ""
echo "[6/8] Instalando PM2 para manter servidor rodando..."
ssh $VPS_USER@$VPS_IP "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs && npm install -g pm2"

# 7. Iniciar com PM2
echo ""
echo "[7/8] Iniciando servidor com PM2..."
ssh $VPS_USER@$VPS_IP "cd $PROJECT_DIR && pm2 delete ruviaro-agent 2>/dev/null || true && pm2 start 'python3 ruviaro_agent/src/webhook_server.py' --name ruviaro-agent && pm2 save && pm2 startup"

# 8. Verificar status
echo ""
echo "[8/8] Verificando status..."
ssh $VPS_USER@$VPS_IP "pm2 status && pm2 logs ruviaro-agent --lines 20"

echo ""
echo "========================================="
echo "  ✅ DEPLOY CONCLUÍDO!"
echo "========================================="
echo ""
echo "Webhook URL: http://76.13.70.207:5000/webhook"
echo ""
echo "Comandos úteis:"
echo "  Ver logs:     ssh root@76.13.70.207 'pm2 logs ruviaro-agent'"
echo "  Restart:      ssh root@76.13.70.207 'pm2 restart ruviaro-agent'"
echo "  Stop:         ssh root@76.13.70.207 'pm2 stop ruviaro-agent'"
echo ""
