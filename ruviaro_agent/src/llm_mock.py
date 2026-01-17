
import re
import re
from .tools import search_products, format_stock_response, search_web_info

class MockRuviaroBrain:
    def __init__(self):
        # Estado Sessão
        self.context = {
            'awaiting_plate': False,
            'awaiting_photo': False,
            'last_results': [], 
            'detected_model': "Gol G5",
            'photo_verified': False,
            'plate_verified': False
        }
        self.cart = [] 
        self.client_name = None
        self.is_first_interaction = True

    def classify_category(self, text):
        lataria = ['parachoque', 'grade', 'capo', 'capô', 'porta', 'farol', 'lanterna', 'retrovisor', 'painel']
        mecanica = ['vela', 'cabo', 'bomba', 'correia', 'pastilha', 'disco', 'freio', 'amortecedor', 'suspesão']
        for k in lataria: 
            if k in text: return 'LATARIA'
        for k in mecanica: 
            if k in text: return 'MECANICA'
        return 'OUTROS'

    def process_message(self, user_message):
        text = user_message.lower()
        
        # --- FLUXO DE BOAS VINDAS / NOME ---
        if self.is_first_interaction:
            self.is_first_interaction = False
            return "Tudo bem? Ruviaro aqui. Qual seu nome amigo e como posso lhe ajudar hoje?"

        if not self.client_name:
            name_match = re.search(r'\b(sou|me chamo|o|eu sou)\s+(\w+)', text)
            if name_match:
                self.client_name = name_match.group(2).title()
            else:
                first_word = text.split()[0]
                if len(first_word) > 2 and first_word not in ['bom', 'boa', 'ola', 'oi', 'preciso', 'tem', 'quero']:
                    self.client_name = first_word.title()
                else:
                    self.client_name = "Amigo"
            
            if len(text.split()) < 4:
                return f"Fala {self.client_name}! Joia. O que você tá precisando pro carro hoje?"
        
        greeting_name = f"{self.client_name}"

        # --- RECONHECIMENTO VISUAL (Simulado) ---
        # Se mandar foto, o "Beto" já identifica o carro e pede a lista
        if '[foto]' in text or 'segue' in text or 'ta ae' in text:
             self.context['photo_verified'] = True
             self.context['awaiting_photo'] = False
             # Simula identificação visual
             return f"Vixe, pancada no {self.context['detected_model']} hein chefia. Mas fica tranquilo.\nVi aqui pela foto que é o modelo novo. **Manda a lista de tudo que quebrou** (parachoque, farol, alma...) que eu já puxo os preços pra você deixar ele zero."

        # --- COMANDOS DE CONTEXTO ---
        if any(x in text for x in ['pix', 'conta', 'total', 'quanto deu', 'fecha']):
            return self.finalize_order()

        if any(x in text for x in ['quero', 'manda', 'pode por', 'inclui', 'separa']) and self.context['last_results']:
            preferred_side = None
            if 'direito' in text or 'ld' in text: preferred_side = 'LD'
            if 'esquerdo' in text or 'le' in text: preferred_side = 'LE'
            
            selected_item = None
            for item in self.context['last_results']:
                if preferred_side:
                    if preferred_side in item['part_name']: selected_item = item; break
                    if preferred_side == 'LD' and ('Direito' in item['part_name'] or ' LD' in item['part_name']): selected_item = item; break
                    if preferred_side == 'LE' and ('Esquerdo' in item['part_name'] or ' LE' in item['part_name']): selected_item = item; break
                else:
                    selected_item = item; break
            
            if selected_item:
                self.cart.append(selected_item)
                self.context['last_results'] = [] 
                return f"Fechou, {greeting_name}! Separando **{selected_item['part_name']}** aqui.\nMais alguma coisa pra lista?"
        
        # --- FLUXO DE BUSCA ---
        category = self.classify_category(text)
        
        stop_words = ['tem', 'preciso', 'de', 'do', 'da', 'o', 'a', 'quero', 'agora', 'direito', 'esquerdo', 'lado', 'sou', 'meu', 'nome', 'é', 'e', 'um', 'uma']
        words = text.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2 and w not in ["amigo"]]
        query = " ".join(keywords)

        if not query and not self.context['awaiting_plate'] and not self.context['awaiting_photo']:
             return f"Não entendi a peça, {greeting_name}. Digita o nome dela pra mim."

        # Regras de Negócio (Guard Rails)
        # MECANICA
        if (category == 'MECANICA' or self.context['awaiting_plate']) and not self.context['plate_verified']:
            plate = self.extract_plate(user_message)
            if not plate:
                self.context['awaiting_plate'] = True
                self.context['last_search_intent'] = query 
                # FRASE DO PROMPT: "Pra eu não te vender a pastilha errada..."
                return f"Opa, consigo sim, {greeting_name}. Mas pra eu não te vender a peça errada, me manda a **PLACA** do carro? O sistema puxa certinho."
            
            self.context['plate_verified'] = True
            self.context['awaiting_plate'] = False
            if not query and self.context.get('last_search_intent'): query = self.context['last_search_intent']
            print(f"[Sistema] Veículo identificado via Placa {plate}: {self.context['detected_model']}")

        # LATARIA (Se não mandou foto ainda)
        if (category == 'LATARIA' or self.context['awaiting_photo']) and not self.context['photo_verified']:
             self.context['awaiting_photo'] = True
             self.context['last_search_intent'] = query
             # FRASE DO PROMPT: "Manda uma foto da peça velha..."
             return f"Fala chefia, tenho sim. Mas pra lataria tem muito detalhe. Manda uma **FOTO** do carro batido pra eu conferir o modelo e não ter erro?"

        if query:
            print(f"[Sistema] Buscando: {query}")
            results = search_products(query, self.context['detected_model'])
            self.context['last_results'] = results
            
            display_results = results
            if 'direito' in text or 'ld' in text:
                display_results = [r for r in results if 'LD' in r['part_name'] or 'Direito' in r['part_name']]
            elif 'esquerdo' in text or 'le' in text:
                display_results = [r for r in results if 'LE' in r['part_name'] or 'Esquerdo' in r['part_name']]
            
            if not display_results:
                 # Tentativa de Ajuda Externa (Loma)
                 # FRASE DO PROMPT REFORÇADA: "Tudo Mastigado"
                 response = "Poxa, tô sem aqui no estoque físico.\n"
                 
                 # Tenta buscar na web simulada (Loma)
                 web_info = search_web_info(query)
                 if "Loma" in web_info:
                     response += "\nMas **pesquisei no catálogo** e vi que tem essa opção:\n"
                     response += web_info
                     response += "\n\nQuer que eu encomende direto da fábrica pra você?"
                 else:
                     response += "Vou ver se acho em algum parceiro."
                     
                 return response

            return format_stock_response(display_results)

        return f"Tô na escuta, {greeting_name}. Manda o nome da peça."

    def extract_plate(self, text):
        match = re.search(r'[a-zA-Z]{3}[0-9][0-9a-zA-Z][0-9]{2}', text)
        if match: return match.group(0).upper()
        return None

    def finalize_order(self):
        if not self.cart: return "Carrinho tá vazio, chefia!"
        total = sum([item['price'] for item in self.cart])
        response = f"📝 **RESUMO DO PEDIDO - Cliente: {self.client_name or 'Amigo'}**\n\n"
        for item in self.cart: response += f"1x {item['part_name']}... R$ {item['price']:.2f}\n"
        response += "-"*30 + f"\n💰 **TOTAL À VISTA: R$ {total:.2f}**\n"
        response += "\nPosso separar aqui pra motoboy retirar?\n"
        response += "\n**Pode fechar tranquilo! Nossa empresa é a melhor do mundo em pós-venda/assistência. Qualquer B.O a gente resolve na hora.**\n"
        response += "\nPagamento via PIX (CNPJ):\n**24775830000159**\nRuviaro Auto Peças Ltda"
        return response
