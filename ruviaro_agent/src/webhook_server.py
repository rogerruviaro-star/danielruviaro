
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
from openai import OpenAI
import tempfile
import random
import time

# ... imports ...

# Force load .env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=env_path)

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

# Quick Debug check
if not os.getenv("OPENAI_API_KEY"):
    logging.error("❌ CRITICAL: OPENAI_API_KEY IS MISSING IN ENV!")
else:
    logging.info("✅ OPENAI_API_KEY LOADED.")

# Configurações Z-API
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# URL base para envio (Z-API)
BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"

# Cliente OpenAI para transcrição
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
    """Baixa e transcreve áudio usando OpenAI Whisper."""
    try:
        # Baixa o áudio
        response = requests.get(audio_url)
        if response.status_code != 200:
            logging.error(f"Erro ao baixar áudio: {response.status_code}")
            return None
        
        # Salva em arquivo temporário (Whisper precisa de arquivo)
        # OGG é comum no WhatsApp
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
            temp_audio.write(response.content)
            temp_audio_path = temp_audio.name
        
        logging.info(f"🎤 Transcrevendo arquivo temporário: {temp_audio_path}")
        
        with open(temp_audio_path, "rb") as audio_file:
            transcription_response = openai_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
        
        # Limpa arquivo temp
        try:
            os.remove(temp_audio_path)
        except:
             pass

        transcription = transcription_response.strip()
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
        sender_name = data.get('senderName') or data.get('pushName') or "Cliente"
        
        # Ignora grupos
        if is_group or (phone and "@g.us" in phone):
            logging.info(f"🚫 Ignorando mensagem de grupo: {phone}")
            return jsonify({"status": "ignored_group"}), 200
        
        # INTERVENÇÃO HUMANA DETECTADA (Desativado temporariamente para evitar auto-pause em mensagens da API)
        if from_me:
            logging.info(f"🛑 Mensagem própria detectada (fromMe) de {phone}. Salvando no histórico.")
            if HAS_BRAIN and message_text:
               try:
                   agent = get_brain(phone)
                   # Salva como 'bot' para aparecer como assistant no histórico do LLM
                   agent._save_interaction(message_text, 'bot') 
               except Exception as e:
                   logging.error(f"Erro ao salvar msg humana: {e}")
            
            return jsonify({"status": "ignored_me"}), 200
        
        message_text = None
        
        # Mensagem de texto
        if 'text' in data and 'message' in data['text']:
            message_text = data['text']['message']
            logging.info(f"📩 [Z-API] Texto de {sender_name} ({phone}): {message_text}")
        
        # Mensagem de áudio
        elif 'audio' in data:
            audio_url = data['audio'].get('audioUrl') or data['audio'].get('url')
            if audio_url:
                logging.info(f"🎤 [Z-API] Áudio recebido de {sender_name}, transcrevendo...")
                message_text = transcribe_audio(audio_url)
                if message_text:
                    logging.info(f"🎤 [Z-API] Transcrição de {sender_name}: {message_text}")
                else:
                    # Se falhou a transcrição, pede para digitar
                    send_message_zapi(phone, "Não consegui entender o áudio, pode digitar por favor?")
                    return jsonify({"status": "audio_failed"}), 200

        # Mensagem de Imagem
        elif 'image' in data:
            logging.info(f"📸 [Z-API] Imagem recebida de {sender_name}")
            # Injeta contexto de imagem para o agente reagir com handoff
            message_text = "[O CLIENTE ENVIOU UMA FOTO DO CARRO/PEÇA. AGRADEÇA E USE A BOLINHA VERDE 🟢 PARA CHAMAR O HUMANO CONFERIR]"
        
        # Processa a mensagem (texto ou áudio transcrito)
        if message_text and HAS_BRAIN:
            try:
                agent = get_brain(phone)
                
                # Verifica se o agente deve responder (Handoff ou Pausa)
                if not agent.should_reply(message_text):
                    logging.info(f"🚫 Agente em silêncio (Handoff ou Pausa) para {phone}.")
                    return jsonify({"status": "silenced"}), 200

                response_text = agent.process_message(message_text, user_name=sender_name)
                logging.info(f"🧠 Resposta: {response_text[:100]}...")
            except Exception as e:
                logging.error(f"❌ Erro no Brain: {e}")
                response_text = "Desculpe, tive um problema técnico. Pode repetir?"
            
            # Delay "Humano" (3 a 7 segundos)
            delay = random.randint(3, 7)
            logging.info(f"⏳ Aguardando {delay}s para parecer humano...")
            time.sleep(delay)

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
