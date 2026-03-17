import re
from parser.utils import extrair_valor  # reaproveita utils


def parse(texto):

    dados = {}

    dados["DEMANDA_KW"] = extrair_valor([
        r"demanda\s+contratada.*?(\d+[.,]\d+)",
        r"demanda.*?(\d+[.,]\d+)\s*k?w"
    ], texto)

    dados["CONSUMO_HFP_KWH"] = extrair_valor([
        r"fora\s+ponta.*?(\d+[.,]\d+)",
        r"consumo\s+fora\s+ponta.*?(\d+[.,]\d+)"
    ], texto)

    dados["CONSUMO_HP_KWH"] = extrair_valor([
        r"ponta.*?(\d+[.,]\d+)\s*kwh",
        r"consumo\s+ponta.*?(\d+[.,]\d+)"
    ], texto)

    dados["TOTAL_RS"] = extrair_valor([
        r"total\s+a\s+pagar.*?(\d+[.,]\d+)",
        r"valor\s+total.*?(\d+[.,]\d+)"
    ], texto)

    return dados
