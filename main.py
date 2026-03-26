import os
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, send_file
)

from werkzeug.utils import secure_filename
import pandas as pd
import pdfplumber

from parser.detector import detectar_concessionaria
from parser.factory import get_parser  # ✅ NOVO


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


# =========================
# EXTRAÇÃO DE TEXTO
# =========================

def extrair_texto_pdf(caminho):

    texto = ""

    try:
        with pdfplumber.open(caminho) as pdf:
            for page in pdf.pages:
                conteudo = page.extract_text(x_tolerance=2, y_tolerance=2)
                if conteudo:
                    texto += conteudo + "\n"

    except Exception as e:
        print("Erro ao extrair texto:", e)

    return texto.lower()


def extrair_texto(caminho):
    return extrair_texto_pdf(caminho)


# =========================
# EXTRAÇÃO DE DADOS (🔥 CORRIGIDO)
# =========================

def extrair_dados_fatura(texto):

    # 1️⃣ Detecta concessionária
    concessionaria = detectar_concessionaria(texto)

    print(f"Concessionária detectada: {concessionaria}")

    # 2️⃣ Escolhe parser correto
    parser = get_parser(concessionaria)

    # 3️⃣ Executa parser
    dados = parser(texto)

    # 4️⃣ Adiciona info
    dados["CONCESSIONARIA"] = concessionaria

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

        sucessos = 0
        erros = 0

        for file in files:

            if file and allowed_file(file.filename):

                try:
                    filename = secure_filename(file.filename)

                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    filename = f"{timestamp}_{filename}"

                    caminho = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                    file.save(caminho)

                    texto = extrair_texto(caminho)

                    print("\n==============================")
                    print(f"PROCESSANDO: {filename}")
                    print("==============================")

                    # 🔥 AQUI USA O NOVO FLUXO
                    dados = extrair_dados_fatura(texto)

                    print("DADOS EXTRAÍDOS:", dados)

                    fatura = {
                        "nome_arquivo": filename,
                        "data_upload": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "dados_fatura": dados
                    }

                    faturas.append(fatura)

                    sucessos += 1

                except Exception as e:
                    print(f"Erro ao processar {file.filename}: {e}")
                    erros += 1

            else:
                erros += 1

        if sucessos > 0:
            flash(f"{sucessos} fatura(s) processada(s) com sucesso!", "success")

        if erros > 0:
            flash(f"{erros} arquivo(s) falharam no processamento.", "warning")

        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# =========================
# RESTANTE (igual)
# =========================

@app.route("/relatorio/<nome_arquivo>")
def relatorio(nome_arquivo):

    fatura = next((f for f in faturas if f["nome_arquivo"] == nome_arquivo), None)

    if not fatura:
        flash("Arquivo não encontrado.", "danger")
        return redirect(url_for("dashboard"))

    return render_template(
        "relatorio.html",
        fatura=fatura,
        dados=fatura["dados_fatura"]
    )


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


@app.route("/dashboard_geral")
def dashboard_geral():

    dados_list = [f["dados_fatura"] for f in faturas if f.get("dados_fatura")]

    df = pd.DataFrame(dados_list) if dados_list else pd.DataFrame()

    return render_template(
        "dashboard_geral.html",
        tabela=df.to_html(classes="table table-bordered", index=False),
        df_json=df.to_json(orient="records")
    )


@app.route("/exportar_excel")
def exportar_excel():

    dados_list = [f["dados_fatura"] for f in faturas if f.get("dados_fatura")]

    if not dados_list:
        flash("Nenhum dado disponível.", "warning")
        return redirect(url_for("dashboard_geral"))

    df = pd.DataFrame(dados_list)

    caminho_excel = os.path.join(UPLOAD_FOLDER, "relatorio_consolidado.xlsx")

    df.to_excel(caminho_excel, index=False)

    return send_file(
        caminho_excel,
        as_attachment=True,
        download_name="relatorio_energia.xlsx"
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("splash"))


# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)





