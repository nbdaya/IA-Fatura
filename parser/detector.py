def detectar_concessionaria(texto):

    texto = texto.upper()

    if "ENEL" in texto:
        return "ENEL"

    if "NEOENERGIA" in texto:
        return "NEOENERGIA"

    if "EQUATORIAL" in texto:
        return "EQUATORIAL"

    if "CPFL" in texto:
        return "CPFL"

    if "ENERGISA" in texto:
        return "ENERGISA"

    if "CEMIG" in texto:
        return "CEMIG"
    if "LIGHT": ["light", "light servicos de eletricidade"] in texto:
        return "LIGHT"

    return "DESCONHECIDA"
