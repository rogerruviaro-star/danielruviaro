
import requests
import os
import sys
import json
import logging
import time
import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Configuração da API
API_PROVIDER = os.getenv("API_PROVIDER", "EVOLUTION").upper()
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "daniel")

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Imports internos
try:
    from ruviaro_agent.src.llm_openai import GPTRuviaroBrain
    from ruviaro_agent.src.audio_handler import transcribe_audio, generate_audio
    HAS_MODULES = True
except ImportError as e:
    logging.error(f"Erro de import: {e}")
    HAS_MODULES = False

app = Flask(__name__)

# Configurações Z-API
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")

# URL base para envio (Z-API)
BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"

sessions = {}

def get_brain(sender_id):
    """Recupera ou cria uma sessão cerebral para o usuário."""
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
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        logging.info(f"📤 [Z-API] Enviado para {phone}: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Erro ao enviar Z-API: {e}")

@app.route('/webhook', methods=['POST'])
def zapi_webhook_handler():
    try:
        data = request.json
        # Log em arquivo para garantir (com encoding utf-8)
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now()}] RECEBIDO: {json.dumps(data)}\n")
        
        print(f"\n\n[DEBUG] DADOS CHEGARAM! Ver debug_log.txt\n\n", flush=True)
        
        # Verifica se é mensagem de Text
        # Z-API estrutura: { "phone": "55...", "text": { "message": "ola" }, ... }
        
        if 'text' in data and 'message' in data['text']:
            phone = data.get('phone')
            message_text = data['text']['message']
            from_me = data.get('fromMe', False)

            # Ignora minhas próprias mensagens
            if from_me:
                return jsonify({"status": "ignored_me"}), 200

            logging.info(f"📩 [Z-API] De {phone}: {message_text}")

            # Cérebro
            agent = get_brain(phone)
            response_text = agent.process_message(message_text)

            # Resposta
            send_message_zapi(phone, response_text)
            
            return jsonify({"status": "success"}), 200

        return jsonify({"status": "ignored_type"}), 200

    except Exception as e:
        logging.error(f"Erro webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(">> Servidor Ruviaro (Z-API Mode) Rodando na porta 5000...")
    app.run(host='0.0.0.0', port=5000)
