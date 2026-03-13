import re

def limpar_valor(valor):

    valor = valor.replace(".", "").replace(",", ".")

    try:
        return float(valor)
    except:
        return None


def extrair_numero_linha(linha):

    numeros = re.findall(r"\d[\d\.,]*", linha)

    if numeros:
        return numeros[-1]

    return None
