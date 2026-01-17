
import os
import requests
import io
import time
from openai import OpenAI

# Configuração da API Key (deve estar no .env)
# A classe que chama isso já deve ter garantido que a chave existe
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_url):
    """
    Baixa áudio do WhatsApp e transcreve usando Whisper.
    """
    try:
        print(f"🎤 Baixando áudio: {audio_url}")
        response = requests.get(audio_url)
        response.raise_for_status()
        
        # O OpenAI API precisa de um arquivo com nome e extensão
        # Usamos BytesIO com nome fictício
        audio_file = io.BytesIO(response.content)
        audio_file.name = "audio_whatsapp.ogg"  # Z-API/Evolution geralmente mandam OGG
        
        print("🧠 Transcrevendo com Whisper...")
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            language="pt"
        )
        
        print(f"📝 Transcrição: {transcription.text}")
        return transcription.text
        
    except Exception as e:
        print(f"❌ Erro na transcrição: {e}")
        return "[Erro ao ouvir áudio]"

def generate_audio(text_response):
    """
    Gera áudio de resposta usando OpenAI TTS (Modelo HD, Voz Onyx).
    Salva em arquivo temporário e retorna o caminho.
    """
    try:
        if not text_response:
            return None
            
        print(f"🗣️ Gerando voz para: {text_response[:50]}...")
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx", # Voz masculina, séria e confiável
            input=text_response
        )
        
        # Salva arquivo
        filename = f"response_{int(time.time())}.mp3"
        filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_audio', filename)
        
        # Garante diretório
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        response.stream_to_file(filepath)
        print(f"💾 Áudio salvo em: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Erro na geração de voz: {e}")
        return None
