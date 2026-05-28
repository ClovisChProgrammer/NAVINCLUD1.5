$ErrorActionPreference = 'Stop'

$src = Get-Location
$dist = Join-Path $src "_cws_build"
$zip = Join-Path $src "navinclud-cws.zip"

if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
New-Item -ItemType Directory -Path $dist | Out-Null

$files = @(
    "manifest.json"
    "popup.html", "popup.js", "popup.css"
    "background.js", "content.js"
    "wizard.html", "wizard.js"
    "calibrate.html", "calibrate.js"
    "experience.html", "experience.js"
    "icon16.png", "icon48.png", "icon128.png"
)

foreach ($f in $files) {
    if (Test-Path (Join-Path $src $f)) {
        Copy-Item -Path (Join-Path $src $f) -Destination (Join-Path $dist $f)
    } else {
        Write-Warning "Arquivo nao encontrado: $f"
    }
}

$imgDir = Join-Path $dist "images"
New-Item -ItemType Directory -Path $imgDir -Force | Out-Null
$imgSrc = Join-Path $src "images"
if (Test-Path $imgSrc) {
    Get-ChildItem -Path $imgSrc -Filter "*.webp" | Copy-Item -Destination $imgDir
} else {
    Write-Warning "Diretorio images/ nao encontrado"
}

if (Test-Path $zip) { Remove-Item -Force $zip }

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($dist, $zip, [System.IO.Compression.CompressionLevel]::Optimal, $false)

Remove-Item -Recurse -Force $dist

$totalKb = [math]::Round((Get-Item $zip).Length / 1KB, 1)
Write-Host "ZIP criado: $zip ($totalKb KB)"
Write-Host "Conteudo:"
[System.IO.Compression.ZipFile]::OpenRead($zip).Entries | ForEach-Object {
    Write-Host "  $($_.FullName) ($([math]::Round($_.Length/1KB,1)) KB)"
}
