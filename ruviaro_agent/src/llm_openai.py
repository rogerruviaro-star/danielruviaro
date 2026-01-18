import os
import json
import sqlite3
import datetime
import google.generativeai as genai

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class GPTRuviaroBrain:
    def __init__(self, model="gemini-pro", sender_id=None):
        self.model = genai.GenerativeModel(model)
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
        
        # Inicializa chat do Gemini
        self.chat = self.model.start_chat(history=[])

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

    def _execute_tool(self, fname, args):
        """Executa as ferramentas/funções internas."""
        tool_output = ""
        
        if fname == "registrar_veiculo":
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
            tool_output = f"DIAGNOSTICO: Para o sintoma '{args.get('symptom', '')}', considere peças comuns como: Buchas, Bieletas, Amortecedores (se suspensão); Pastilhas (se freio). Pergunte se ele ouve estalos ou barulho seco."

        elif fname == "calcular_parcelamento":
            valor = float(args.get('total_value', 0))
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
            tool_output = f"CORRECAO: O cliente disse '{args.get('wrong_term', '')}', mas o certo é '{args.get('correct_term', '')}'. Explique: {args.get('explanation', '')}."

        elif fname == "informacoes_loja":
            topics = {
                "pix": "CNPJ: 24.775.830/0001-59 (Ruviaro Auto Peças Ltda). Banco Sicredi.",
                "address": "Av. Gov. Walter Jobim, 585 - Patronato, Santa Maria - RS",
                "hours": "Segunda a Sexta: 08:00–12:00, 13:30–18:00. Sábado: 08:00–12:00.",
                "warranty": "Garantia total de balcão. Deu problema? Trocamos. Nosso pós-venda é referência."
            }
            tool_output = topics.get(args.get('topic', ''), "Info não disponível.")

        elif fname == "handoff_para_humano":
            tool_output = "HANDOFF_TRIGGERED. Avise o cliente que o especialista humano vai assumir para passar valores exatos."

        return tool_output

    def process_message(self, user_message):
        # Salva interação do usuário
        if isinstance(user_message, dict) and user_message.get('type') == 'image':
            self._save_interaction(f"[IMAGEM] {user_message.get('text', '')}", 'user')
            user_text = user_message.get('text', 'Analise esta imagem.')
        else:
            self._save_interaction(user_message, 'user')
            user_text = user_message

        try:
            # Monta prompt completo com system prompt + mensagem do usuário
            full_prompt = f"""
{self.system_prompt}

### FUNÇÕES DISPONÍVEIS (Use quando apropriado):
- registrar_veiculo: Salva o carro do cliente. Use quando ele confirmar o modelo.
- handoff_para_humano: Transfere para humano para cotação. Use quando precisar de preços.
- diagnosticar_problema: Ajuda diagnosticar peça baseado em sintoma.
- informacoes_loja: Fornece PIX, endereço, horário, garantia.
- calcular_parcelamento: Calcula parcelas com juros 1.2% a.m.
- correcao_tecnica: Corrige termo técnico gentilmente.

Se precisar usar uma função, responda no formato:
[FUNCTION_CALL: nome_da_funcao] {{"parametro": "valor"}}

Mensagem do cliente: {user_text}
"""
            
            # Envia para o Gemini
            response = self.chat.send_message(full_prompt)
            reply = response.text
            
            # Verifica se há chamada de função na resposta
            if "[FUNCTION_CALL:" in reply:
                import re
                match = re.search(r'\[FUNCTION_CALL:\s*(\w+)\]\s*(\{.*?\})', reply, re.DOTALL)
                if match:
                    fname = match.group(1)
                    try:
                        args = json.loads(match.group(2))
                    except:
                        args = {}
                    
                    tool_result = self._execute_tool(fname, args)
                    
                    # Segunda chamada com resultado da ferramenta
                    followup = f"Resultado da função {fname}: {tool_result}\n\nAgora responda ao cliente de forma natural, sem mencionar a função."
                    final_response = self.chat.send_message(followup)
                    reply = final_response.text

            self.history.append({"role": "assistant", "content": reply})
            self._save_interaction(reply, 'bot')
            return reply

        except Exception as e:
            return f"Opa, falhou aqui meu sistema: {str(e)}"
