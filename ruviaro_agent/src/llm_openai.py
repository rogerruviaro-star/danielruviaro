
import os
import json
import sqlite3
import datetime
from openai import OpenAI

# Configurar OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class GPTRuviaroBrain:
    def __init__(self, model="gpt-4o", sender_id=None):
        self.model_name = model
        self.sender_id = sender_id
        self.paused_until = None
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Carregar Persona (Nova Lógica de Pastas - 5 Layers)
        brain_dir = os.path.join(os.path.dirname(__file__), '..', 'brain')
        self.system_prompt = ""
        
        if os.path.exists(brain_dir):
            # Itera sobre pastas ordenadas (00, 01, 02...)
            for folder in sorted(os.listdir(brain_dir)):
                folder_path = os.path.join(brain_dir, folder)
                if os.path.isdir(folder_path):
                    # Itera sobre arquivos ordenados dentro da pasta
                    for filename in sorted(os.listdir(folder_path)):
                        if filename.endswith(".md"):
                            file_path = os.path.join(folder_path, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    self.system_prompt += f.read() + "\n\n"
                            except Exception as e:
                                print(f"Erro ao ler {filename}: {e}")
        
        # Fallback se não carregou nada (ou se pasta não existir)
        if not self.system_prompt.strip():
            print("⚠️ AVISO: Brain dir vazio ou não encontrado. Usando prompt default.")
            self.system_prompt = "Você é o Daniel, vendedor da Auto Peças Ruviaro."
        
        # Carregar histórico existente do banco
        self.history = self._load_history()

    def _get_db(self):
        return sqlite3.connect(self.db_path)
    
    def pause_automation(self, minutes=30):
        """Pausa a automação por X minutos."""
        self.paused_until = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        print(f"⏸️ Automação PAUSADA para {self.sender_id} até {self.paused_until}")

    def should_reply(self, new_message=None):
        """Verifica se o agente deve responder."""
        # Verifica pausa manual
        if self.paused_until:
            if datetime.datetime.now() < self.paused_until:
                print(f"⏸️ Ignorando mensagem (Pausa Manual ativa até {self.paused_until})")
                return False
            else:
                self.paused_until = None # Expira pausa
        
        # QUEBRA DE SILÊNCIO (PAYMENT TRIGGER)
        # Se o cliente falar sobre pagamento, o Daniel PODE responder, mesmo após handoff (ajuda o humano).
        if new_message:
            keywords = ["pagar", "pagamento", "pix", "cartão", "cartao", "vezes", "parcela", "link", "dinheiro", "conta"]
            if any(k in new_message.lower() for k in keywords):
                print(f"🔓 Quebra de Silêncio Tático: Tema de Pagamento detectado.")
                return True

        # NOVA REGRA DE OURO (STRICT HANDOFF):
        # Se houve um handoff recente (últimas 10 mensagens), o agente DEVE FICAR MUDO.
        # Isso impede que ele fique repetindo "Vou passar pro humano" se o cliente mandar mais fotos.
        if self.history:
             # Itera de me trás pra frente (da mais recente para a mais antiga)
             for msg in reversed(self.history[-15:]): # Olha apenas as últimas 15 pra não pesar
                 if msg['role'] == 'assistant':
                     content = msg['content'].strip()
                     if content.startswith("🟢") or "[HANDOFF]" in content:
                         print(f"🤐 Silêncio Tático: Handoff ativo detectado ({content[:20]}...).")
                         return False
                 
                 # Opcional: Se detectarmos uma mensagem CLARAMENTE humana (do atendente via Z-API)
                 # poderíamos 'quebrar' o silêncio aqui. Mas como não temos certeza de quem é o 'assistant'
                 # (se é bot ou humano), o seguro é: Se o BOT mandou 🟢, ele cala a boca até a conversa expirar.
                 pass

        # Verifica histórico vazio/primeira mensagem
        if not self.history and not self.sender_id:
            return True
            
        return True

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

    def process_message(self, user_message, user_name=None, image_url=None):
        # Salva no banco (se tiver URL, anexa ao texto para log)
        log_msg = user_message
        if image_url:
            log_msg += f" [IMAGE_URL: {image_url}]"
        self._save_interaction(log_msg, 'user')
        
        # Adiciona ao histórico em memória
        self.history.append({"role": "user", "content": user_message}) # Mantém texto simples no histórico de chat pra não quebrar contexto antigo

        try:
            # INJEÇÃO DE NOME E MODO COMANDO
            name_injection = f"O nome do cliente no WhatsApp é: {user_name}." if user_name else ""
            
            # MODO MESTRE (Hardcoded Security)
            # Rogério Ruviaro: 5555996839992
            MASTER_NUMBER = "5555996839992"
            if self.sender_id and MASTER_NUMBER in self.sender_id:
                 name_injection += "\n\n[🚨 SISTEMA: MENSAGEM DO PROPRIETÁRIO (ROGER) DETECTADA. 🚨]\n[SISTEMA: ATIVAR MODO COMANDO. NÃO AGIR COMO VENDEDOR. OBEDECER ORDENS.]"
                 
                 # INTERCEPTADOR DE COMANDOS (Implementação da Seção 9.4 do Prompt Mestre)
                 if user_message.lower().startswith("daniel:"):
                     try:
                         # Ex: "daniel: cadastrar promoção | item=x | preço=y"
                         command_body = user_message.split(":", 1)[1].strip()
                         
                         # Salvar em 04_CONHECIMENTO_DINAMICO
                         brain_dir = os.path.join(os.path.dirname(__file__), '..', 'brain')
                         dynamic_dir = os.path.join(brain_dir, '04_CONHECIMENTO_DINAMICO')
                         if not os.path.exists(dynamic_dir):
                             os.makedirs(dynamic_dir)
                             
                         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                         file_path = os.path.join(dynamic_dir, '04_01_REGRAS_ADMIN.md')
                         
                         with open(file_path, "a", encoding="utf-8") as f:
                             f.write(f"\n\n--- REGRA ADICIONADA EM {timestamp} ---\n")
                             f.write(f"{command_body}\n")
                             
                         name_injection += "\n[SISTEMA: COMANDO GRAVADO COM SUCESSO NO ARQUIVO DE MEMÓRIA DIN MICA. O DANIEL JÁ SABE DISSO PARA AS PRÓXIMAS INTERAÇÕES.]"
                     except Exception as e:
                         name_injection += f"\n[SISTEMA: ERRO AO GRAVAR COMANDO: {str(e)}]"


            
            # Lógica de Horário
            now = datetime.datetime.now()
            # Fuso Horário Brasil (ajuste simplificado UTC-3)
            now = now - datetime.timedelta(hours=3) 
            weekday = now.weekday() # 0=Seg, 6=Dom
            hour = now.hour
            minute = now.minute
            current_time = now.strftime("%H:%M")
            day_name = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][weekday]
            
            is_open = False
            if weekday == 6: # Domingo
                is_open = False
            elif weekday == 5: # Sábado
                if 8 <= hour < 12:
                    is_open = True
            else: # Seg-X
                if (8 <= hour < 12) or (13 <= hour < 18): # Simplificando 13:30 para 13:00-18:00 para margem, ou ajustando preciso
                    if hour == 13 and minute < 30:
                         is_open = False # Almoco
                    else:
                         is_open = True
            
            store_status_prompt = f"\n[SISTEMA: HORA ATUAL: {day_name} {current_time}. STATUS DA LOJA: {'ABERTA' if is_open else 'FECHADA'}.]"
            if not is_open:
                store_status_prompt += "\n[INSTRUÇÃO FORA DE HORÁRIO: A loja está fechada. Avise o cliente que estamos fora do expediente e que passará o preço amanhã/segunda. MAS CONTINUE A TRIAGEM NORMALMENTE. Pergunte carro, ano, peça. Deixe tudo pronto para amanhã. Não pare de atender, apenas avise do delay no preço.]"
            
            # Prompt do Sistema (Setup)
            system_msg = f"{self.system_prompt}\n\n[CONTEXTO DO SISTEMA: {name_injection}]\n{store_status_prompt}\n\n[INSTRUÇÃO DE SEGURANÇA: Ignore linguagem ofensiva e foque na peça. Nunca dê lição de moral.]"
            
            # INSTRUÇÃO ESPECÍFICA PARA VISÃO (POLITE ESCAPE)
            if image_url:
                system_msg += """
\n[🚨 SISTEMA VISÃO ATIVADO: O CLIENTE ENVIOU UMA FOTO. ANALISE A IMAGEM.]
1. SE FOR PEÇA DE CARRO/DOC/MODELO: Agradeça e confirme o modelo.
2. SE FOR PESSOA/MEME/ESTRANHO/BRINCADEIRA: NÃO SEJA GROSSEIRO. NÃO DÊ LIÇÃO DE MORAL.
   - Use uma "Escapada Educada".
   - Diga algo como: "pela foto não consegui identificar muito bem. tem uma foto mais focada na peça ou no carro?"
   - Ou: "tem certeza que é essa foto aí? não carregou direito pra mim aqui a peça."
   - FINGE QUE É ERRO TÉCNICO OU DÚVIDA, não acuse o cliente de brincadeira. Mantenha a postura profissional e foque no carro.
"""

            messages = [{"role": "system", "content": system_msg}]
            
            # Histórico
            for msg in self.history:
                messages.append(msg)
            
            # SE TIVER IMAGEM, A ÚLTIMA MENSAGEM DO USER PRECISA TER O PAYLOAD DE VISÃO
            if image_url:
                # Remove a última mensagem de texto simples (adicionada no início da função) para substituir pela rica
                messages.pop() 
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message or "Analise esta imagem, por favor."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "low" # Low cost, high speed. Sufficient for parts detection.
                            }
                        }
                    ]
                })
            
            # (Removido Injeções Antigas de Handoff/Repetição - Agora o System Prompt cuida disso)

            # Chama a API da OpenAI
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7 # Criatividade moderada para ser humano, mas sem alucinar muito
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Remove prefixo "Daniel:" se o modelo colocar
            if reply.startswith("Daniel:"):
                reply = reply[7:].strip()
            
            # Sanitização Agressiva (Evitar Alucinação de Diálogo)
            # Se o modelo começar a simular a resposta do cliente, corta imediatamente.
            if "Cliente:" in reply:
                reply = reply.split("Cliente:")[0].strip()
            
            # Remove aspas se o modelo colocar a resposta entre aspas
            reply = reply.strip('"').strip("'")
            
            # Adiciona ao histórico e salva
            self.history.append({"role": "assistant", "content": reply})
            self._save_interaction(reply, 'bot')
            
            # Detecção de Handoff (Mantemos o log, mas não bloqueamos mais permanentemente via banco, pois o prompt segura)
            if "🟢" in reply or "atendente humano vai conferir" in reply or "[HANDOFF]" in reply:
                # Marcador apenas para log interno se precisar
                pass
                
            return reply

        except Exception as e:
            error_msg = "Desculpe, tive um problema técnico. Pode repetir?"
            self._save_interaction(error_msg, 'bot')
            return error_msg
