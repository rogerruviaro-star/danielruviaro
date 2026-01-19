import os
import json
import sqlite3
import datetime
from google import genai
from google.genai import types

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

class GPTRuviaroBrain:
    def __init__(self, model="gemini-2.0-flash", sender_id=None):
        self.model_name = model
        self.sender_id = sender_id
        self.history = []  # Histórico da conversa atual
        
        # Conexão CRM (Memória)
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'inventory.db')
        
        # Carregar Contexto do Cliente
        self.customer_context = self._load_customer_memory()
        
        # Carregar Persona
        persona_path = os.path.join(os.path.dirname(__file__), 'system_persona.md')
        if os.path.exists(persona_path):
            with open(persona_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        else:
            base_prompt = "Você é o Daniel, vendedor da Auto Peças Ruviaro."
            
        self.system_prompt = base_prompt

    def _get_db(self):
        return sqlite3.connect(self.db_path)

    def _load_customer_memory(self):
        """Carrega dados do CRM para o prompt."""
        if not self.sender_id:
            return ""
            
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, vehicle_info, trust_level, notes FROM customers WHERE phone = ?", (self.sender_id,))
            row = cursor.fetchone()
            
            if row:
                info = f"Nome do cliente: {row[0] or 'Desconhecido'}\nVeículo: {row[1] or 'Não informado'}"
                return info
            else:
                cursor.execute("INSERT INTO customers (phone) VALUES (?)", (self.sender_id,))
                conn.commit()
                return ""
        except Exception as e:
            return ""
        finally:
            if 'conn' in locals(): conn.close()

    def _save_interaction(self, message, type_):
        """Salva a mensagem no histórico do banco."""
        if not self.sender_id: return
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO interactions (customer_id, message, type) VALUES ((SELECT id FROM customers WHERE phone = ?), ?, ?)", 
                           (self.sender_id, message, type_))
            conn.commit()
            conn.close()
        except:
            pass

    def process_message(self, user_message):
        # Salva interação do usuário
        self._save_interaction(user_message, 'user')
        
        # Adiciona ao histórico da sessão
        self.history.append({"role": "user", "content": user_message})

        try:
            # Monta o histórico de conversa
            conversation = f"{self.system_prompt}\n\n"
            
            # Adiciona contexto do cliente se houver
            if self.customer_context:
                conversation += f"## Dados do cliente:\n{self.customer_context}\n\n"
            
            # Adiciona histórico de mensagens
            conversation += "## Conversa:\n"
            for msg in self.history:
                if msg["role"] == "user":
                    conversation += f"Cliente: {msg['content']}\n"
                else:
                    conversation += f"Daniel: {msg['content']}\n"
            
            # Pede a resposta
            conversation += "Daniel:"
            
            # Chama a API do Gemini
            response = client.models.generate_content(
                model=self.model_name,
                contents=conversation
            )
            
            reply = response.text.strip()
            
            # Remove prefixo "Daniel:" se o modelo colocar
            if reply.startswith("Daniel:"):
                reply = reply[7:].strip()
            
            # Adiciona ao histórico
            self.history.append({"role": "assistant", "content": reply})
            self._save_interaction(reply, 'bot')
            
            return reply

        except Exception as e:
            return f"Desculpe, tive um problema técnico. Pode repetir?"
