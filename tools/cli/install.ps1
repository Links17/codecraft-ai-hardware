$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "../..")
Push-Location $repo
try {
    $codecraftRustVersion = rustc -vV
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect Rust compiler" }
    $codecraftHostTarget = ($codecraftRustVersion | Select-String '^host: ').Line -replace '^host: ', ''
    if (-not $codecraftHostTarget) { throw "Cannot determine Rust host target" }
    cargo build --release --locked --package codecraft --target-dir .codecraft/cargo --target $codecraftHostTarget
    if ($LASTEXITCODE -ne 0) { throw "CodeCraft build failed" }
    $destination = if ($env:CODECRAFT_BIN_DIR) { $env:CODECRAFT_BIN_DIR } else { Join-Path $env:LOCALAPPDATA "CodeCraft/bin" }
    New-Item -ItemType Directory -Force $destination | Out-Null
    Copy-Item ".codecraft/cargo/$codecraftHostTarget/release/codecraft.exe" (Join-Path $destination "codecraft.exe")
    Write-Output "Installed CodeCraft in $destination. Add this directory to PATH."
} finally { Pop-Location }
