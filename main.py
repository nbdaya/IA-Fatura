import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import cv2
import numpy as np
from fuzzywuzzy import process

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
SECRET_KEY = 'supersecret'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

# Simulando um "banco" de faturas em memória
faturas = []

CAMPOS = [
    'concessionária', 'nome', 'unidade', 'código da instalação', 'data de emissão',
    'vencimento', 'valor total', 'consumo', 'kwh', 'ponta', 'fora ponta',
    'demanda contratada', 'leitura atual', 'leitura anterior', 'tarifa', 'classe',
    'medidor', 'energia reativa', 'grupo de consumo', 'número do medidor'
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)[1]
    img = cv2.medianBlur(img, 3)
    return Image.fromarray(img)

def extrair_texto_ocr(path):
    ext = path.lower().split('.')[-1]
    if ext == 'pdf':
        # 1. PDF digital (texto)
        try:
            reader = PdfReader(path)
            texto_pdf = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    texto_pdf += page_text + "\n"
            if texto_pdf.strip():
                return texto_pdf
        except Exception as e:
            print("Erro PDF digital:", e)
        # 2. PDF escaneado (imagem)
        try:
            from pdf2image import convert_from_path
            paginas = convert_from_path(path)
            texto_total = ''
            for pag in paginas:
                tmp = pag.convert('L')
                texto_total += pytesseract.image_to_string(tmp, lang='por+eng', config='--psm 6 --oem 3') + '\n'
            return texto_total
        except Exception as err:
            print("Erro PDF escaneado:", err)
            return "PDF escaneado não pôde ser processado (Poppler ausente?)."
    else:
        img = preprocess_image(path)
        return pytesseract.image_to_string(img, lang='por+eng', config='--psm 6 --oem 3')

def extrair_dados_fatura(texto):
    resultado = {}
    linhas = texto.lower().split('\n')
    for campo in CAMPOS:
        achou, score = process.extractOne(campo, linhas)
        if score > 65:
            resultado[campo.title()] = achou
    return resultado if resultado else None

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
            fatura = {
                'nome_arquivo': filename,
                'caminho_arquivo': caminho,
                'data_upload': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'texto_extraido': None,
                'dados_fatura': None
            }
            faturas.append(fatura)
            flash('Upload realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('upload.html')

@app.route('/relatorio/<nome_arquivo>')
def relatorio(nome_arquivo):
    fatura = next((f for f in faturas if f['nome_arquivo'] == nome_arquivo), None)
    if fatura:
        if not fatura.get('texto_extraido'):
            texto = extrair_texto_ocr(fatura['caminho_arquivo'])
            fatura['texto_extraido'] = texto
            fatura['dados_fatura'] = extrair_dados_fatura(texto)
        texto = fatura['texto_extraido']
        dados = fatura['dados_fatura']
        return render_template('relatorio.html', fatura=fatura, texto=texto)
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

if __name__ == "__main__":
    app.run(debug=True)








