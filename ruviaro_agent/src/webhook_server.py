
import requests
import os
import sys
import json
import logging
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Logger
logging.basicConfig(level=logging.INFO)

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

# Configurações
# Evolution API Configuration
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "DANIEL_RUVIARO_2024_KEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "daniel")

# URL base para envio (ajuste conforme seu IP real se rodar fora do docker, ou nome do container internamente)
# Se o agente rodar no mesmo docker compose, pode usar http://evolution_api:8080
# Se rodar fora, usar URL externa.
BASE_URL = f"{EVOLUTION_API_URL}/message"


sessions = {}

def get_brain(sender_id):
    """Recupera ou cria uma sessão cerebral para o usuário."""
    if sender_id not in sessions:
        # Aqui poderíamos carregar o histórico do banco de dados (SQLite)
        # Por enquanto, inicia uma nova sessão GPT
        sessions[sender_id] = GPTRuviaroBrain(sender_id=sender_id) # Passa ID para o Brain carregar memória
    return sessions[sender_id]

def send_message(recipient, text=None, audio_path=None):
    """Envia mensagem (Texto ou Áudio) para o WhatsApp."""
    
    clean_phone = recipient.replace("@s.whatsapp.net", "")
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }

    try:
        # 1. Envio de Áudio
        if audio_path:
            import base64
            with open(audio_path, 'rb') as f:
                encoded_string = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {
                "number": clean_phone,
                "audio": encoded_string,
                "mediatype": "audio", # Opcional dependendo da versão
            }
            # Endpoint Evolution: /message/sendWhatsAppAudio ou /message/sendAudio
            url = f"{BASE_URL}/sendWhatsAppAudio/{INSTANCE_NAME}"

            logging.info(f"📤 Enviando Áudio para {clean_phone} via Evolution...")
            response = requests.post(url, json=payload, headers=headers)
            logging.info(f"Status envio áudio: {response.status_code} - {response.text}")
            return

        # 2. Envio de Texto
        if text:
            import random
            time.sleep(random.uniform(2, 4)) # Delay mais curto
            
            payload = {
                "number": clean_phone,
                "text": text
            }
            # Endpoint Evolution: /message/sendText
            url = f"{BASE_URL}/sendText/{INSTANCE_NAME}"
            
            logging.info(f"📤 Enviando Texto para {clean_phone}: {text[:50]}...")
            response = requests.post(url, json=payload, headers=headers)
            logging.info(f"Status envio texto: {response.status_code} - {response.text}")

    except Exception as e:
        logging.error(f"❌ Erro no envio: {e}")

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    sender = None
    message_content = None
    is_audio = False
    audio_url = None

    # --- Detector Evolution API ---
    # Estrutura típica: data.type = "messages.upsert" e o conteúdo dentro de data.data
    
    # Verifica eventos
    event_type = data.get('type')
    
    if event_type == "messages.upsert":
        msg_data = data.get('data', {})
        key = msg_data.get('key', {})
        from_me = key.get('fromMe', False)
        
        # Ignora mensagens enviadas por mim mesmo
        if from_me:
             return jsonify({"status": "ignored_self"}), 200

        sender = key.get('remoteJid') # ex: 55559999@s.whatsapp.net
        message = msg_data.get('message', {})
        
        # 1. Texto Simples
        if 'conversation' in message:
            message_content = message['conversation']
        
        # 2. Texto Estendido (Android/iOS)
        elif 'extendedTextMessage' in message:
            message_content = message['extendedTextMessage'].get('text')
            
        # 3. Áudio
        elif 'audioMessage' in message:
            is_audio = True
            # Evolution geralmente não manda URL pública direto se for base64 habilitado no webhook
            # Mas vamos verificar como pegar. Se 'saveMedia' estiver on no evolution, vem path.
            # Se vier base64, vem em message.audioMessage.url ou mediaKey?
            # Na v2, geralmente precisamos baixar ou vem em base64 se configurado.
            # Para simplificar, vamos avisar que recebeu áudio mas precisamos configurar a conversão.
            pass
            
            # TODO: Implementar download de mídia da Evolution
            # Por enquanto, tratar como não suportado ou tentar extrair texto se possível (transcrição do whatsapp?)
            # Vamos logar e tentar seguir.
    
    # Ignora se não achou remetente ou conteúdo
    if not sender or (not message_content and not is_audio):
        return jsonify({"status": "ignored_no_content"}), 200

    logging.info(f"\n📩 Mensagem de {sender} [Audio={is_audio}]")

    # Transcrição (Whisper) - Ajuste necessário para Evolution (download de media)
    if is_audio:
        # Temporário: Avisar que áudio está desativado na migração
        # message_content = transcribe_audio(...) 
        logging.info("👂 Recebido áudio (AINDA NÃO INTEGRADO COM EVOLUTION DOWNLOAD)")
        # message_content = "[ÁUDIO RECEBIDO - Transcrição pendente de config]"
        return jsonify({"status": "audio_pending_config"}), 200

    # Processamento Cerebral
    agent = get_brain(sender)
    response_text = agent.process_message(message_content)
    
    logging.info(f"🤖 Resposta do Brain: {response_text}")

    # Decisão de Resposta (Texto ou Áudio?)
    # Se entrada foi áudio, resposta é áudio.
    if is_audio:
        audio_file = generate_audio(response_text)
        if audio_file:
            send_message(sender, audio_path=audio_file)
        else:
            # Fallback se falhar geração
            send_message(sender, text=response_text)
    else:
        send_message(sender, text=response_text)
    
    return jsonify({"status": "processed"}), 200

if __name__ == '__main__':
    print("🚀 Servidor Webhook Ruviaro (Z-API + Audio) Rodando...")
    app.run(port=5000)
