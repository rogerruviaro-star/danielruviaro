
import os
import sys
import traceback

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.join(os.getcwd(), 'ruviaro_agent'))

print(f"DEBUG: CWD: {os.getcwd()}")
print(f"DEBUG: Sys Path: {sys.path}")

try:
    from src.llm_openai import GPTRuviaroBrain
except ImportError as e:
    print(f"❌ Import Error: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ General Error during import: {e}")
    traceback.print_exc()
    sys.exit(1)

# Configuração para usar a chave da API do OpenAI de uma variável de ambiente
# Certifique-se de que OPENAI_API_KEY esteja definida no seu ambiente
# Ex: export OPENAI_API_KEY="sua_chave_aqui"
# Se estiver usando a biblioteca openai diretamente, você pode inicializar assim:
# from openai import OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_sales_persona():
    print("🧠 Inicializando Cérebro GPT-4o (Sales Edition)...")
    try:
        brain = GPTRuviaroBrain()
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        traceback.print_exc()
        return

    print("✅ Cérebro Online. Testando Persona Gaúcho e Vendedor...\n")
    
    # Teste 1: Identidade Gaúcha
    msg1 = "E aí tchê, tudo tranquilo?"
    print(f"👤 User: {msg1}")
    resp1 = brain.process_message(msg1)
    print(f"🤖 Beto: {resp1}\n")

    # Teste 2: Objeção de Preço (Mental Trigger: Valor/Parcelamento)
    msg2 = "Bah, 400 reais nessa pastilha? Achei meio salgado parceiro."
    print(f"👤 User: {msg2}")
    resp2 = brain.process_message(msg2)
    print(f"🤖 Beto: {resp2}\n")

    # Teste 3: Estoque Virtual (Simulando falta de peça)
    msg3 = "Cara, preciso muito do farol esquerdo do Fusca Itamar 94. Mas tem que ser pra hoje. Tu não tem aí né?"
    print(f"👤 User: {msg3}")
    resp3 = brain.process_message(msg3)
    print(f"🤖 Beto: {resp3}\n")

if __name__ == "__main__":
    test_sales_persona()
