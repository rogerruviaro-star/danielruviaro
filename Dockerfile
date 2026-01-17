FROM python:3.9-slim

# Instala dependências do sistema (necessário para áudio/ffmpeg se for usar)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY . .

# Expõe a porta do Flask
EXPOSE 5000

# Comando para rodar com Gunicorn (Produção)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "ruviaro_agent.src.webhook_server:app"]
