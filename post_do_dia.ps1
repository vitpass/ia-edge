# Roda o "post do dia" do IA Edge via Claude Code headless (Task Scheduler: IAEdge-PostDiario).
# Guarda: se já existe post de hoje em posts\, não roda de novo (idempotente em re-execuções).
$repo = 'C:\Users\vitpa\ia-edge'
$hoje = Get-Date -Format 'yyyy-MM-dd'
New-Item -ItemType Directory -Force -Path (Join-Path $repo 'logs') | Out-Null
$log = Join-Path $repo "logs\post_$hoje.log"

if (Get-ChildItem (Join-Path $repo 'posts') -Filter "$hoje-*.md" -ErrorAction SilentlyContinue) {
    "$(Get-Date -Format u) ja existe post de $hoje, nada a fazer" | Out-File $log -Append -Encoding utf8
    exit 0
}

Set-Location $repo
"$(Get-Date -Format u) iniciando post do dia" | Out-File $log -Append -Encoding utf8
git pull --rebase origin main 2>&1 | Out-File $log -Append -Encoding utf8

& "$env:APPDATA\npm\claude.cmd" -p "post do dia" --dangerously-skip-permissions 2>&1 |
    Out-File $log -Append -Encoding utf8

"$(Get-Date -Format u) fim (exit $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8
exit $LASTEXITCODE
