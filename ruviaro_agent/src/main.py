
import sys
import os
import time

# Adiciona o diretório raiz (iaruviaro) ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Tenta importar o Cérebro Real (OpenAI + Memória)
try:
    from ruviaro_agent.src.llm_openai import GPTRuviaroBrain
    BRAIN_TYPE = "GPT-4o (Beto)"
except ImportError:
    from ruviaro_agent.src.llm_mock import MockRuviaroBrain
    BRAIN_TYPE = "Mock (Regras)"

def main():
    print("="*50)
    print(f"🤖 RUVIARO AUTO PEÇAS - ATENDIMENTO ({BRAIN_TYPE})")
    print("="*50)
    
    # ID simulado de telefone para testar memória
    phone_id = "5555999999999"
    
    if BRAIN_TYPE == "GPT-4o (Beto)":
        agent = GPTRuviaroBrain(sender_id=phone_id)
    else:
        agent = MockRuviaroBrain()
        
    print(f"Simulando cliente: {phone_id}")
    print("Ruviaro: Opa! Ruviaro na escuta. Pode falar.")
    print("(Digite 'sair' para encerrar)")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nVocê: ")
            
            if user_input.lower() in ['sair', 'exit', 'tchau']:
                print("\nRuviaro: Falou patrão, qualquer coisa grita. Abraço!")
                break
            
            if not user_input.strip():
                continue
            
            print("Thinking...", end='\r')
            response = agent.process_message(user_input)
            
            # Simula delay humano
            time.sleep(1) # Rápido no console para não irritar, mas existe
            
            print(f"\nRuviaro: {response}")
            
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print(f"\nErro no sistema: {e}")

if __name__ == "__main__":
    main()
