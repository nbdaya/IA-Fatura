import os
import re
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session,
    flash, send_file
)

from werkzeug.utils import secure_filename
import pandas as pd
import PyPDF2

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
SECRET_KEY = 'supersecret'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

# Banco em memória
faturas = []


# =========================
# UTILIDADES
# =========================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def limpar_numero(valor):
    if not valor:
        return None
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return None


# =========================
# EXTRAÇÃO TEXTO PDF
# =========================
def extrair_texto_pdf(caminho):
    texto = ""
    try:
        with open(caminho, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                texto += page.extract_text() or ""
    except Exception as e:
        texto = f"ERRO AO LER PDF: {str(e)}"
    return texto


# =========================
# EXTRAÇÃO GRANDEZAS LIGHT
# =========================
def extrair_dados_fatura(texto):
    resultado = {}

    # Mês
    ref = re.search(r"\b([A-Z]{3}/\d{4})\b", texto)
    resultado["mes"] = ref.group(1) if ref else ""

    # Energia Fora Ponta
    energia_fp = re.search(
        r"Energia Ativa kWh HFP.*?kWh\s+([\d\.,]+)",
        texto,
        re.DOTALL
    )

    # Energia Ponta
    energia_p = re.search(
        r"Energia Ativa kWh HP\s+kWh\s+([\d\.,]+)",
        texto
    )

    # Demanda Medida
    demanda_medida = re.search(
        r"Demanda Ativa-Kw Único.*?([\d\.,]+)\s*$",
        texto,
        re.MULTILINE
    )

    # Demanda Contratada
    demanda_contratada = re.search(
        r"Demanda\s+([\d\.,]+)",
        texto
    )

    energia_fp_val = limpar_numero(energia_fp.group(1)) if energia_fp else None
    energia_p_val = limpar_numero(energia_p.group(1)) if energia_p else None
    demanda_medida_val = limpar_numero(demanda_medida.group(1)) if demanda_medida else None
    demanda_contratada_val = limpar_numero(demanda_contratada.group(1)) if demanda_contratada else None

    resultado["energia_fp_kwh"] = energia_fp_val
    resultado["energia_p_kwh"] = energia_p_val
    resultado["energia_total_kwh"] = (
        (energia_fp_val or 0) + (energia_p_val or 0)
        if energia_fp_val or energia_p_val else None
    )

    resultado["demanda_medida_kw"] = demanda_medida_val
    resultado["demanda_contratada_kw"] = demanda_contratada_val

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


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', faturas=faturas)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':

        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado.', 'danger')
            return redirect(request.url)

        file = request.files['arquivo']

        if file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(caminho)

            texto = extrair_texto_pdf(caminho)
            dados = extrair_dados_fatura(texto)

            fatura = {
                'nome_arquivo': filename,
                'data_upload': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'dados_fatura': dados
            }

            faturas.append(fatura)

            flash('Fatura processada com sucesso!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('upload.html')


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
        flash("Nenhum dado disponível para exportação.", "warning")
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)






