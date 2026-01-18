# 🤖 Ruviaro WhatsApp Agent

Agente inteligente de WhatsApp integrado com o ERP Dintec para Auto Peças Ruviaro.

## 📋 Descrição

Este projeto é um agente conversacional de WhatsApp que utiliza inteligência artificial (OpenAI) para responder clientes de forma natural e profissional, com integração ao ERP Dintec para consulta de produtos, preços e estoque.

## 🛠️ Tecnologias

- **Python 3** - Backend
- **Flask** - Servidor webhook
- **Z-API** - API do WhatsApp
- **OpenAI GPT** - Inteligência artificial
- **Dintec ERP** - Sistema de gestão
- **PM2** - Gerenciador de processos (produção)
- **VPS Hostinger** - Hospedagem em produção

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
# Z-API WhatsApp
API_PROVIDER=ZAPI
ZAPI_INSTANCE_ID=seu_instance_id
ZAPI_TOKEN=seu_token

# OpenAI
OPENAI_API_KEY=sua_chave_openai

# DINTEC ERP
DINTEC_URL=https://dintec.app/acess/
DINTEC_EMPRESA=AUTO PECAS RUVIARO
DINTEC_USUARIO=seu_usuario
DINTEC_SENHA1=sua_senha1
DINTEC_SENHA2=sua_senha2

# Servidor
PORT=5000
```

## 🚀 Deploy no VPS Hostinger

### Opção 1: Comandos Diretos (Recomendado)

Siga o guia completo em: **[COMANDOS_DEPLOY.md](COMANDOS_DEPLOY.md)**

### Opção 2: Script Automatizado

**Windows:**
```bash
deploy_vps.bat
```

**Linux/Mac:**
```bash
chmod +x deploy_vps.sh
./deploy_vps.sh
```

### Configurar Webhook na Z-API

Após o deploy, configure o webhook:

1. Acesse [Z-API Dashboard](https://app.z-api.io)
2. Selecione sua instância
3. Vá em "Webhooks e configurações gerais"
4. Cole a URL do webhook:
   ```
   http://76.13.70.207:5000/webhook
   ```
5. Salvar

**Ou use o script automatizado:**
```bash
setup_webhook_zapi.bat
```

## 💻 Desenvolvimento Local

### Instalar Dependências

```bash
pip install -r requirements.txt
```

### Rodar o Servidor

```bash
python ruviaro_agent/src/webhook_server.py
```

Ou use:
```bash
run_agent.bat
```

## 📁 Estrutura do Projeto

```
danielruviaro/
├── ruviaro_agent/           # Código principal
│   ├── src/
│   │   ├── webhook_server.py    # Servidor Flask
│   │   ├── llm_openai.py        # Lógica do agente IA
│   │   └── audio_handler.py     # Processamento de áudio
├── .env                     # Variáveis de ambiente
├── requirements.txt         # Dependências Python
├── COMANDOS_DEPLOY.md      # Guia de deploy passo-a-passo
├── DEPLOY_GUIDE.md         # Guia técnico detalhado
└── deploy_vps.bat/sh       # Scripts de deploy automatizado
```

## 📡 API do Webhook

**Endpoint:** `POST /webhook`

Recebe eventos do WhatsApp via Z-API e processa mensagens de texto.

### Exemplo de Payload (Z-API):

```json
{
  "phone": "5511999999999",
  "text": {
    "message": "Olá, preciso de uma peça"
  },
  "fromMe": false
}
```

## 🔧 Comandos Úteis (Produção)

### Ver logs em tempo real:
```bash
ssh root@76.13.70.207 'pm2 logs ruviaro-agent'
```

### Restart do agente:
```bash
ssh root@76.13.70.207 'pm2 restart ruviaro-agent'
```

### Verificar status:
```bash
ssh root@76.13.70.207 'pm2 status'
```

### Parar o agente:
```bash
ssh root@76.13.70.207 'pm2 stop ruviaro-agent'
```

## 📝 Informações do Servidor

- **IP:** 76.13.70.207
- **Porta:** 5000
- **Webhook URL:** http://76.13.70.207:5000/webhook
- **Usuário SSH:** root
- **Diretório:** /var/www/ruviaro-agent

## 🤝 Suporte

Para dúvidas ou problemas:
- Verifique os logs: `pm2 logs ruviaro-agent`
- Consulte [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)
- Consulte [COMANDOS_DEPLOY.md](COMANDOS_DEPLOY.md)

## 📄 Licença

Projeto privado - Auto Peças Ruviaro © 2024
