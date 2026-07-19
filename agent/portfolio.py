# -*- coding: utf-8 -*-
"""Gerencia o track record da carteira teórica (paper trading)."""
import json
from datetime import date
from pathlib import Path

ARQ = Path(__file__).resolve().parent.parent / "data" / "track_record.json"


def carregar() -> dict:
    return json.loads(ARQ.read_text(encoding="utf-8"))


def salvar(tr: dict) -> None:
    ARQ.write_text(json.dumps(tr, ensure_ascii=False, indent=2), encoding="utf-8")


def resumo(tr: dict) -> str:
    """Resumo textual da carteira para injetar nos prompts."""
    pos = ", ".join(
        f"{p['ativo']} ({p['percentual_carteira']:.1f}% @ R${p['preco_referencia']:.2f})"
        for p in tr["posicoes"]
    ) or "100% em caixa"
    ultimo = tr["historico_patrimonio"][-1]
    return (
        f"Patrimônio: R${ultimo['patrimonio']:,.2f} | Caixa: R${tr['caixa']:,.2f} | "
        f"Posições: {pos} | Retorno total: {tr['estatisticas']['retorno_total_pct']:.2f}%"
    )


def aplicar_decisoes(tr: dict, decisoes: list) -> None:
    """Registra as decisões do dia e atualiza posições (modelo simplificado por percentual)."""
    hoje = date.today().isoformat()
    for d in decisoes:
        d["data"] = hoje
        tr["decisoes"].append(d)
        acao = d.get("acao")
        ativo = d.get("ativo", "").upper()
        pct = float(d.get("percentual_carteira") or 0)
        preco = float(d.get("preco_referencia") or 0)
        existente = next((p for p in tr["posicoes"] if p["ativo"].upper() == ativo), None)
        if acao == "comprar" and pct > 0:
            if existente:
                existente["percentual_carteira"] += pct
            else:
                tr["posicoes"].append(
                    {"ativo": ativo, "percentual_carteira": pct, "preco_referencia": preco,
                     "data_entrada": hoje}
                )
        elif acao == "vender" and existente:
            existente["percentual_carteira"] -= pct if pct > 0 else existente["percentual_carteira"]
            if existente["percentual_carteira"] <= 0.01:
                tr["posicoes"].remove(existente)
    # normaliza caixa como o que sobra
    alocado = sum(p["percentual_carteira"] for p in tr["posicoes"])
    ultimo = tr["historico_patrimonio"][-1]["patrimonio"]
    tr["caixa"] = round(ultimo * max(0.0, (100 - alocado)) / 100, 2)


def registrar_patrimonio(tr: dict, patrimonio: float, cdi_acum: float, ibov_acum: float) -> None:
    hoje = date.today().isoformat()
    hist = tr["historico_patrimonio"]
    if hist and hist[-1]["data"] == hoje:
        hist[-1] = {"data": hoje, "patrimonio": patrimonio, "cdi_acum": cdi_acum, "ibov_acum": ibov_acum}
    else:
        hist.append({"data": hoje, "patrimonio": patrimonio, "cdi_acum": cdi_acum, "ibov_acum": ibov_acum})
    ret = (patrimonio / tr["capital_inicial"] - 1) * 100
    tr["estatisticas"]["retorno_total_pct"] = round(ret, 2)
    tr["estatisticas"]["vs_cdi_pct"] = round(ret - cdi_acum, 2)
    tr["estatisticas"]["vs_ibov_pct"] = round(ret - ibov_acum, 2)
