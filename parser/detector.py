def detectar_concessionaria(texto):

    texto = texto.lower()

    mapa = {
        "LIGHT": ["light", "light servicos de eletricidade"],
        "EQUATORIAL": ["equatorial"],
        "NEOENERGIA": ["neoenergia", "coelba", "celpe", "cosern"],
        "ENEL": ["enel", "ampla"],
    }

    for nome, palavras in mapa.items():
        for palavra in palavras:
            if palavra in texto:
                return nome

    return "DESCONHECIDA"
