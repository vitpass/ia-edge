# -*- coding: utf-8 -*-
"""Pipeline diário da IA Edge.
1. Descobre o tipo de post do dia (agenda editorial)
2. Gera o post via Claude + web search (dados reais)
3. Passa o texto por revisão editorial
4. Aplica decisões na carteira e atualiza o track record
5. Salva o post em markdown com front matter
6. Constrói o site (build.py) com SEO + GEO
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from agent import generate, portfolio, prompts  # noqa: E402

CONFIG = json.loads((RAIZ / "data" / "config.json").read_text(encoding="utf-8"))


def slugify(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:80]


def montar_prompt(tipo: str, tr: dict) -> str:
    base = prompts.PROMPTS[tipo]
    decisoes_recentes = json.dumps(tr["decisoes"][-10:], ensure_ascii=False)
    historico = json.dumps(tr["historico_patrimonio"][-30:], ensure_ascii=False)
    temas = ", ".join(
        p.stem.split("-", 3)[-1] for p in sorted((RAIZ / "posts").glob("*.md"))[-30:]
    ) or "nenhum"
    prognosticos = json.dumps(
        [d for d in tr["decisoes"] if d.get("acao") == "prognostico"][-6:], ensure_ascii=False
    )
    return base.format(
        bancos=", ".join(CONFIG["bancos_monitorados"]),
        carteira=portfolio.resumo(tr),
        decisoes_recentes=decisoes_recentes,
        historico=historico,
        temas_cobertos=temas,
        prognosticos_anteriores=prognosticos,
    )


def salvar_post(post: dict, tipo: str) -> Path:
    hoje = date.today().isoformat()
    slug = post.get("slug") or slugify(post["titulo"])
    slug = slugify(slug)
    caminho = RAIZ / "posts" / f"{hoje}-{slug}.md"
    fm = {
        "titulo": post["titulo"],
        "data": hoje,
        "slug": f"{hoje}-{slug}",
        "tipo": tipo,
        "meta_description": post.get("meta_description", "")[:155],
        "palavras_chave": post.get("palavras_chave", []),
    }
    conteudo = "---\n" + json.dumps(fm, ensure_ascii=False, indent=2) + "\n---\n\n" + post["corpo_markdown"]
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def main() -> None:
    dia_semana = str(datetime.now().weekday() + 1 if datetime.now().weekday() < 6 else 0)
    # weekday(): seg=0..dom=6 -> agenda usa 1..6 e 0=domingo
    tipo = CONFIG["agenda_editorial"].get(dia_semana, "novidades")
    print(f"[IA Edge] Post do dia: {tipo}")

    tr = portfolio.carregar()
    prompt = montar_prompt(tipo, tr)

    post = generate.gerar_post(
        prompt, prompts.SISTEMA, CONFIG["modelo"], CONFIG["max_tokens_post"]
    )
    print(f"[IA Edge] Gerado: {post['titulo']}")

    post["corpo_markdown"] = generate.revisar_post(post["corpo_markdown"], CONFIG["modelo"])
    print("[IA Edge] Revisão editorial concluída")

    decisoes = post.get("decisoes_carteira") or []
    if decisoes:
        portfolio.aplicar_decisoes(tr, decisoes)
        print(f"[IA Edge] {len(decisoes)} decisão(ões) aplicada(s) à carteira")
    portfolio.salvar(tr)

    caminho = salvar_post(post, tipo)
    print(f"[IA Edge] Post salvo em {caminho}")

    # build do site
    from site_builder import build  # type: ignore
    build.main()
    print("[IA Edge] Site construído. Pronto para deploy.")


if __name__ == "__main__":
    main()
