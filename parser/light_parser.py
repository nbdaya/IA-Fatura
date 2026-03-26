from parser.utils import limpar_valor
import re


def extrair_valor(linha):
    numeros = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}|\d{1,3}(?:\.\d{3})+", linha)
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

            if "demanda ativa" in linha_lower and resultado["DEMANDA_KW"] is None:
                numero = extrair_valor(linha)
                if numero:
                    resultado["DEMANDA_KW"] = limpar_valor(numero)

            elif "energia ativa kwh hfp" in linha_lower and resultado["CONSUMO_HFP_KWH"] is None:
                numero = extrair_valor(linha)
                if numero:
                    resultado["CONSUMO_HFP_KWH"] = limpar_valor(numero)

            elif "energia ativa kwh hp" in linha_lower and resultado["CONSUMO_HP_KWH"] is None:
                numero = extrair_valor(linha)
                if numero:
                    resultado["CONSUMO_HP_KWH"] = limpar_valor(numero)

            elif "total a pagar" in linha_lower and resultado["TOTAL_RS"] is None:
                numero = extrair_valor(linha)
                if numero:
                    resultado["TOTAL_RS"] = limpar_valor(numero)

        except Exception as e:
            print("Erro LIGHT:", e)

    return resultado
