import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_ai(texto):

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": f"""
Extraia os dados desta fatura de energia.

Retorne SOMENTE JSON válido (sem texto antes ou depois):

{{
  "DEMANDA_KW": numero,
  "CONSUMO_HP_KWH": numero,
  "CONSUMO_HFP_KWH": numero,
  "TOTAL_RS": numero
}}

Texto:
{texto}
"""
                }
            ]
        )

        resposta = response.choices[0].message.content.strip()

        print("RESPOSTA IA:", resposta)

        # 🧠 tenta converter direto
        try:
            return json.loads(resposta)
        except:
            # 🔧 tenta limpar texto antes/depois
            inicio = resposta.find("{")
            fim = resposta.rfind("}") + 1
            json_limpo = resposta[inicio:fim]

            return json.loads(json_limpo)

    except Exception as e:
        print("ERRO IA GERAL:", e)

        # ⚠️ NÃO QUEBRA MAIS O SISTEMA
        return {
            "DEMANDA_KW": None,
            "CONSUMO_HP_KWH": None,
            "CONSUMO_HFP_KWH": None,
            "TOTAL_RS": None
        }
