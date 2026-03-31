FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar app
COPY . .

# Criar usuário (FIX)
RUN adduser --disabled-password --gecos "" appuser

# Permissões
RUN mkdir -p /app/static/uploads \
    && chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=10000

EXPOSE 10000

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000", "--workers", "2", "--threads", "2", "--timeout", "120"]
