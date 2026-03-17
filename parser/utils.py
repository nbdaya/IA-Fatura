import re


def limpar_valor(valor_str):
    try:
        valor = valor_str.replace(".", "").replace(",", ".")
        return float(valor)
    except:
        return None


def extrair_valor(patterns, texto):

    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)

        if match:
            valor = limpar_valor(match.group(1))
            if valor is not None:
                return valor

    return None


def extrair_numero_linha(texto, palavra_chave):
    linhas = texto.split("\n")

    for linha in linhas:
        if palavra_chave in linha:
            numeros = re.findall(r"\d+[.,]?\d*", linha)
            if numeros:
                return limpar_valor(numeros[0])

    return None
