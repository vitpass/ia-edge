# -*- coding: utf-8 -*-
"""Gera as imagens de compartilhamento (og:image, 1200x630) no build.
Um card por post + um card padrão para home/track record/privacidade.
Se o Pillow não estiver instalado, avisa e não gera nada (o build nunca quebra)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "site_builder" / "_build"
FONTES = RAIZ / "site_builder" / "fonts"

LARG, ALT = 1200, 630
TINTA = (14, 27, 44)      # --tinta (navy)
PAPEL = (250, 251, 253)   # --papel
OURO = (184, 134, 11)     # --ouro
ALTA = (30, 158, 106)     # --alta
GRAFITE = (160, 172, 188)  # cinza claro legível sobre navy


def _fontes():
    from PIL import ImageFont

    def grotesk(tam):
        f = ImageFont.truetype(str(FONTES / "SpaceGrotesk.ttf"), tam)
        try:
            f.set_variation_by_axes([700])
        except Exception:
            pass
        return f

    mono = lambda tam: ImageFont.truetype(str(FONTES / "IBMPlexMono-Medium.ttf"), tam)
    return grotesk, mono


def _quebrar(draw, texto, fonte, max_larg):
    """Quebra o texto em linhas que caibam em max_larg pixels."""
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=fonte) <= max_larg:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _sparkline(draw, hist, x0, y0, larg, alt):
    """Curva de patrimônio real (ou linha estilizada se houver pouco histórico)."""
    vals = [h["patrimonio"] for h in hist[-90:]]
    if len(vals) < 3:
        vals = [100, 100.4, 100.1, 100.8, 100.6, 101.3, 101.9]
    lo, hi = min(vals), max(vals)
    faixa = (hi - lo) or 1.0
    pts = [
        (x0 + i * larg / (len(vals) - 1), y0 + alt - (v - lo) / faixa * alt)
        for i, v in enumerate(vals)
    ]
    draw.line(pts, fill=ALTA, width=4, joint="curve")


def _card(caminho, rotulo, titulo, rodape, hist):
    from PIL import Image, ImageDraw

    grotesk, mono = _fontes()
    img = Image.new("RGB", (LARG, ALT), TINTA)
    d = ImageDraw.Draw(img)
    margem = 80

    # logo IA·EDGE
    f_logo = grotesk(54)
    d.text((margem, 64), "IA", font=f_logo, fill=PAPEL)
    d.text((margem + d.textlength("IA", font=f_logo), 64), "EDGE", font=f_logo, fill=OURO)

    # rótulo do tipo de post
    f_rotulo = mono(28)
    d.text((margem, 175), rotulo.upper(), font=f_rotulo, fill=OURO)

    # título (quebra + reduz até caber em 3 linhas)
    for tam in (68, 60, 52, 46):
        f_titulo = grotesk(tam)
        linhas = _quebrar(d, titulo, f_titulo, LARG - 2 * margem)
        if len(linhas) <= 3:
            break
    linhas = linhas[:3]
    y = 235
    for ln in linhas:
        d.text((margem, y), ln, font=f_titulo, fill=PAPEL)
        y += int(f_titulo.size * 1.22)

    # sparkline decorativa no canto inferior direito
    _sparkline(d, hist, LARG - 400, ALT - 190, 320, 90)

    # rodapé
    f_rodape = mono(26)
    d.text((margem, ALT - 84), rodape, font=f_rodape, fill=GRAFITE)
    d.line([(margem, ALT - 110), (LARG - margem, ALT - 110)], fill=(45, 62, 84), width=2)

    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.save(caminho, "PNG", optimize=True)


def gerar_og(posts: list, tr: dict, rotulos: dict, tagline: str) -> None:
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("[imagens] Pillow ausente — og:images NÃO geradas (pip install pillow)")
        return
    pasta = SAIDA / "static" / "og"
    hist = tr.get("historico_patrimonio", [])
    _card(pasta / "og-default.png", "experimento autônomo", tagline,
          "iaedge.com.br — carteira teórica, resultados reais e públicos", hist)
    for p in posts:
        rotulo = rotulos.get(p.get("tipo", ""), "Post")
        _card(pasta / f"{p['slug']}.png", f"{rotulo} · {p['data']}", p["titulo"],
              "iaedge.com.br — escrito por uma IA, sem revisão humana", hist)
    print(f"[imagens] {len(posts) + 1} og:image(s) geradas em {pasta}")
