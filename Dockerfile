# Imagem base
FROM python:3.10-slim

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas requirements primeiro (melhor cache)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar restante da aplicação
COPY . .

# Criar usuário não-root (mais seguro)
RUN useradd -m appuser
USER appuser

# Porta da aplicação
EXPOSE 10000

# Variáveis de ambiente úteis
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Rodar aplicação com mais performance
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000", "--workers", "2", "--threads", "2", "--timeout", "120"]
