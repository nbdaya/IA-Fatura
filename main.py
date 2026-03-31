import os
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, send_file
)

from werkzeug.utils import secure_filename
import pandas as pd
import pdfplumber

from parser.ai_parser import parse_ai
from parser.detector import detectar_concessionaria


# =========================
# CONFIG
# =========================

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"pdf"}
SECRET_KEY = "supersecret"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
app.secret_key = SECRET_KEY

faturas = []


# =========================
# UTIL
# =========================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def limpar_valor_monetario(valor):
    try:
        valor = str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except:
        return 0


def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor


def tratar_dados(dados):
    if not isinstance(dados, dict):
        return {}

    for chave, valor in dados.items():
        if any(p in chave.lower() for p in ["valor", "custo", "total"]):
            dados[chave] = formatar_moeda(valor)

    return dados


# =========================
# EXTRAÇÃO DE TEXTO
# =========================

def extrair_texto_pdf(caminho):
    texto = ""

    try:
        with pdfplumber.open(caminho) as pdf:
            for page in pdf.pages:
                conteudo = page.extract_text()
                if conteudo:
                    texto += conteudo + "\n"
    except Exception as e:
        print("Erro ao extrair texto:", e)

    return texto.lower()


def extrair_texto(caminho):
    return extrair_texto_pdf(caminho)


# =========================
# EXTRAÇÃO DE DADOS
# =========================

def extrair_dados_fatura(texto):

    dados = parse_ai(texto)
    dados["CONCESSIONARIA"] = detectar_concessionaria(texto)

    dados = tratar_dados(dados)

    return dados


# =========================
# ROTAS
# =========================

@app.route("/")
def splash():
    return render_template("splash.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        session["user_email"] = request.form["email"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", faturas=faturas)


# =========================
# UPLOAD
# =========================

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        files = request.files.getlist("faturas")

        if not files or files[0].filename == "":
            flash("Nenhum arquivo selecionado", "danger")
            return redirect(request.url)

        for file in files:

            if file and allowed_file(file.filename):

                try:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    filename = f"{timestamp}_{filename}"

                    caminho = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(caminho)

                    texto = extrair_texto(caminho)
                    dados = extrair_dados_fatura(texto)

                    faturas.append({
                        "nome_arquivo": filename,
                        "data_upload": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "dados_fatura": dados,
                        "texto_ocr": texto[:2000]
                    })

                except Exception as e:
                    print("Erro:", e)

        flash("Faturas processadas com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# =========================
# RELATÓRIO
# =========================

@app.route("/relatorio/<nome_arquivo>")
def relatorio(nome_arquivo):

    fatura = next((f for f in faturas if f["nome_arquivo"] == nome_arquivo), None)

    if not fatura:
        flash("Arquivo não encontrado.", "danger")
        return redirect(url_for("dashboard"))

    return render_template("relatorio.html", fatura=fatura, texto=fatura.get("texto_ocr", ""))


# =========================
# REMOVER
# =========================

@app.route("/remover/<nome_arquivo>")
def remover(nome_arquivo):

    global faturas
    faturas = [f for f in faturas if f["nome_arquivo"] != nome_arquivo]

    try:
        os.remove(os.path.join(UPLOAD_FOLDER, nome_arquivo))
    except:
        pass

    flash("Arquivo removido.", "success")
    return redirect(url_for("dashboard"))


# =========================
# DASHBOARD GERAL
# =========================

@app.route("/dashboard_geral")
def dashboard_geral():

    dados_list = [f["dados_fatura"] for f in faturas if f.get("dados_fatura")]

    df = pd.DataFrame(dados_list) if dados_list else pd.DataFrame()

    return render_template(
        "dashboard_geral.html",
        tabela=df.to_html(classes="table table-hover", index=False)
    )


# =========================
# GRÁFICOS
# =========================

@app.route("/graficos")
def graficos():

    dados_list = [f["dados_fatura"] for f in faturas if f.get("dados_fatura")]

    if not dados_list:
        return render_template("graficos.html", vazio=True)

    df = pd.DataFrame(dados_list)

    consumo_total = 0
    despesa_total = 0

    if "CONSUMO_HP_KWH" in df.columns:
        consumo_total += pd.to_numeric(df["CONSUMO_HP_KWH"], errors="coerce").fillna(0).sum()

    if "CONSUMO_HFP_KWH" in df.columns:
        consumo_total += pd.to_numeric(df["CONSUMO_HFP_KWH"], errors="coerce").fillna(0).sum()

    if "VALOR_TOTAL" in df.columns:
        despesa_total = df["VALOR_TOTAL"].apply(limpar_valor_monetario).sum()

    return render_template(
        "graficos.html",
        consumo_total=round(consumo_total, 2),
        despesa_total=round(despesa_total, 2),
        vazio=False
    )


# =========================
# EXPORTAR
# =========================

@app.route("/exportar_excel")
def exportar_excel():

    dados_list = [f["dados_fatura"] for f in faturas if f.get("dados_fatura")]

    if not dados_list:
        flash("Nenhum dado disponível.", "warning")
        return redirect(url_for("dashboard_geral"))

    df = pd.DataFrame(dados_list)

    caminho_excel = os.path.join(UPLOAD_FOLDER, "relatorio.xlsx")
    df.to_excel(caminho_excel, index=False)

    return send_file(caminho_excel, as_attachment=True)


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("splash"))


# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

   
