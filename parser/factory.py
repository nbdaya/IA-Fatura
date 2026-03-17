from parser.smart_parser import parse_smart
from parser.light_parser import parse as parse_light


def get_parser(concessionaria):

    if concessionaria == "LIGHT":
        return parse_light

    # futuros:
    # if concessionaria == "ENEL":
    #     return parse_enel

    return parse_smart
