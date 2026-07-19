# IA Edge — blog 100% autônomo

Uma IA que administra uma carteira teórica de R$ 100 mil, analisa as carteiras dos grandes
bancos brasileiros, faz prognósticos e publica um post por dia — sem intervenção humana.

## Como funciona

```
GitHub Actions (cron diário 07:00 BRT)
        │
        ▼
agent/run.py ──► Claude API + web search (dados reais do dia)
        │            │
        │            ├─ gera o post do dia (agenda editorial por dia da semana)
        │            └─ segunda passada: revisão editorial do texto
        ▼
posts/*.md  +  data/track_record.json (decisões aplicadas)
        │
        ▼
site_builder/build.py ──► HTML + sitemap.xml + feed.xml + robots.txt + llms.txt (GEO)
        │
        ▼
Deploy automático no GitHub Pages ──► iaedge.com.br
```

## Setup (uma única vez, ~10 minutos)

1. **Crie um repositório no GitHub** e envie estes arquivos:
   ```bash
   git init && git add -A && git commit -m "inicio"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/ia-edge.git
   git push -u origin main
   ```

2. **Adicione a chave da API**: no repositório, vá em
   `Settings → Secrets and variables → Actions → New repository secret`
   - Nome: `ANTHROPIC_API_KEY`
   - Valor: sua chave em https://console.anthropic.com

3. **Ative o GitHub Pages**: `Settings → Pages → Source: GitHub Actions`

4. **Aponte o domínio**: no seu provedor de domínio, crie um registro:
   - `CNAME` de `www` → `SEU_USUARIO.github.io`
   - Registros `A` do apex (`iaedge.com.br`) → IPs do GitHub Pages
     (185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153)
   - Edite o arquivo `CNAME` deste repo se o domínio for outro.
   - Em `Settings → Pages`, preencha o Custom domain e ative "Enforce HTTPS".

5. **Teste agora**: aba `Actions → IA Edge — post diário → Run workflow`.
   O primeiro post real será gerado, commitado e publicado.

A partir daí, roda sozinho todo dia às 07:00 (Brasília).

## Ajustes rápidos

- **Domínio, nome, capital inicial, bancos monitorados**: `data/config.json`
- **Agenda editorial** (o que sai em cada dia da semana): `data/config.json`
- **Tom e regras de escrita/SEO**: `agent/prompts.py`
- **Visual do site**: `site_builder/static/style.css`

## Custo estimado

~2 chamadas de API por dia (geração + revisão) com web search.
Ordem de grandeza: poucos dólares por mês no Sonnet. GitHub Actions e Pages: grátis.

## Avisos importantes

- A carteira é **teórica** (paper trading) e o site deixa isso explícito em todas as páginas.
- O conteúdo é educacional e **não é recomendação de investimento** (relevante para CVM).
- Recomendo acompanhar os primeiros posts para calibrar os prompts ao seu gosto.
