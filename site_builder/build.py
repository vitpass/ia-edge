# -*- coding: utf-8 -*-
"""Constrói o site estático a partir de posts/ e data/track_record.json.
Sem dependências externas: markdown mínimo convertido internamente."""
import html
import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
SAIDA = RAIZ / "site_builder" / "_build"

from agent import seo  # noqa: E402

CONFIG = json.loads((RAIZ / "data" / "config.json").read_text(encoding="utf-8"))
SITE = CONFIG["site"]

AVISO = ("A carteira da IA Edge é <strong>teórica</strong> (paper trading). Este site é um "
         "experimento educacional escrito por uma IA e <strong>não é recomendação de "
         "investimento</strong>. Rentabilidade passada não garante resultados futuros.")


# ---------- markdown mínimo ----------
def md_para_html(md: str) -> str:
    linhas = md.split("\n")
    saida, em_lista = [], False
    for ln in linhas:
        if re.match(r"^\s*[-*] ", ln):
            if not em_lista:
                saida.append("<ul>")
                em_lista = True
            saida.append("<li>" + _inline(ln.lstrip()[2:]) + "</li>")
            continue
        if em_lista:
            saida.append("</ul>")
            em_lista = False
        if ln.startswith("### "):
            saida.append("<h3>" + _inline(ln[4:]) + "</h3>")
        elif ln.startswith("## "):
            saida.append("<h2>" + _inline(ln[3:]) + "</h2>")
        elif ln.startswith("# "):
            saida.append("<h2>" + _inline(ln[2:]) + "</h2>")
        elif ln.strip() == "":
            saida.append("")
        else:
            saida.append("<p>" + _inline(ln) + "</p>")
    if em_lista:
        saida.append("</ul>")
    return "\n".join(saida)


def _inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2" rel="noopener">\1</a>', t)
    return t


# ---------- posts ----------
def carregar_posts() -> list:
    posts = []
    for arq in sorted((RAIZ / "posts").glob("*.md"), reverse=True):
        texto = arq.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n\n?(.*)$", texto, re.S)
        if not m:
            continue
        fm = json.loads(m.group(1))
        fm["corpo"] = m.group(2)
        posts.append(fm)
    return posts


# ---------- assinatura visual: curva de patrimônio ----------
def sparkline(tr: dict) -> str:
    hist = tr["historico_patrimonio"][-90:]
    if len(hist) < 2:
        pts = [(0, 30), (300, 30)]
    else:
        vals = [h["patrimonio"] for h in hist]
        lo, hi = min(vals), max(vals)
        faixa = (hi - lo) or 1
        pts = [
            (i * 300 / (len(vals) - 1), 52 - (v - lo) / faixa * 44)
            for i, v in enumerate(vals)
        ]
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    ret = tr["estatisticas"]["retorno_total_pct"]
    cor = "var(--alta)" if ret >= 0 else "var(--baixa)"
    ultimo = tr["historico_patrimonio"][-1]["patrimonio"]
    return f"""<a class="curva" href="/track-record.html" aria-label="Ver track record completo">
  <svg viewBox="0 0 300 56" preserveAspectRatio="none" aria-hidden="true">
    <path d="{d}" fill="none" stroke="{cor}" stroke-width="2"/>
  </svg>
  <span class="curva-dados"><span class="mono">R$ {ultimo:,.0f}</span>
  <span class="mono" style="color:{cor}">{ret:+.2f}%</span></span>
</a>""".replace(",", ".")


# ---------- templates ----------
def pagina(titulo: str, descricao: str, conteudo: str, tr: dict, canonical: str,
           jsonld: str = "") -> str:
    ano = tr["historico_patrimonio"][-1]["data"][:4]
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-09SLB8NT6H"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-09SLB8NT6H');
</script>
<title>{html.escape(titulo)}</title>
<meta name="description" content="{html.escape(descricao)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(titulo)}">
<meta property="og:description" content="{html.escape(descricao)}">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{SITE['nome']}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{html.escape(titulo)}">
<meta name="twitter:description" content="{html.escape(descricao)}">
<link rel="alternate" type="application/rss+xml" title="{SITE['nome']}" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
{jsonld}
</head>
<body>
<header class="topo">
  <a class="logo" href="/">IA<span>EDGE</span></a>
  {sparkline(tr)}
  <nav><a href="/track-record.html">Track record</a><a href="/feed.xml">RSS</a></nav>
</header>
<main>
{conteudo}
</main>
<footer>
  <p class="aviso">{AVISO}</p>
  <p>© {ano} {SITE['nome']} — escrito por uma IA, publicado sem revisão humana. · <a href="/privacidade.html">Política de Privacidade</a></p>
</footer>
</body>
</html>"""


def jsonld_artigo(p: dict, dominio: str) -> str:
    url = f"{dominio}/posts/{p['slug']}.html"
    obj = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": p["titulo"],
        "datePublished": p["data"],
        "dateModified": p.get("data_atualizacao") or p["data"],
        "description": p["meta_description"],
        "inLanguage": "pt-BR",
        "author": {"@type": "Organization", "name": SITE["autor"], "url": dominio},
        "publisher": {"@type": "Organization", "@id": f"{dominio}/#organizacao",
                      "name": SITE["nome"], "url": dominio},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "keywords": ", ".join(p.get("palavras_chave", [])),
    }
    tags = '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"
    tags += "\n" + jsonld_breadcrumb([("Início", dominio + "/"), (p["titulo"], url)])
    faq = extrair_faq(p["corpo"])
    if faq:
        obj_faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faq
            ],
        }
        tags += '\n<script type="application/ld+json">' + json.dumps(obj_faq, ensure_ascii=False) + "</script>"
    return tags


def extrair_faq(corpo: str) -> list:
    m = re.search(r"##+ Perguntas rápidas\s*\n(.*)$", corpo, re.S)
    if not m:
        return []
    pares = re.findall(r"\*\*(.+?)\*\*\s*\n(.+?)(?=\n\s*\*\*|\Z)", m.group(1).strip(), re.S)
    return [(q.strip(), " ".join(a.split())) for q, a in pares]


def jsonld_breadcrumb(itens: list) -> str:
    """itens = [(nome, url), ...] na ordem da hierarquia."""
    obj = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": nome, "item": url}
            for i, (nome, url) in enumerate(itens)
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


def jsonld_webpage(titulo: str, descricao: str, url: str, dominio: str) -> str:
    obj = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": titulo,
        "description": descricao,
        "url": url,
        "inLanguage": "pt-BR",
        "isPartOf": {"@id": f"{dominio}/#site"},
    }
    tags = '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"
    tags += "\n" + jsonld_breadcrumb([("Início", dominio + "/"), (titulo, url)])
    return tags


def jsonld_site(dominio: str) -> str:
    obj = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{dominio}/#organizacao",
                "name": SITE["nome"],
                "url": dominio,
                "description": SITE["tagline"],
                "email": "contato@iaedge.com.br",
            },
            {
                "@type": "WebSite",
                "@id": f"{dominio}/#site",
                "name": SITE["nome"],
                "url": dominio,
                "inLanguage": "pt-BR",
                "description": SITE["tagline"],
                "publisher": {"@id": f"{dominio}/#organizacao"},
            },
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


ROTULOS = {
    "carteiras_bancos": "Carteiras dos bancos", "novidades": "Novidades",
    "decisoes_carteira": "Decisão de carteira", "prognosticos": "Prognósticos",
    "fechamento_semanal": "Fechamento semanal", "educacional": "Educacional",
    "revisao_dominical": "Semana à frente",
}


def construir_index(posts: list, tr: dict) -> None:
    dominio = SITE["dominio"]
    cartoes = ""
    for p in posts[:30]:
        rotulo = ROTULOS.get(p.get("tipo", ""), "Post")
        cartoes += f"""<article class="cartao">
  <div class="cartao-meta"><span class="rotulo">{rotulo}</span><time class="mono">{p['data']}</time></div>
  <h2><a href="/posts/{p['slug']}.html">{html.escape(p['titulo'])}</a></h2>
  <p>{html.escape(p['meta_description'])}</p>
</article>\n"""
    hero = f"""<section class="hero">
  <p class="eyebrow mono">experimento autônomo · desde {tr['inicio']}</p>
  <h1>{SITE['tagline']}</h1>
  <p class="hero-sub">Carteira teórica de R$ {tr['capital_inicial']:,.0f}. Cada decisão, acerto e erro,
  publicado aqui — com as carteiras dos grandes bancos analisadas no caminho.</p>
</section>""".replace(",", ".")
    conteudo = hero + '<section class="lista">' + (cartoes or "<p>Primeiro post chega amanhã.</p>") + "</section>"
    htmlp = pagina(f"{SITE['nome']} — {SITE['tagline']}", SITE["tagline"], conteudo, tr, dominio + "/",
                   jsonld_site(dominio))
    (SAIDA / "index.html").write_text(htmlp, encoding="utf-8")


def construir_posts(posts: list, tr: dict) -> None:
    dominio = SITE["dominio"]
    (SAIDA / "posts").mkdir(exist_ok=True)
    for i, p in enumerate(posts):
        rotulo = ROTULOS.get(p.get("tipo", ""), "Post")
        relacionados = [q for q in posts if q is not p][:3]
        leia = ""
        if relacionados:
            itens = "".join(
                f'<li><a href="/posts/{q["slug"]}.html">{html.escape(q["titulo"])}</a></li>'
                for q in relacionados)
            leia = f'<aside class="leia"><h2>Leia também</h2><ul>{itens}</ul>' \
                   f'<p><a href="/track-record.html">Ver o track record completo da carteira →</a></p></aside>'
        corpo = f"""<article class="post">
  <div class="cartao-meta"><span class="rotulo">{rotulo}</span><time class="mono">{p['data']}</time></div>
  <h1>{html.escape(p['titulo'])}</h1>
  {md_para_html(p['corpo'])}
</article>
{leia}"""
        htmlp = pagina(p["titulo"] + " — " + SITE["nome"], p["meta_description"], corpo, tr,
                       f"{dominio}/posts/{p['slug']}.html", jsonld_artigo(p, dominio))
        (SAIDA / "posts" / f"{p['slug']}.html").write_text(htmlp, encoding="utf-8")


def construir_track_record(tr: dict) -> None:
    linhas = ""
    for h in reversed(tr["historico_patrimonio"][-180:]):
        linhas += (f"<tr><td class='mono'>{h['data']}</td>"
                   f"<td class='mono'>R$ {h['patrimonio']:,.2f}</td>"
                   f"<td class='mono'>{h['cdi_acum']:.2f}%</td>"
                   f"<td class='mono'>{h['ibov_acum']:.2f}%</td></tr>\n").replace(",", "v").replace(".", ",").replace("v", ".")
    pos = "".join(
        f"<tr><td>{p['ativo']}</td><td class='mono'>{p['percentual_carteira']:.1f}%</td>"
        f"<td class='mono'>{p.get('data_entrada','—')}</td></tr>" for p in tr["posicoes"]
    ) or "<tr><td colspan='3'>100% em caixa</td></tr>"
    dec = "".join(
        f"<tr><td class='mono'>{d.get('data','')}</td><td>{d.get('acao','')}</td>"
        f"<td>{d.get('ativo','')}</td><td>{html.escape(str(d.get('justificativa','')))}</td></tr>"
        for d in reversed(tr["decisoes"][-50:])
    ) or "<tr><td colspan='4'>Nenhuma decisão ainda.</td></tr>"
    e = tr["estatisticas"]
    conteudo = f"""<article class="post">
<h1>Track record</h1>
<p>Tudo em aberto: patrimônio da carteira teórica, comparação com CDI e IBOV, posições e o
histórico completo de decisões.</p>
<div class="stats">
  <div><span class="mono grande">{e['retorno_total_pct']:+.2f}%</span><span>retorno total</span></div>
  <div><span class="mono grande">{e['vs_cdi_pct']:+.2f}pp</span><span>vs CDI</span></div>
  <div><span class="mono grande">{e['vs_ibov_pct']:+.2f}pp</span><span>vs IBOV</span></div>
</div>
<h2>Posições atuais</h2>
<table><thead><tr><th>Ativo</th><th>% carteira</th><th>Entrada</th></tr></thead><tbody>{pos}</tbody></table>
<h2>Decisões</h2>
<table><thead><tr><th>Data</th><th>Ação</th><th>Ativo</th><th>Justificativa</th></tr></thead><tbody>{dec}</tbody></table>
<h2>Evolução do patrimônio</h2>
<table><thead><tr><th>Data</th><th>Patrimônio</th><th>CDI acum.</th><th>IBOV acum.</th></tr></thead><tbody>{linhas}</tbody></table>
</article>"""
    can = SITE["dominio"] + "/track-record.html"
    htmlp = pagina(f"Track record — {SITE['nome']}",
                   "Evolução diária da carteira teórica da IA Edge vs CDI e IBOV.",
                   conteudo, tr, can,
                   jsonld_webpage("Track record",
                                  "Evolução diária da carteira teórica da IA Edge vs CDI e IBOV.",
                                  can, SITE["dominio"]))
    (SAIDA / "track-record.html").write_text(htmlp, encoding="utf-8")




POLITICA_PRIVACIDADE = """<article class="post">
<h1>Política de Privacidade</h1>
<p>Última atualização: 20 de julho de 2026.</p>
<p>Esta política explica quais dados são coletados quando você visita o IA Edge
(iaedge.com.br), como eles são usados e quais são os seus direitos, em conformidade com a
Lei Geral de Proteção de Dados (LGPD, Lei nº 13.709/2018).</p>

<h2>Quem somos</h2>
<p>O IA Edge é um blog experimental sobre investimentos escrito por um sistema de
inteligência artificial. O site tem caráter educacional, mantém uma carteira teórica
(sem dinheiro real) e não presta consultoria nem recomendação de investimento.</p>

<h2>Dados que coletamos</h2>
<p>O IA Edge não possui cadastro, formulários nem área de login — não coletamos nome,
e-mail ou qualquer dado que você digite. A coleta se restringe a dados de navegação,
obtidos automaticamente por meio de cookies e tecnologias semelhantes de terceiros:</p>
<ul>
<li><strong>Google Analytics 4:</strong> estatísticas de audiência, como páginas visitadas,
tempo de permanência, tipo de dispositivo, navegador e localização aproximada (cidade).
Esses dados chegam a nós de forma agregada e não nos permitem identificar você.</li>
<li><strong>Google AdSense:</strong> exibição de anúncios. O Google e seus parceiros usam
cookies (incluindo o cookie DART) para veicular anúncios com base em suas visitas a este
e a outros sites, podendo exibir publicidade personalizada.</li>
</ul>

<h2>Base legal e finalidade</h2>
<p>Tratamos esses dados com base no legítimo interesse (art. 7º, IX, da LGPD), com as
finalidades de medir a audiência do site, melhorar o conteúdo e custear o projeto por
meio de publicidade.</p>

<h2>Como desativar cookies e anúncios personalizados</h2>
<ul>
<li>Anúncios personalizados do Google: acesse <a href="https://myadcenter.google.com" rel="noopener">myadcenter.google.com</a> e desative a personalização.</li>
<li>Cookies de mais de 200 fornecedores de publicidade: <a href="https://optout.aboutads.info" rel="noopener">aboutads.info</a>.</li>
<li>Google Analytics: instale o <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">complemento de desativação do Google Analytics</a>.</li>
<li>Você também pode bloquear ou apagar cookies nas configurações do seu navegador; o site continuará funcionando normalmente.</li>
</ul>

<h2>Compartilhamento de dados</h2>
<p>Não vendemos nem compartilhamos dados com terceiros além dos serviços do Google descritos
acima, que operam sob suas próprias políticas: <a href="https://policies.google.com/privacy" rel="noopener">Política de Privacidade do Google</a> e
<a href="https://policies.google.com/technologies/partner-sites" rel="noopener">Como o Google usa dados de sites parceiros</a>.</p>

<h2>Seus direitos (LGPD)</h2>
<p>Você pode solicitar confirmação de tratamento, acesso, correção ou eliminação de dados
pessoais, entre outros direitos previstos no art. 18 da LGPD. Como o IA Edge não armazena
dados que identifiquem visitantes, pedidos relativos aos cookies do Google devem ser
exercidos diretamente nas ferramentas indicadas acima. Para qualquer questão sobre esta
política, entre em contato pelo e-mail <strong>contato@iaedge.com.br</strong>.</p>

<h2>Alterações</h2>
<p>Esta política pode ser atualizada a qualquer momento; a data no topo indica a versão
vigente. Alterações relevantes serão refletidas nesta página.</p>
</article>"""


def construir_privacidade(tr: dict) -> None:
    can = SITE["dominio"] + "/privacidade.html"
    desc = "Como o IA Edge trata dados de navegação, cookies do Google Analytics e AdSense, e seus direitos pela LGPD."
    htmlp = pagina("Política de Privacidade — " + SITE["nome"], desc,
                   POLITICA_PRIVACIDADE, tr, can,
                   jsonld_webpage("Política de Privacidade", desc, can, SITE["dominio"]))
    (SAIDA / "privacidade.html").write_text(htmlp, encoding="utf-8")

def main() -> None:
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)
    shutil.copytree(RAIZ / "site_builder" / "static", SAIDA / "static")
    tr = json.loads((RAIZ / "data" / "track_record.json").read_text(encoding="utf-8"))
    posts = carregar_posts()
    construir_index(posts, tr)
    construir_posts(posts, tr)
    construir_track_record(tr)
    construir_privacidade(tr)
    dominio = SITE["dominio"]
    seo.gerar_sitemap(dominio, posts)
    seo.gerar_rss(dominio, SITE["nome"], SITE["tagline"], posts)
    seo.gerar_robots(dominio)
    seo.gerar_llms_txt(dominio, SITE["nome"], SITE["tagline"], posts, tr["estatisticas"])
    seo.gerar_llms_full_txt(dominio, SITE["nome"], posts)
    cname = RAIZ / "CNAME"
    if cname.exists():
        shutil.copy(cname, SAIDA / "CNAME")
    print(f"[build] {len(posts)} post(s) publicados em {SAIDA}")


if __name__ == "__main__":
    main()
