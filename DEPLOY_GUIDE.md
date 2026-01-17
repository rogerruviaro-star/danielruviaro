# 🚀 Deploy Rápido via Git

## Método Simplificado

Já que o repositório está no GitHub, vamos fazer o deploy mais simples:

### Passo 1: Conectar ao VPS
```bash
ssh root@76.13.70.207
# Senha: Ruviaro4545#
```

### Passo 2: Clonar o repositório
```bash
cd /var/www
git clone https://github.com/rogerruviaro-star/danielruviaro.git ruviaro-agent
cd ruviaro-agent
```

### Passo 3: Configurar .env
```bash
nano .env
```

Cole o conteúdo:
```env
# Configurações da API do WhatsApp (Z-API)
API_PROVIDER=ZAPI
ZAPI_INSTANCE_ID=3ED6019729C8B15020203A6098DEEA35
ZAPI_TOKEN=A0264306385444ACA0237C38

# URL da Evolution API (Backup)
EVOLUTION_API_URL=http://76.13.70.207:8080

# Nome da instância
INSTANCE_NAME=ruviaro_final

# API Key (Evolution)
EVOLUTION_API_KEY=DANIEL_RUVIARO_2024_KEY

# OpenAI
OPENAI_API_KEY=AIzaSyD3GIvs5JmwukG_9QsTKu8e3nFVBlBU7FY

# DINTEC ERP
DINTEC_URL=https://dintec.app/acess/
DINTEC_EMPRESA=AUTO PECAS RUVIARO
DINTEC_USUARIO=roger
DINTEC_SENHA1=Ruviaro6886
DINTEC_SENHA2=d4545

# Server Config
PORT=5000
```

Salvar: `Ctrl+X`, `Y`, `Enter`

### Passo 4: Instalar dependências
```bash
apt update
apt install python3-pip -y
pip3 install -r requirements.txt
```

### Passo 5: Testar o servidor
```bash
python3 ruviaro_agent/src/webhook_server.py
```

Se iniciar sem erros, pressione `Ctrl+C` e prossiga.

### Passo 6: Instalar PM2
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt-get install -y nodejs
npm install -g pm2
```

### Passo 7: Iniciar servidor com PM2
```bash
pm2 start "python3 ruviaro_agent/src/webhook_server.py" --name ruviaro-agent
pm2 save
pm2 startup
```

### Passo 8: Abrir porta no firewall
```bash
ufw allow 5000/tcp
```

### Passo 9: Verificar status
```bash
pm2 status
pm2 logs ruviaro-agent --lines 50
```

## ✅ Pronto!

**Webhook URL para configurar na Z-API:**
```
http://76.13.70.207:5000/webhook
```

## Comandos Úteis

```bash
# Ver logs em tempo real
pm2 logs ruviaro-agent

# Restart
pm2 restart ruviaro-agent

# Stop
pm2 stop ruviaro-agent

# Ver status
pm2 status
```
