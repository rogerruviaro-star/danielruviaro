import os
import json
import sqlite3
import datetime
from openai import OpenAI

# Tente pegar a chave do ambiente
API_KEY = os.getenv("OPENAI_API_KEY")

class GPTRuviaroBrain:
    def __init__(self, model="gpt-4o", sender_id=None):
        self.client = OpenAI(api_key=API_KEY)
        self.model = model
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
            
        # Injeta Memória no Prompt e Instruções de Venda
        memory_injection = f"\n\n### DADOS DO CLIENTE (MEMÓRIA)\n{self.customer_context}"
        sales_injection = "\n\n### INSTRUÇÃO DE VENDA CRÍTICA\nSe o cliente pedir uma marca específica (ex: TRW) e o estoque tiver outra (ex: Viemar), você DEVE argumentar que a nossa marca é melhor (mais reforçada, melhor garantia, feita pro Brasil). Nunca perca a venda por marca."
        self.system_prompt = base_prompt + sales_injection + memory_injection
        
        self.history.append({"role": "system", "content": self.system_prompt})

    def _get_db(self):
        return sqlite3.connect(self.db_path)

    def _load_customer_memory(self):
        """Carrega dados do CRM para o prompt."""
        if not self.sender_id:
            return "Cliente Novo (Sem ID)."
            
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            # Busca ou Cria Cliente
            cursor.execute("SELECT name, vehicle_info, trust_level, notes FROM customers WHERE phone = ?", (self.sender_id,))
            row = cursor.fetchone()
            
            if row:
                info = f"Nome: {row[0] or 'Amigo'}\nVeículo: {row[1] or 'Não identificado'}\nNível Confiança: {row[2]}\nNotas: {row[3]}"
                
                # Busca últimas 3 interações para contexto
                cursor.execute("SELECT message, type FROM interactions WHERE customer_id = (SELECT id FROM customers WHERE phone = ?) ORDER BY id DESC LIMIT 3", (self.sender_id,))
                last_msgs = cursor.fetchall()
                if last_msgs:
                    history_summary = "\nÚltimas conversas:\n" + "\n".join([f"- {m[1]}: {m[0][:50]}..." for m in last_msgs])
                    info += history_summary
                return info
            else:
                # Cria novo
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
        # Detecta se é multimídia (imagem) ou texto puro
        if isinstance(user_message, dict) and user_message.get('type') == 'image':
            # Entrada Visual
            content_payload = [
                {"type": "text", "text": user_message.get('text', "Analise esta imagem.")},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": user_message['image_url']
                    }
                }
            ]
            self.history.append({"role": "user", "content": content_payload})
            self._save_interaction(f"[IMAGEM] {user_message['text']}", 'user')
        else:
            # Entrada Texto Puro
            self.history.append({"role": "user", "content": user_message})
            self._save_interaction(user_message, 'user')

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "registrar_veiculo",
                    "description": "Salva o carro do cliente na memória. Use quando ele confirmar o modelo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "vehicle": {"type": "string", "description": "Ex: Gol G5 1.6 ou Honda Civic 2010"},
                            "name": {"type": "string", "description": "Nome do cliente (se ele falou)"}
                        },
                        "required": ["vehicle"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "handoff_para_humano",
                    "description": "Transfere para o atendente humano COTAR PREÇOS/ESTOQUE. O bot sai de cena.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string", "description": "Resumo do que o cliente quer (Peça + Carro + Problema)"}
                        },
                        "required": ["summary"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "diagnosticar_problema",
                    "description": "Ajuda a identificar a peça baseada no sintoma relatado. Consultar base de conhecimento interna.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symptom": {"type": "string", "description": "Descrição do problema (ex: barulho na roda, carro falhando)"}
                        },
                        "required": ["symptom"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "informacoes_loja",
                    "description": "Fornece dados operacionais (PIX, Endereço, Horário).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "enum": ["pix", "address", "hours", "warranty"]}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calcular_parcelamento",
                    "description": "Calcula parcelas com juros de 1.2% a.m. Ofertar proativamente quando falar de preço.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "total_value": {"type": "number", "description": "Valor total à vista"}
                        },
                        "required": ["total_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "correcao_tecnica",
                    "description": "Corrige gentilmente o nome da peça (Ex: cliente diz 'farol traseiro', Beto diz 'lanterna').",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "wrong_term": {"type": "string", "description": "O termo errado usado pelo cliente"},
                            "correct_term": {"type": "string", "description": "O termo técnico correto"},
                            "explanation": {"type": "string", "description": "Breve explicação técnica (Ex: Farol é na frente, lanterna é atrás)"}
                        },
                        "required": ["wrong_term", "correct_term", "explanation"]
                    }
                }
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                self.history.append(response_message)

                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    tool_output = ""
                    
                    if fname == "registrar_veiculo":
                        # Atualiza DB
                        try:
                            conn = self._get_db()
                            cursor = conn.cursor()
                            if args.get('name'):
                                cursor.execute("UPDATE customers SET vehicle_info = ?, name = ? WHERE phone = ?", (args['vehicle'], args['name'], self.sender_id))
                            else:
                                cursor.execute("UPDATE customers SET vehicle_info = ? WHERE phone = ?", (args['vehicle'], self.sender_id))
                            conn.commit()
                            conn.close()
                            tool_output = "Veículo/Nome salvo com sucesso na memória persistente."
                        except Exception as e:
                            tool_output = f"Erro ao salvar: {e}"

                    elif fname == "diagnosticar_problema":
                        tool_output = f"DIAGNOSTICO: Para o sintoma '{args['symptom']}', considere peças comuns como: Buchas, Bieletas, Amortecedores (se suspensão); Pastilhas (se freio). Pergunte se ele ouve estalos ou barulho seco."

                    elif fname == "calcular_parcelamento":
                        valor = float(args['total_value'])
                        tabela = "Opções de Parcelamento (Taxa 1.2% a.m.):\n"
                        for p in range(1, 11): 
                            if p == 1:
                                tabela += f"1x R$ {valor:.2f} (Sem Juros)\n"
                            else:
                                montante = valor * (1 + (0.012 * p))
                                parcela = montante / p
                                tabela += f"{p}x R$ {parcela:.2f} (Total R$ {montante:.2f})\n"
                        tool_output = tabela

                    elif fname == "correcao_tecnica":
                        tool_output = f"CORRECAO: O cliente disse '{args['wrong_term']}', mas o certo é '{args['correct_term']}'. Explique: {args['explanation']}."

                    elif fname == "informacoes_loja":
                        topics = {
                            "pix": "CNPJ: 24.775.830/0001-59 (Ruviaro Auto Peças Ltda). Banco Sicredi.",
                            "address": "Av. Gov. Walter Jobim, 585 - Patronato, Santa Maria - RS",
                            "hours": "Segunda a Sexta: 08:00–12:00, 13:30–18:00. Sábado: 08:00–12:00.",
                            "warranty": "Garantia total de balcão. Deu problema? Trocamos. Nosso pós-venda é referência."
                        }
                        tool_output = topics.get(args['topic'], "Info não disponível.")

                    elif fname == "handoff_para_humano":
                        tool_output = "HANDOFF_TRIGGERED. Avise o cliente que o especialista humano vai assumir para passar valores exatos."

                    self.history.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fname,
                        "content": tool_output
                    })
                
                # Segunda chamada
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.history
                )
                final_answer = second_response.choices[0].message.content
            else:
                final_answer = response_message.content

            self.history.append({"role": "assistant", "content": final_answer})
            self._save_interaction(final_answer, 'bot')
            return final_answer

        except Exception as e:
            return f"Opa, falhou aqui meu sistema: {str(e)}"
