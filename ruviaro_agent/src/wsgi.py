import os
import sys

# Adiciona o diretório atual ao path para importar os módulos corretamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from webhook_server import app

if __name__ == "__main__":
    app.run()
