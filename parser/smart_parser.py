from .utils import limpar_valor, extrair_numero_linha


PALAVRAS_CHAVE = {

    "DEMANDA_KW": ["demanda"],

    "CONSUMO_HP_KWH": [
        "ponta"
    ],

    "CONSUMO_HFP_KWH": [
        "fora ponta"
    ],

    "TOTAL_RS": [
        "total a pagar",
        "valor total",
        "total"
    ]
}


def parse_smart(texto):

    resultado = {
        "DEMANDA_KW": None,
        "CONSUMO_HP_KWH": None,
        "CONSUMO_HFP_KWH": None,
        "TOTAL_RS": None
    }

    linhas = texto.split("\n")

    for linha in linhas:

        linha_lower = linha.lower()

        for campo, palavras in PALAVRAS_CHAVE.items():

            for palavra in palavras:

                if palavra in linha_lower:

                    numero = extrair_numero_linha(linha)

                    if numero:
                        resultado[campo] = limpar_valor(numero)

    return resultado
