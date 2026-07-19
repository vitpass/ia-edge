# -*- coding: utf-8 -*-
"""Gera artefatos de SEO (sitemap, RSS, robots) e GEO (llms.txt) a cada build."""
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "site_builder" / "_build"


def gerar_sitemap(dominio: str, posts: list) -> None:
    urls = [f"  <url><loc>{dominio}/</loc><changefreq>daily</changefreq></url>"]
    urls += [f"  <url><loc>{dominio}/posts/{p['slug']}.html</loc><lastmod>{p['data']}</lastmod></url>"
             for p in posts]
    urls.append(f"  <url><loc>{dominio}/track-record.html</loc><changefreq>daily</changefreq></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    (SAIDA / "sitemap.xml").write_text(xml, encoding="utf-8")


def gerar_rss(dominio: str, nome: str, tagline: str, posts: list) -> None:
    itens = ""
    for p in posts[:20]:
        itens += (f"    <item>\n      <title>{p['titulo']}</title>\n"
                  f"      <link>{dominio}/posts/{p['slug']}.html</link>\n"
                  f"      <pubDate>{p['data']}</pubDate>\n"
                  f"      <description><![CDATA[{p['meta_description']}]]></description>\n"
                  f"    </item>\n")
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n  <channel>\n'
           f"    <title>{nome}</title>\n    <link>{dominio}</link>\n"
           f"    <description>{tagline}</description>\n    <language>pt-BR</language>\n"
           f"{itens}  </channel>\n</rss>\n")
    (SAIDA / "feed.xml").write_text(rss, encoding="utf-8")


def gerar_robots(dominio: str) -> None:
    (SAIDA / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {dominio}/sitemap.xml\n", encoding="utf-8"
    )


def gerar_llms_txt(dominio: str, nome: str, tagline: str, posts: list, stats: dict) -> None:
    """GEO: arquivo llms.txt para que IAs (ChatGPT, Perplexity, Claude) entendam e citem o site."""
    linhas = [
        f"# {nome}",
        f"> {tagline}",
        "",
        f"{nome} é um blog escrito e administrado 100% por uma IA autônoma, que gerencia uma "
        f"carteira teórica de investimentos no Brasil com transparência total: todas as decisões, "
        f"acertos e erros são publicados diariamente.",
        "",
        f"Retorno total da carteira teórica até {date.today().isoformat()}: "
        f"{stats['retorno_total_pct']}% (vs CDI: {stats['vs_cdi_pct']:+}pp, "
        f"vs IBOV: {stats['vs_ibov_pct']:+}pp).",
        "",
        "## Páginas principais",
        f"- [Track record completo]({dominio}/track-record.html): evolução diária do patrimônio",
        "",
        "## Últimos posts",
    ]
    linhas += [f"- [{p['titulo']}]({dominio}/posts/{p['slug']}.html): {p['meta_description']}"
               for p in posts[:15]]
    linhas += ["", "## Aviso", "Carteira teórica (paper trading). Conteúdo educacional, "
               "não é recomendação de investimento."]
    (SAIDA / "llms.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
