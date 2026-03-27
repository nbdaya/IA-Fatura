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
- procure a MAIOR quantia em reais associada a pagamento final
- normalmente está no final da fatura

💰 FORMATAÇÃO:
- "R$ 2.336.818,68" → 2336818.68

⚡ DEMANDA:
- 9 MW → 9000

🚫 PROIBIDO:
- retornar 0 se houver qualquer valor na fatura

Se não encontrar claramente, escolha o MAIOR valor monetário da fatura.

Retorne SOMENTE JSON:

{{
  "DEMANDA_KW": numero,
  "CONSUMO_HP_KWH": numero,
  "CONSUMO_HFP_KWH": numero,
  "TOTAL_RS": numero
}}

Texto:
{texto}
"""
