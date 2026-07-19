# -*- coding: utf-8 -*-
"""Chama a API da Anthropic com web search para gerar o post do dia."""
import json
import os
import re
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"


def _extrair_json(texto: str) -> dict:
    """Extrai o primeiro objeto JSON válido da resposta."""
    texto = re.sub(r"```(json)?", "", texto).strip()
    inicio = texto.find("{")
    if inicio == -1:
        raise ValueError("Resposta sem JSON")
    # tenta decodificar do primeiro '{' até o final, recuando se necessário
    for fim in range(len(texto), inicio, -1):
        try:
            return json.loads(texto[inicio:fim])
        except json.JSONDecodeError:
            continue
    raise ValueError("JSON inválido na resposta do modelo")


def gerar_post(prompt_usuario: str, sistema: str, modelo: str, max_tokens: int = 4000) -> dict:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    corpo = {
        "model": modelo,
        "max_tokens": max_tokens,
        "system": sistema,
        "messages": [{"role": "user", "content": prompt_usuario}],
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    texto = "\n".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return _extrair_json(texto)


def revisar_post(corpo_markdown: str, modelo: str) -> str:
    """Segunda passada: melhora clareza e naturalidade do texto (sem web search)."""
    api_key = os.environ["ANTHROPIC_API_KEY"]
    corpo = {
        "model": modelo,
        "max_tokens": 4000,
        "system": (
            "Você é editor de um blog financeiro brasileiro. Reescreva o texto mantendo TODOS os "
            "fatos, números e a estrutura de subtítulos, mas melhorando fluidez, cortando "
            "redundâncias e simplificando jargões. Responda APENAS com o markdown revisado."
        ),
        "messages": [{"role": "user", "content": corpo_markdown}],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        revisado = "\n".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        ).strip()
        return revisado or corpo_markdown
    except Exception:
        return corpo_markdown  # em caso de falha, publica a versão original
