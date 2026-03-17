import re


def extrair_valor(patterns, texto):

    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)

        if match:
            try:
                valor = match.group(1)
                valor = valor.replace(".", "").replace(",", ".")
                return float(valor)
            except:
                continue

    return None
