param(
    [int]$Port = 8000
)

Push-Location (Join-Path $PSScriptRoot "..\backend")
try {
    uvicorn app.main:app --reload --host 0.0.0.0 --port $Port
}
finally {
    Pop-Location
}
