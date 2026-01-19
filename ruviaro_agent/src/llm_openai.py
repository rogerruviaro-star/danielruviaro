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
        
        # Conexão CRM (Memória)
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'inventory.db')
        
        # Carregar Persona
        persona_path = os.path.join(os.path.dirname(__file__), 'system_persona.md')
        if os.path.exists(persona_path):
            with open(persona_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = "Você é o Daniel, vendedor da Auto Peças Ruviaro."
        
        # Carregar histórico existente do banco
        self.history = self._load_history()

    def _get_db(self):
        return sqlite3.connect(self.db_path)

    def _load_history(self):
        """Carrega as últimas mensagens do banco de dados."""
        if not self.sender_id:
            return []
            
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            # Busca as últimas 20 mensagens da conversa
            cursor.execute("""
                SELECT message, type FROM interactions 
                WHERE customer_id = (SELECT id FROM customers WHERE phone = ?)
                ORDER BY id DESC LIMIT 20
            """, (self.sender_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Inverte para ordem cronológica
            rows = rows[::-1]
            
            history = []
            for msg, msg_type in rows:
                role = "user" if msg_type == "user" else "assistant"
                history.append({"role": role, "content": msg})
            
            return history
            
        except Exception as e:
            return []

    def _save_interaction(self, message, type_):
        """Salva a mensagem no histórico do banco."""
        if not self.sender_id: 
            return
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            # Garante que o cliente existe
            cursor.execute("SELECT id FROM customers WHERE phone = ?", (self.sender_id,))
            row = cursor.fetchone()
            
            if not row:
                cursor.execute("INSERT INTO customers (phone) VALUES (?)", (self.sender_id,))
                conn.commit()
                cursor.execute("SELECT id FROM customers WHERE phone = ?", (self.sender_id,))
                row = cursor.fetchone()
            
            customer_id = row[0]
            cursor.execute("INSERT INTO interactions (customer_id, message, type) VALUES (?, ?, ?)", 
                           (customer_id, message, type_))
            conn.commit()
            conn.close()
        except Exception as e:
            pass

    def process_message(self, user_message):
        # Salva no banco
        self._save_interaction(user_message, 'user')
        
        # Adiciona ao histórico em memória
        self.history.append({"role": "user", "content": user_message})

        try:
            # Monta a conversa completa
            conversation = f"{self.system_prompt}\n\n## Conversa com o cliente:\n"
            
            # Adiciona todo o histórico
            for msg in self.history:
                if msg["role"] == "user":
                    conversation += f"Cliente: {msg['content']}\n"
                else:
                    conversation += f"Daniel: {msg['content']}\n"
            
            # Pede a resposta (SEM o prefixo Daniel: para evitar repetição)
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
            
            # Adiciona ao histórico e salva
            self.history.append({"role": "assistant", "content": reply})
            self._save_interaction(reply, 'bot')
            
            return reply

        except Exception as e:
            error_msg = "Desculpe, tive um problema técnico. Pode repetir?"
            self._save_interaction(error_msg, 'bot')
            return error_msg
