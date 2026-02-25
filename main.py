import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import re
import pandas as pd

# 🔴 OCR DESATIVADO TEMPORARIAMENTE
# from PyPDF2 import PdfReader
# from pdf2image import convert_from_path
# import pytesseract
# from PIL import Image
# import cv2
# import numpy as np
# from fuzzywuzzy import process

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
SECRET_KEY = 'supersecret'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

# Banco em memória
faturas = []

CAMPOS_EXTRAIR = [
    'CÓDIGO DA INSTALAÇÃO',
    'NOME DA CONCESSIONÁRIA',
    'REF:MÊS/ANO',
    'DEMANDA',
    'ENERGIA ATIVA HFP',
    'ENERGIA ATIVA HP',
    'TOTAL A PAGAR'
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 🔴 FUNÇÕES DE OCR DESATIVADAS
"""
def preprocess_image(path):
    ...

def extrair_texto_ocr(path):
    ...
"""

def extrair_dados_fatura(texto):
    resultado = {}
    codigo_instalacao = re.search(r"\b\d{9}\b", texto)
    resultado['CÓDIGO DA INSTALAÇÃO'] = codigo_instalacao.group(0) if codigo_instalacao else ""
    resultado['NOME DA CONCESSIONÁRIA'] = "LIGHT" if "LIGHT" in texto.upper() else "NÃO IDENTIFICADO"
    ref_mes_ano = re.search(r"\b([A-Z]{3}/\d{4})\b", texto)
    resultado['REF:MÊS/ANO'] = ref_mes_ano.group(1) if ref_mes_ano else ""
    resultado['DEMANDA'] = ""
    resultado['ENERGIA ATIVA HFP'] = ""
    resultado['ENERGIA ATIVA HP'] = ""
    resultado['TOTAL A PAGAR'] = ""
    return resultado


@app.route('/')
def splash():
    return render_template('splash.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user_email'] = request.form['email']
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('cadastro.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', faturas=faturas)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado', 'danger')
            return redirect(request.url)

        file = request.files['arquivo']

        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(caminho)

            # 🔴 OCR DESATIVADO TEMPORARIAMENTE
            texto = "OCR DESATIVADO"
            dados = {}

            fatura = {
                'nome_arquivo': filename,
                'caminho_arquivo': caminho,
                'data_upload': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'texto_extraido': texto,
                'dados_fatura': dados
            }

            faturas.append(fatura)
            flash('Upload realizado!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('upload.html')


@app.route('/relatorio/<nome_arquivo>')
def relatorio(nome_arquivo):
    fatura = next((f for f in faturas if f['nome_arquivo'] == nome_arquivo), None)
    if fatura:
        return render_template('relatorio.html', fatura=fatura, texto=fatura['texto_extraido'], dados=fatura['dados_fatura'])
    else:
        flash('Arquivo não encontrado.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/remover/<nome_arquivo>')
def remover(nome_arquivo):
    global faturas
    faturas = [f for f in faturas if f['nome_arquivo'] != nome_arquivo]
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, nome_arquivo))
    except Exception:
        pass
    flash('Arquivo removido.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('splash'))


@app.route('/dashboard_geral')
def dashboard_geral():
    dados_list = [f['dados_fatura'] for f in faturas if f.get('dados_fatura')]
    df = pd.DataFrame(dados_list) if dados_list else pd.DataFrame()
    return render_template(
        'dashboard_geral.html',
        tabela=df.to_html(classes='table table-bordered', index=False),
        df_json=df.to_json(orient='records')
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)








