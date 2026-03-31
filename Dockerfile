
CMD # =========================
# BASE
# =========================
FROM python:3.10-slim

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# =========================
# WORKDIR
# =========================
WORKDIR /app

# =========================
# DEPENDÊNCIAS DO SISTEMA
# =========================
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# =========================
# PYTHON DEPENDENCIES (CACHE)
# =========================
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =========================
# COPIAR APP
# =========================
COPY . .

# =========================
# CRIAR USUÁRIO NÃO-ROOT
# =========================
RUN useradd -m appuser

# =========================
# PERMISSÕES (🔥 CORREÇÃO DO ERRO)
# =========================
RUN mkdir -p /app/static/uploads \
    && chown -R appuser:appuser /app

# =========================
# USAR USUÁRIO SEGURO
# =========================
USER appuser

# =========================
# ENV
# =========================
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# =========================
# PORTA
# =========================
EXPOSE 10000

# =========================
# START
# =========================
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000", "--workers", "2", "--threads", "2", "--timeout", "120"]
