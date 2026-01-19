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
        self.history = []
        
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
            base_prompt = "Você é o Beto, assistente da Ruviaro Auto Peças."
            
        # Injeta Memória no Prompt
        memory_injection = f"\n\n### DADOS DO CLIENTE (MEMÓRIA)\n{self.customer_context}"
        sales_injection = "\n\n### INSTRUÇÃO DE VENDA CRÍTICA\nSe o cliente pedir uma marca específica (ex: TRW) e o estoque tiver outra (ex: Viemar), você DEVE argumentar que a nossa marca é melhor (mais reforçada, melhor garantia, feita pro Brasil). Nunca perca a venda por marca."
        self.system_prompt = base_prompt + sales_injection + memory_injection

    def _get_db(self):
        return sqlite3.connect(self.db_path)

    def _load_customer_memory(self):
        """Carrega dados do CRM para o prompt."""
        if not self.sender_id:
            return "Cliente Novo (Sem ID)."
            
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, vehicle_info, trust_level, notes FROM customers WHERE phone = ?", (self.sender_id,))
            row = cursor.fetchone()
            
            if row:
                info = f"Nome: {row[0] or 'Amigo'}\nVeículo: {row[1] or 'Não identificado'}\nNível Confiança: {row[2]}\nNotas: {row[3]}"
                
                cursor.execute("SELECT message, type FROM interactions WHERE customer_id = (SELECT id FROM customers WHERE phone = ?) ORDER BY id DESC LIMIT 3", (self.sender_id,))
                last_msgs = cursor.fetchall()
                if last_msgs:
                    history_summary = "\nÚltimas conversas:\n" + "\n".join([f"- {m[1]}: {m[0][:50]}..." for m in last_msgs])
                    info += history_summary
                return info
            else:
                cursor.execute("INSERT INTO customers (phone) VALUES (?)", (self.sender_id,))
                conn.commit()
                return "Cliente Novo. Tente descobrir o nome e o carro dele."
        except Exception as e:
            return f"Erro ao carregar memória: {e}"
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
        if isinstance(user_message, dict) and user_message.get('type') == 'image':
            self._save_interaction(f"[IMAGEM] {user_message.get('text', '')}", 'user')
            user_text = user_message.get('text', 'Analise esta imagem.')
        else:
            self._save_interaction(user_message, 'user')
            user_text = user_message

        try:
            # Monta prompt completo
            full_prompt = f"{self.system_prompt}\n\nMensagem do cliente: {user_text}"
            
            # Chama a API do Gemini com o novo pacote
            response = client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
            reply = response.text
            
            self.history.append({"role": "assistant", "content": reply})
            self._save_interaction(reply, 'bot')
            return reply

        except Exception as e:
            return f"Opa, falhou aqui meu sistema: {str(e)}"
