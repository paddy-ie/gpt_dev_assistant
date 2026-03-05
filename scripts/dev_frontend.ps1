param(
    [int]$Port = 3000
)

Push-Location (Join-Path $PSScriptRoot "..\web")
try {
    npm run dev -- --port $Port
}
finally {
    Pop-Location
}
