import os
import json
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_ai(texto):

    try:
        # 🧠 PROMPT SEGURO (SEM f-string)
        prompt = """
Você é um especialista em contas de energia elétrica brasileiras.

Sua principal tarefa é encontrar o VALOR TOTAL FINAL da fatura.

Extraia:

- DEMANDA_KW (em kW)
- CONSUMO_HP_KWH (kWh)
- CONSUMO_HFP_KWH (kWh)
- TOTAL_RS (valor final da conta)

⚠️ REGRA MAIS IMPORTANTE:

O TOTAL_RS é o valor FINAL A PAGAR.

Ele geralmente aparece como:

- "Valor a pagar"
- "Total a pagar"
- "Valor total da fatura"
- "Total da fatura"
- "TOTAL R$"
- "VALOR TOTAL"

🚫 IGNORE COMPLETAMENTE:
- impostos
- ICMS
- PIS/COFINS
- subtotais
- tarifas unitárias

🔎 ESTRATÉGIA:
- procure a MAIOR quantia em reais associada ao pagamento final
- normalmente está no final da fatura

💰 FORMATAÇÃO:
- "R$ 2.336.818,68" → 2336818.68

⚡ DEMANDA:
- 9 MW → 9000

🚫 PROIBIDO:
- retornar 0 se houver qualquer valor na fatura

Se não encontrar claramente, escolha o MAIOR valor monetário da fatura.

Retorne SOMENTE JSON:

{
  "DEMANDA_KW": numero,
  "CONSUMO_HP_KWH": numero,
  "CONSUMO_HFP_KWH": numero,
  "TOTAL_RS": numero
}

Texto da fatura:
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

        # 🧠 tentativa direta
        try:
            dados = json.loads(resposta)

        except Exception:
            # 🔧 limpeza de resposta
            inicio = resposta.find("{")
            fim = resposta.rfind("}") + 1
            json_limpo = resposta[inicio:fim]

            dados = json.loads(json_limpo)

        # 🔥 FALLBACK INTELIGENTE PARA TOTAL_RS
        if not dados.get("TOTAL_RS") or dados["TOTAL_RS"] == 0:
            print("⚠️ IA não encontrou TOTAL, aplicando fallback...")

            valores = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', texto)

            if valores:
                valores_convertidos = [
                    float(v.replace('.', '').replace(',', '.'))
                    for v in valores
                ]

                maior_valor = max(valores_convertidos)
                print("💰 TOTAL via fallback:", maior_valor)

                dados["TOTAL_RS"] = maior_valor

        return dados

    except Exception as e:
        print("ERRO IA GERAL:", e)

        return {
            "DEMANDA_KW": None,
            "CONSUMO_HP_KWH": None,
            "CONSUMO_HFP_KWH": None,
            "TOTAL_RS": None
        }
