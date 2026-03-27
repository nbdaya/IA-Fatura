import os
import json
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_ai(texto):

    try:
        prompt = """
Você é um analista especialista em leitura de faturas de energia elétrica no Brasil.

Interprete a fatura como um humano especialista faria.

EXTRAIA:

- DEMANDA_KW (em kW, converter MW → kW)
- CONSUMO_HP_KWH (ponta)
- CONSUMO_HFP_KWH (fora ponta)
- TOTAL_RS (valor final da fatura)

REGRAS:

- TOTAL_RS = valor FINAL A PAGAR
- Ignore impostos, subtotais e tarifas
- Se houver vários valores, escolha o maior valor final

CONVERSÃO:
- "R$ 2.336.818,68" → 2336818.68

NUNCA:
- retornar 0 se houver valor

Retorne SOMENTE JSON:

{
  "DEMANDA_KW": numero,
  "CONSUMO_HP_KWH": numero,
  "CONSUMO_HFP_KWH": numero,
  "TOTAL_RS": numero
}

FATURA:
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

        # tentativa de parse
        try:
            dados = json.loads(resposta)

        except Exception:
            inicio = resposta.find("{")
            fim = resposta.rfind("}") + 1
            json_limpo = resposta[inicio:fim]
            dados = json.loads(json_limpo)

        # fallback TOTAL
        if not dados.get("TOTAL_RS") or dados["TOTAL_RS"] == 0:
            print("⚠️ fallback TOTAL")

            valores = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', texto)

            if valores:
                valores_convertidos = [
                    float(v.replace('.', '').replace(',', '.'))
                    for v in valores
                ]

                dados["TOTAL_RS"] = max(valores_convertidos)

        return dados

    except Exception as e:
        print("ERRO IA:", e)

        return {
            "DEMANDA_KW": None,
            "CONSUMO_HP_KWH": None,
            "CONSUMO_HFP_KWH": None,
            "TOTAL_RS": None
        }
