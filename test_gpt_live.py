
import os
import sys

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.join(os.getcwd(), 'ruviaro_agent'))

from src.llm_openai import GPTRuviaroBrain

# Chave fornecida pelo usuário (APENAS PARA TESTE LOCAL, NÃO COMMITAR EM PRODUÇÃO)
# A chave da API deve ser definida como uma variável de ambiente (OPENAI_API_KEY)
# antes de executar este script.

def test_gpt():
    print("🧠 Inicializando Cérebro GPT-4o...")
    try:
        brain = GPTRuviaroBrain()
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        return

    print("✅ Cérebro Online. Testando Tool Calling...")
    
    # Cenário 1: Busca de Peça (Deve chamar consultar_estoque)
    msg1 = "Olá, tem amortecedor dianteiro pro Gol G5?"
    print(f"\n👤 User: {msg1}")
    resp1 = brain.process_message(msg1)
    print(f"🤖 Beto (GPT): {resp1}")

    # Cenário 2: Conversa Humana / Negociação (Deve responder como Persona)
    msg2 = "Caramba, tá meio salgado esse preço. Não consegue melhorar pra fechar agora?"
    print(f"\n👤 User: {msg2}")
    resp2 = brain.process_message(msg2)
    print(f"🤖 Beto (GPT): {resp2}")

    # Cenário 3: Item Inexistente (Deve chamar consultar_catalogo_externo - Loma)
    msg3 = "E tem o amortecedor Cofap traseiro?"
    print(f"\n👤 User: {msg3}")
    resp3 = brain.process_message(msg3)
    print(f"🤖 Beto (GPT): {resp3}")

if __name__ == "__main__":
    test_gpt()
