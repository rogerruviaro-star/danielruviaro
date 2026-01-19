
import requests
import os
import sys
import json
import logging
import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Imports internos
try:
    from ruviaro_agent.src.llm_openai import GPTRuviaroBrain
    HAS_BRAIN = True
    logging.info("✅ GPTRuviaroBrain carregado com sucesso!")
except ImportError as e:
    logging.error(f"Erro de import do Brain: {e}")
    HAS_BRAIN = False

app = Flask(__name__)

# Configurações Z-API
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN", "")  # Token de segurança (opcional mas recomendado)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# URL base para envio (Z-API)
BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"

logging.info(f"🔧 Z-API Instance: {ZAPI_INSTANCE_ID}")
logging.info(f"🔧 Z-API Base URL: {BASE_URL}")

sessions = {}

def get_brain(sender_id):
    """Recupera ou cria uma sessão cerebral para o usuário."""
    if not HAS_BRAIN:
        return None
    if sender_id not in sessions:
        sessions[sender_id] = GPTRuviaroBrain(sender_id=sender_id) 
    return sessions[sender_id]

def send_message_zapi(phone, text):
    """Envia mensagem de TEXTO via Z-API."""
    try:
        url = f"{BASE_URL}/send-text"
        payload = {
            "phone": phone,
            "message": text
        }
        headers = {
            "Content-Type": "application/json"
        }
        # Adiciona Client-Token se configurado
        if ZAPI_CLIENT_TOKEN:
            headers["Client-Token"] = ZAPI_CLIENT_TOKEN
        
        logging.info(f"📤 Enviando para Z-API: URL={url}")
        logging.info(f"📤 Payload: {json.dumps(payload)}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        logging.info(f"📤 [Z-API] Status: {response.status_code}")
        logging.info(f"📤 [Z-API] Resposta: {response.text}")
        
        return response.status_code
    except Exception as e:
        logging.error(f"❌ Erro ao enviar Z-API: {e}")
        return 500

@app.route('/webhook', methods=['POST'])
def zapi_webhook_handler():
    try:
        data = request.json
        
        # Log em arquivo para garantir (com encoding utf-8)
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now()}] RECEBIDO: {json.dumps(data, ensure_ascii=False)}\n")
        
        logging.info(f"[DEBUG] DADOS CHEGARAM!")
        
        # Verifica se é mensagem de Text
        # Z-API estrutura: { "phone": "55...", "text": { "message": "ola" }, ... }
        
        if 'text' in data and 'message' in data['text']:
            phone = data.get('phone')
            message_text = data['text']['message']
            from_me = data.get('fromMe', False)

            # Ignora minhas próprias mensagens
            if from_me:
                logging.info(f"Ignorando mensagem própria de {phone}")
                return jsonify({"status": "ignored_me"}), 200

            logging.info(f"📩 [Z-API] De {phone}: {message_text}")

            # Processa com o Cérebro (Gemini)
            if HAS_BRAIN:
                try:
                    agent = get_brain(phone)
                    response_text = agent.process_message(message_text)
                    logging.info(f"🧠 Resposta do Gemini: {response_text[:100]}...")
                except Exception as e:
                    logging.error(f"❌ Erro no Brain: {e}")
                    response_text = "Opa! Aqui é o Beto da Ruviaro. Tô com uma instabilidade aqui, pode repetir?"
            else:
                response_text = "Olá! Aqui é o Beto. Em que posso ajudar?"

            # Envia resposta
            send_message_zapi(phone, response_text)
            
            return jsonify({"status": "success"}), 200

        # Verifica se é mensagem de áudio
        if 'audio' in data:
            phone = data.get('phone')
            from_me = data.get('fromMe', False)
            
            if from_me:
                return jsonify({"status": "ignored_me"}), 200
            
            logging.info(f"🎤 [Z-API] Áudio recebido de {phone}")
            
            # Pede para digitar
            response_text = "Opa! Aqui na loja tá um pouco barulhento e não consegui ouvir bem o áudio. Pode me passar por escrito o que você precisa?"
            send_message_zapi(phone, response_text)
            
            return jsonify({"status": "audio_handled"}), 200

        return jsonify({"status": "ignored_type"}), 200

    except Exception as e:
        logging.error(f"Erro webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "brain": HAS_BRAIN,
        "zapi_instance": ZAPI_INSTANCE_ID,
        "gemini_key": "set" if GEMINI_API_KEY else "missing"
    }), 200

if __name__ == '__main__':
    print(">> Servidor Ruviaro (Z-API + Gemini) Rodando na porta 5000...")
    app.run(host='0.0.0.0', port=5000)
