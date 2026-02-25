FROM python:3.10-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivos
COPY . /app

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor porta
EXPOSE 10000

# Rodar aplicação
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000"]
