
import requests
import os
import sys
import json
import logging
import datetime
import tempfile
import base64
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai

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
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# URL base para envio (Z-API)
BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"

# Cliente Gemini para transcrição
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

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

def transcribe_audio(audio_url):
    """Baixa e transcreve áudio usando Gemini."""
    try:
        # Baixa o áudio
        response = requests.get(audio_url)
        if response.status_code != 200:
            logging.error(f"Erro ao baixar áudio: {response.status_code}")
            return None
        
        audio_data = response.content
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Usa Gemini para transcrever
        transcription_response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {
                    "parts": [
                        {"text": "Transcreva este áudio em português. Retorne APENAS o texto transcrito, sem formatação adicional:"},
                        {
                            "inline_data": {
                                "mime_type": "audio/ogg",
                                "data": audio_base64
                            }
                        }
                    ]
                }
            ]
        )
        
        transcription = transcription_response.text.strip()
        logging.info(f"🎤 Transcrição: {transcription}")
        return transcription
        
    except Exception as e:
        logging.error(f"Erro na transcrição: {e}")
        return None

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
        
        # Log em arquivo
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now()}] RECEBIDO: {json.dumps(data, ensure_ascii=False)}\n")
        
        logging.info(f"[DEBUG] DADOS CHEGARAM!")
        
        phone = data.get('phone')
        from_me = data.get('fromMe', False)
        is_group = data.get('isGroup', False)
        
        # Ignora grupos
        if is_group or (phone and "@g.us" in phone):
            logging.info(f"🚫 Ignorando mensagem de grupo: {phone}")
            return jsonify({"status": "ignored_group"}), 200
        
        # Ignora minhas próprias mensagens
        if from_me:
            logging.info(f"Ignorando mensagem própria de {phone}")
            return jsonify({"status": "ignored_me"}), 200
        
        message_text = None
        
        # Mensagem de texto
        if 'text' in data and 'message' in data['text']:
            message_text = data['text']['message']
            logging.info(f"📩 [Z-API] Texto de {phone}: {message_text}")
        
        # Mensagem de áudio
        elif 'audio' in data:
            audio_url = data['audio'].get('audioUrl') or data['audio'].get('url')
            if audio_url:
                logging.info(f"🎤 [Z-API] Áudio recebido de {phone}, transcrevendo...")
                message_text = transcribe_audio(audio_url)
                if message_text:
                    logging.info(f"🎤 [Z-API] Transcrição de {phone}: {message_text}")
                else:
                    # Se falhou a transcrição, pede para digitar
                    send_message_zapi(phone, "Não consegui entender o áudio, pode digitar por favor?")
                    return jsonify({"status": "audio_failed"}), 200
        
        # Processa a mensagem (texto ou áudio transcrito)
        if message_text and HAS_BRAIN:
            try:
                agent = get_brain(phone)
                response_text = agent.process_message(message_text)
                logging.info(f"🧠 Resposta: {response_text[:100]}...")
            except Exception as e:
                logging.error(f"❌ Erro no Brain: {e}")
                response_text = "Desculpe, tive um problema técnico. Pode repetir?"
            
            send_message_zapi(phone, response_text)
            return jsonify({"status": "success"}), 200
        
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
