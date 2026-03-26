from parser.utils import limpar_valor
import re


def extrair_numero_posicional(linha):
    numeros = re.findall(r"\d{1,3}(?:\.\d{3})*(?:,\d+)?", linha)
    if len(numeros) >= 3:
        return numeros[2]
    return None


def extrair_numero_final(linha):
    numeros = re.findall(r"\d{1,3}(?:\.\d{3})*(?:,\d+)?", linha)
    if numeros:
        return numeros[-1]
    return None


def parse_light(texto):

    resultado = {
        "DEMANDA_KW": None,
        "CONSUMO_HP_KWH": None,
        "CONSUMO_HFP_KWH": None,
        "TOTAL_RS": None
    }

    linhas = texto.split("\n")

    for linha in linhas:

        linha_lower = linha.lower()

        try:

            # 🔌 DEMANDA (parte de cima da fatura)
            if "demanda ativa" in linha_lower:
                numero = extrair_numero_posicional(linha)
                if numero:
                    resultado["DEMANDA_KW"] = limpar_valor(numero)

            # ⚡ CONSUMO (parte de baixo - medidor)
            elif "energia ativa-kwh ponta" in linha_lower:
                numero = extrair_numero_final(linha)
                if numero:
                    resultado["CONSUMO_HP_KWH"] = limpar_valor(numero)

            elif "energia ativa-kwh fora ponta" in linha_lower:
                numero = extrair_numero_final(linha)
                if numero:
                    resultado["CONSUMO_HFP_KWH"] = limpar_valor(numero)

            # 💰 TOTAL
            elif "total a pagar" in linha_lower:
                numero = extrair_numero_final(linha)
                if numero:
                    resultado["TOTAL_RS"] = limpar_valor(numero)

        except Exception as e:
            print("Erro LIGHT:", e)

    return resultado
