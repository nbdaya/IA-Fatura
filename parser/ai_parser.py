import os
import json
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_ai(texto):

    try:
        # 🧠 PROMPT SEGURO (SEM f-string)
       prompt = """
Você é um analista especialista em leitura de faturas de energia elétrica no Brasil.

Sua tarefa é interpretar o documento como um humano especialista faria.

⚠️ IMPORTANTE:
As faturas podem variar de formato, concessionária e layout.

Você deve identificar os dados pelo CONTEXTO, não apenas por palavras exatas.

========================
DADOS A EXTRAIR
========================

1. DEMANDA_KW
- Valor de demanda contratada ou medida
- Pode estar em kW ou MW (se estiver em MW, converter para kW multiplicando por 1000)

2. CONSUMO_HP_KWH
- Consumo em horário de ponta

3. CONSUMO_HFP_KWH
- Consumo fora de ponta

4. TOTAL_RS
- Valor final da fatura (valor total a pagar)

========================
COMO ENCONTRAR OS DADOS
========================

TOTAL_RS:
- É o valor final a ser pago
- Geralmente aparece no final do documento
- Pode estar como:
  "valor a pagar", "total", "total da fatura"
- Ignore impostos e subtotais
- Se houver vários valores, escolha o mais alto associado ao pagamento final

CONSUMOS:
- Procure por tabelas de consumo
- Diferencie ponta e fora ponta pelo contexto

DEMANDA:
- Pode aparecer como:
  "demanda contratada", "demanda medida"
- Converter MW → kW se necessário

========================
REGRAS DE CONVERSÃO
========================

- "R$ 1.234.567,89" → 1234567.89
- Sempre retornar números (float ou int)
- Nunca retornar texto
- Nunca retornar 0 se existir valor

========================
VALIDAÇÃO (PENSAMENTO)
========================

Antes de responder, verifique:

- O TOTAL_RS é plausível?
- Não é imposto ou subtotal?
- É o maior valor relevante?

========================
SAÍDA
========================

Retorne SOMENTE JSON válido:

{
  "DEMANDA_KW": numero,
  "CONSUMO_HP_KWH": numero,
  "CONSUMO_HFP_KWH": numero,
  "TOTAL_RS": numero
}

========================
FATURA
========================
"""
