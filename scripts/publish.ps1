# Publish private repository; refuses to overwrite an existing GitHub repo.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Install Git first: winget install --id Git.Git -e" }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "Install GitHub CLI first: winget install --id GitHub.cli -e" }
gh auth status
if ($LASTEXITCODE -ne 0) { throw "Run gh auth login first." }
gh repo view asapacsin/ai-native-engineering 2>$null
if ($LASTEXITCODE -eq 0) { throw "Remote already exists; refusing to create or overwrite it." }
if (-not (Test-Path ".git")) { git init -b main }
git add README.md AGENTS.md .gitignore .github .claude docs scripts tests adapters examples
$changes = git status --porcelain
if ($changes) { git -c user.name="AI Native Repo" -c user.email="ai-native@users.noreply.github.com" commit -m "Initialize reusable AI-native engineering workflow" }
gh repo create asapacsin/ai-native-engineering --private --source . --remote origin --push
if ($LASTEXITCODE -ne 0) { throw "Repository creation/push failed. Check gh output and login." }
Write-Host "Created: https://github.com/asapacsin/ai-native-engineering"
