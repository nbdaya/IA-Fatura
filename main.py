import os
import re
import gc
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, send_file
)
from werkzeug.utils import secure_filename
import pandas as pd

# PDF texto
import PyPDF2

# OCR fallback
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# Caminho do Tesseract no container
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
SECRET_KEY = 'supersecret'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

faturas = []

# =========================
# UTIL
# =========================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# =========================
# EXTRAÇÃO PDF TEXTO
# =========================

def extrair_texto_pdf(caminho):
    texto = ""
    try:
        with open(caminho, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[:1]:
                texto += page.extract_text() or ""
    except:
        pass
    return texto


# =========================
# OCR FALLBACK
# =========================

def extrair_texto_ocr(caminho):
    texto_extraido = ""
    try:
        paginas = convert_from_path(
            caminho,
            dpi=120,
            first_page=1,
            last_page=1
        )

        for pagina in paginas:
            texto_extraido += pytesseract.image_to_string(
                pagina,
                lang="por",
                config="--oem 1 --psm 6",
                timeout=60
            )
            pagina.close()

        del paginas
        gc.collect()

    except Exception as e:
        texto_extraido = f"OCR_ERRO: {str(e)}"

    return texto_extraido


# =========================
# EXTRAÇÃO HÍBRIDA
# =========================

def extrair_texto(caminho):
    texto = extrair_texto_pdf(caminho)

    if len(texto.strip()) < 100:
        texto = extrair_texto_ocr(caminho)

    return texto


# =========================
# EXTRAÇÃO DE DADOS
# =========================

def extrair_valor(label, texto):
    padrao = rf"{label}.*?([\d\.,]+)"
    match = re.search(padrao, texto, re.IGNORECASE)
    return match.group(1) if match else ""


def extrair_dados_fatura(texto):
    resultado = {}

    codigo = re.search(r"\b\d{9}\b", texto)
    resultado['CODIGO_INSTALACAO'] = codigo.group(0) if codigo else ""

    ref = re.search(r"\b([A-Z]{3}/\d{4})\b", texto)
    resultado['MES_REFERENCIA'] = ref.group(1) if ref else ""

    resultado['DEMANDA_KW'] = extrair_valor("Demanda", texto)
    resultado['CONSUMO_HFP_KWH'] = extrair_valor("HFP", texto)
    resultado['CONSUMO_HP_KWH'] = extrair_valor("HP", texto)
    resultado['TOTAL_RS'] = extrair_valor("Total a Pagar", texto)

    return resultado


# =========================
# ROTAS
# =========================

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
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for('login'))
    return render_template('cadastro.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', faturas=faturas)


@app.route('/upload', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':

        file = request.files.get('arquivo')

        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(caminho)

            texto = extrair_texto(caminho)
            dados = extrair_dados_fatura(texto)

            fatura = {
                'nome_arquivo': filename,
                'data_upload': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'dados_fatura': dados
            }

            faturas.append(fatura)

            flash('Upload realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('upload.html')


@app.route('/relatorio/<nome_arquivo>')
def relatorio(nome_arquivo):
    fatura = next((f for f in faturas if f['nome_arquivo'] == nome_arquivo), None)

    if not fatura:
        flash("Arquivo não encontrado.", "danger")
        return redirect(url_for('dashboard'))

    return render_template(
        "relatorio.html",
        fatura=fatura,
        dados=fatura['dados_fatura']
    )


@app.route('/remover/<nome_arquivo>')
def remover(nome_arquivo):
    global faturas

    faturas = [f for f in faturas if f['nome_arquivo'] != nome_arquivo]

    try:
        os.remove(os.path.join(UPLOAD_FOLDER, nome_arquivo))
    except:
        pass

    flash("Arquivo removido.", "success")
    return redirect(url_for('dashboard'))


@app.route('/dashboard_geral')
def dashboard_geral():

    dados_list = [f['dados_fatura'] for f in faturas if f.get('dados_fatura')]
    df = pd.DataFrame(dados_list) if dados_list else pd.DataFrame()

    return render_template(
        'dashboard_geral.html',
        tabela=df.to_html(classes='table table-bordered', index=False),
        df_json=df.to_json(orient='records')
    )


@app.route('/exportar_excel')
def exportar_excel():

    dados_list = [f['dados_fatura'] for f in faturas if f.get('dados_fatura')]

    if not dados_list:
        flash("Nenhum dado disponível.", "warning")
        return redirect(url_for('dashboard_geral'))

    df = pd.DataFrame(dados_list)

    caminho_excel = os.path.join(UPLOAD_FOLDER, "relatorio_consolidado.xlsx")
    df.to_excel(caminho_excel, index=False)

    return send_file(
        caminho_excel,
        as_attachment=True,
        download_name="relatorio_energia.xlsx"
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('splash'))


# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)







