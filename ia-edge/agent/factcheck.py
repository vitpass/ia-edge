# -*- coding: utf-8 -*-
"""Agente verificador de fatos: checa cada afirmação factual do post contra a web
antes da publicação. Corrige o que estiver errado, corta o que não se sustenta."""
from agent.generate import chamar_claude, extrair_json

SISTEMA_FACTCHECK = """Você é o verificador de fatos da IA Edge, um blog financeiro
brasileiro. Você recebe o rascunho de um post e sua missão é impedir que qualquer
informação errada seja publicada.

PROCESSO:
1. Liste mentalmente todas as afirmações verificáveis do texto: números (cotações,
   taxas, percentuais, datas), atribuições ("o BTG recomendou X"), eventos ("a empresa
   anunciou Y"), rankings e superlativos ("a mais valiosa do mundo").
2. Verifique na web as afirmações mais importantes e as mais arriscadas (priorize
   números e atribuições a instituições). Use fontes primárias quando possível
   (Banco Central, B3, CVM, relatório do próprio banco, veículo de imprensa de primeira linha).
3. Classifique cada afirmação checada: CONFIRMADA, CORRIGIDA (com o valor certo) ou
   NÃO VERIFICÁVEL.
4. Reescreva o texto aplicando as correções. Afirmações NÃO VERIFICÁVEIS importantes
   devem ser suavizadas ("segundo apurado até o fechamento deste post...") ou removidas.
   Nunca deixe passar um número que você não conseguiu confirmar e que seja central
   para o argumento.

Mantenha estrutura, tom e extensão do texto. Não acrescente conteúdo novo além do
necessário para as correções.

FORMATO DE SAÍDA — responda APENAS com JSON válido:
{
  "corpo_markdown": "texto integral corrigido",
  "relatorio": [
    {"afirmacao": "...", "status": "confirmada|corrigida|nao_verificavel", "obs": "fonte ou correção"}
  ]
}"""


def verificar(corpo_markdown: str, modelo: str) -> tuple[str, list]:
    prompt = "Verifique e corrija o post abaixo:\n\n" + corpo_markdown
    try:
        resposta = chamar_claude(prompt, SISTEMA_FACTCHECK, modelo, max_tokens=6000,
                                 web_search=True, max_buscas=8)
        dados = extrair_json(resposta)
        corpo = dados.get("corpo_markdown") or corpo_markdown
        return corpo, dados.get("relatorio", [])
    except Exception as e:
        print(f"[factcheck] falhou ({e}); mantendo texto original")
        return corpo_markdown, []
