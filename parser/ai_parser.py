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
Você é um especialista em contas de energia elétrica brasileiras.

Extraia os seguintes dados com precisão:

- DEMANDA_KW → em kW (se estiver em MW, multiplicar por 1000)
- CONSUMO_HP_KWH → consumo ponta (kWh)
- CONSUMO_HFP_KWH → consumo fora ponta (kWh)
- TOTAL_RS → valor total da fatura

REGRAS IMPORTANTES:

1. O TOTAL_RS deve ser o valor final da conta, normalmente identificado como:
   - "Valor a pagar"
   - "Total a pagar"
   - "Valor total"
   - "Total da fatura"

2. IGNORE:
   - subtotais
   - impostos isolados
   - tarifas individuais
   - valores unitários

3. CONVERSÃO DE VALORES:
   - "R$ 2.336.818,68" → 2336818.68
   - "2.336.818,68" → 2336818.68
   - usar ponto como decimal final

4. DEMANDA:
   - se aparecer "9 MW", retornar 9000
   - se aparecer "9.000 kW", retornar 9000

5. NUNCA:
   - retornar 0 se houver valor na fatura
   - confundir subtotal com total final

6. PRIORIDADE:
   - sempre escolher o valor FINAL a pagar

Retorne SOMENTE JSON válido (sem texto antes ou depois):

{{
  "DEMANDA_KW": numero,
  "CONSUMO_HP_KWH": numero,
  "CONSUMO_HFP_KWH": numero,
  "TOTAL_RS": numero
}}

Texto da fatura:
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

        return {
            "DEMANDA_KW": None,
            "CONSUMO_HP_KWH": None,
            "CONSUMO_HFP_KWH": None,
            "TOTAL_RS": None
        }
