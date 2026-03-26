from parser.light_parser import parse_light
from parser.smart_parser import parse_smart


def get_parser(concessionaria):

    if concessionaria == "LIGHT":
        return parse_light

    # fallback genérico
    return parse_smart
