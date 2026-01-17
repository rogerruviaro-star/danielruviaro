
import os
import re
from tools import search_products, format_stock_response

# Tente importar openai, se não tiver, roda em modo simulação
try:
    from openai import OpenAI
    HAS_OPENAI_LIB = True
except ImportError:
    HAS_OPENAI_LIB = False

class RuviaroAgent:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.use_real_ai = HAS_OPENAI_LIB and self.api_key
        
        # Carregar System Prompt
        with open('ruviaro_agent/src/system_persona.md', 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()

        if self.use_real_ai:
            print("🚀 Modo OpenAI ATIVADO. Usando cérebro real.")
            self.client = OpenAI(api_key=self.api_key)
        else:
            print("⚠️ Modo Simulação (Regex) ATIVADO. (Configure OPENAI_API_KEY para modo real)")

    def process_message(self, user_text):
        if self.use_real_ai:
            return self._process_with_gpt(user_text)
        else:
            return self._process_with_regex(user_text)

    def _process_with_regex(self, text):
        """Simulação simples para demonstração sem API Key"""
        text_lower = text.lower()
        
        # Detectar intenção de busca de peça
        # Procura padrões como "preço do [peça]", "tem [peça]", etc
        # Simplificação: assume que tudo que não é saudação é busca
        
        if any(x in text_lower for x in ['bom dia', 'boa tarde', 'ola', 'oi']):
            return "Opa, bom dia! Beto aqui da Autopeças. O que manda hoje patrão?"
        
        # Extrair filtros básicos (Bem rudimentar, só para Demo)
        # Tenta achar ano (4 digitos)
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        year = year_match.group(0) if year_match else None
        
        # Tenta achar modelos conhecidos
        models = ['gol', 'onix', 'uno', 'palio', 'corsa']
        model = next((m for m in models if m in text_lower), None)
        
        # O resto é a peça (aproximação grosseira)
        # Remove ano e modelo da string para "limpar" o termo da peça
        clean_text = text_lower
        if year: clean_text = clean_text.replace(year, '')
        if model: clean_text = clean_text.replace(model, '')
        
        part_term = clean_text.replace('tem', '').replace('preciso', '').replace('preço', '').strip()
        
        if len(part_term) < 3:
            return "Não entendi qual peça você precisa, parceiro. Pode repetir?"

        print(f"DEBUG: Buscando '{part_term}' para Carro='{model}' Ano='{year}'")
        results = search_products(part_term, model, year)
        
        response = format_stock_response(results)
        return f"{response}\n\n(Dica: No modo Real AI, eu entenderia contextos complexos como 'Serve no g5?')"

    def _process_with_gpt(self, user_text):
        """Chamada real ao GPT (Exemplo de implementação de Function Calling)"""
        # Obs: Para manter o código simples e rodável direto, vamos usar Prompt Chain 
        # em vez de Function Calling estrito nesta versão v1, mas o ideal é FC.
        
        # 1. Prompt para extrair intenção e parametros JSON
        extraction_prompt = f"""
        {self.system_prompt}
        
        TAREFA INTERNA:
        O usuário enviou: "{user_text}"
        
        Identifique se é uma busca de peça.
        Se for, retorne APENAS um JSON no formato: {{"action": "search", "part": "nome da peça", "car": "modelo do carro", "year": "ano"}}
        Se for conversa fiada, retorne {{"action": "chat", "response": "sua resposta"}}
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": extraction_prompt}]
            )
            content = completion.choices[0].message.content
            # Aqui processaria o JSON e chamaria search_products...
            # Como não temos certeza da Key, vou deixar o esqueleto.
            return f"GPT Respondeu (Raw): {content}"
        except Exception as e:
            return f"Erro na API OpenAI: {str(e)}"

