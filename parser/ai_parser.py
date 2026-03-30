import os
import json
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def normalizar_numero(valor):
    try:
        return round(float(valor), 2)
    except:
        return None


def normalizar_concessionaria(nome):
    if not nome:
        return "DESCONHECIDA"

    nome = nome.lower()

    if "enel" in nome or "ampla" in nome:
        return "ENEL"
    if "light" in nome:
        return "LIGHT"
    if "energisa" in nome:
        return "ENERGISA"
    if "cpfl" in nome:
        return "CPFL"
    if "neoenergia" in nome or "celpe" in nome or "coelba" in nome:
        return "NEOENERGIA"
    if "equatorial" in nome or "celpa" in nome:
        return "EQUATORIAL"
    if "edp" in nome:
        return "EDP"
    if "cemig" in nome:
        return "CEMIG"
    if "copel" in nome:
        return "COPEL"
    if "celesc" in nome:
        return "CELESC"

    return nome.upper()


def parse_ai(texto):
    try:
        prompt = """
Você é um especialista em leitura e interpretação de faturas de energia elétrica no Brasil.

Sua tarefa NÃO é apenas extrair dados.
Você deve interpretar a fatura como um especialista humano faria.

========================
DADOS A EXTRAIR
========================

- DEMANDA_KW
- CONSUMO_HP_KWH
- CONSUMO_HFP_KWH
- TOTAL_RS
- CONCESSIONARIA

========================
REGRAS IMPORTANTES
========================

💰 TOTAL_RS:
- Valor final a pagar
- Pode aparecer como:
  "valor a pagar", "total", "total da fatura"
- Ignore impostos e subtotais
- Se houver vários valores → escolha o MAIOR valor final

⚡ DEMANDA:
- Se estiver em MW → converter para kW (multiplicar por 1000)

🔌 CONSUMO:
- Valores em kWh
- Normalmente inteiros (evitar centavos)

🏢 CONCESSIONARIA:
- Identifique a empresa distribuidora
- Pode estar no topo ou rodapé
- Pode ter nomes diferentes (ex: AMPLA = ENEL)
- Retorne o nome do grupo principal

💰 FORMATAÇÃO:
- "R$ 1.234.567,89" → 1234567.89

🚫 PROIBIDO:
- retornar 0 se houver valor
- inventar dados

========================
SAÍDA
========================

Retorne SOMENTE JSON válido:

{
  "DEMANDA_KW": numero,
  "CONSUMO_HP_KWH": numero,
  "CONSUMO_HFP_KWH": numero,
  "TOTAL_RS": numero,
  "CONCESSIONARIA": "nome"
}

========================
FATURA
========================
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt + texto
                }
            ]
        )

        resposta = response.choices[0].message.content.strip()
        print("RESPOSTA IA:", resposta)

        # 🔧 tentativa de parse
        try:
            dados = json.loads(resposta)
        except Exception:
            inicio = resposta.find("{")
            fim = resposta.rfind("}") + 1
            dados = json.loads(resposta[inicio:fim])

        # 🔥 fallback TOTAL
        if not dados.get("TOTAL_RS") or dados["TOTAL_RS"] == 0:
            print("⚠️ fallback TOTAL")

            valores = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', texto)

            if valores:
                valores_convertidos = [
                    float(v.replace('.', '').replace(',', '.'))
                    for v in valores
                ]
                dados["TOTAL_RS"] = max(valores_convertidos)

        # 🔧 normalização dos números
        dados["DEMANDA_KW"] = normalizar_numero(dados.get("DEMANDA_KW"))
        dados["CONSUMO_HP_KWH"] = normalizar_numero(dados.get("CONSUMO_HP_KWH"))
        dados["CONSUMO_HFP_KWH"] = normalizar_numero(dados.get("CONSUMO_HFP_KWH"))
        dados["TOTAL_RS"] = normalizar_numero(dados.get("TOTAL_RS"))

        # 🔧 normalização da concessionária
        dados["CONCESSIONARIA"] = normalizar_concessionaria(
            dados.get("CONCESSIONARIA")
        )

        return dados

    except Exception as e:
        print("ERRO IA:", e)

        return {
            "DEMANDA_KW": None,
            "CONSUMO_HP_KWH": None,
            "CONSUMO_HFP_KWH": None,
            "TOTAL_RS": None,
            "CONCESSIONARIA": "DESCONHECIDA"
        }
