#!/bin/bash
# BLINDAGEM AUTOMÁTICA DO SERVIDOR RUVIARO
# Execute com: sudo bash harden_vps.sh

echo "🛡️  INICIANDO PROTOCOLO FORTALEZA..."

# 1. Instalar Dependências de Sistema
echo "📦 1/5 Instalando Nginx e Utilitários..."
apt-get update
apt-get install -y nginx

# 2. Proteger Segredos (Mover .env para /etc/)
echo "🔑 2/5 Blindando .env..."
mkdir -p /etc/ruviaro-agent
# Procura .env na pasta atual ou na pasta pai
if [ -f .env ]; then
    cp .env /etc/ruviaro-agent/.env
    echo " -> .env encontrado na raiz."
elif [ -f ../.env ]; then
    cp ../.env /etc/ruviaro-agent/.env
    echo " -> .env encontrado na pasta superior."
elif [ -f /var/www/ruviaro-agent/.env ]; then
    cp /var/www/ruviaro-agent/.env /etc/ruviaro-agent/.env
    echo " -> .env resgatado de /var/www."
else
    echo "⚠️ ALERTA: .env não encontrado! Você terá que criá-lo em /etc/ruviaro-agent/.env manualmente."
fi

# Define permissão 600 (Só root lê)
chmod 600 /etc/ruviaro-agent/.env
chown root:root /etc/ruviaro-agent/.env

# 3. Configurar Nginx (Reverse Proxy)
echo "🌐 3/5 Configurando Proxy Reverso (Porta 80 -> 5000)..."
# Copia o conf que está na pasta deploy
cp ruviaro_agent/deploy/nginx.conf /etc/nginx/sites-available/ruviaro-agent
ln -sf /etc/nginx/sites-available/ruviaro-agent /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

# 4. Migrar para Gunicorn (Produção)
echo "🚀 4/5 Migrando de Flask Dev para Gunicorn..."

# Garante Gunicorn instalado
pip install gunicorn --break-system-packages

# Configura PM2 para rodar Gunicorn
pm2 delete ruviaro-agent
# Roda Gunicorn na porta 5000 (Localhost apenas)
# O wsgi:app está dentro de src, então vamos executar de lá
cd ruviaro_agent/src
pm2 start "gunicorn -w 2 -b 127.0.0.1:5000 wsgi:app" --name ruviaro-agent --interpreter python3
pm2 save

echo "✅ BLINDAGEM CONCLUÍDA COM SUCESSO!"
echo "Status Atual:"
pm2 status
echo "---------------------------------------------------"
echo "O Robô está atrás do Nginx. Teste acessando pelo IP."
