# 🚀 Deploy Rápido - Cole os Comandos no Terminal SSH

## 1. Conectar ao VPS
```bash
ssh root@76.13.70.207
```
**Senha:** `Ruviaro4545#`

---

## 2. Clonar Repositório
```bash
cd /var/www
git clone https://github.com/rogerruviaro-star/danielruviaro.git ruviaro-agent
cd ruviaro-agent
```

---

## 3. Instalar Python e Dependências
```bash
apt update && apt install python3-pip -y
pip3 install -r requirements.txt
```

---

## 4. Testar Servidor
```bash
python3 ruviaro_agent/src/webhook_server.py
```
**Se rodar sem erro, pressione `Ctrl+C` e continue**

---

## 5. Instalar Node.js e PM2
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt install -y nodejs
npm install -g pm2
```

---

## 6. Iniciar Servidor 24/7
```bash
pm2 start "python3 ruviaro_agent/src/webhook_server.py" --name ruviaro-agent
pm2 save
pm2 startup
ufw allow 5000/tcp
```

---

## 7. Verificar Status
```bash
pm2 status
pm2 logs ruviaro-agent --lines 50
```

---

## ✅ Configurar Z-API

**URL do Webhook:**
```
http://76.13.70.207:5000/webhook
```

1. Acesse https://app.z-api.io
2. Instância "daniel"
3. Webhooks e configurações gerais
4. Cole o URL em "Ao enviar"
5. Salvar

---

## 📝 Comandos Úteis Depois

```bash
# Ver logs em tempo real
pm2 logs ruviaro-agent

# Restart
pm2 restart ruviaro-agent

# Stop
pm2 stop ruviaro-agent

# Status
pm2 status
```
