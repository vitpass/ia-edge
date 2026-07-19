# -*- coding: utf-8 -*-
"""Cliente da API da Anthropic. Função genérica usada por todos os agentes."""
import json
import os
import re
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"


def chamar_claude(prompt: str, sistema: str, modelo: str, max_tokens: int = 4000,
                  web_search: bool = False, max_buscas: int = 8) -> str:
    """Chama a API e retorna o texto concatenado da resposta."""
    corpo = {
        "model": modelo,
        "max_tokens": max_tokens,
        "system": sistema,
        "messages": [{"role": "user", "content": prompt}],
    }
    if web_search:
        corpo["tools"] = [{"type": "web_search_20250305", "name": "web_search",
                           "max_uses": max_buscas}]
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return "\n".join(b.get("text", "") for b in data.get("content", [])
                     if b.get("type") == "text")


def extrair_json(texto: str) -> dict:
    """Extrai o primeiro objeto JSON válido de uma resposta."""
    texto = re.sub(r"```(json)?", "", texto).strip()
    inicio = texto.find("{")
    if inicio == -1:
        raise ValueError("Resposta sem JSON")
    for fim in range(len(texto), inicio, -1):
        try:
            return json.loads(texto[inicio:fim])
        except json.JSONDecodeError:
            continue
    raise ValueError("JSON inválido na resposta do modelo")


def gerar_post(prompt_usuario: str, sistema: str, modelo: str, max_tokens: int = 4000) -> dict:
    texto = chamar_claude(prompt_usuario, sistema, modelo, max_tokens,
                          web_search=True, max_buscas=8)
    return extrair_json(texto)
