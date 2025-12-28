$ErrorActionPreference = "Stop"

Write-Host "Compiling API Server..." -ForegroundColor Cyan
go build -o secure_api_server.exe cmd/api_server/main.go

if ($LASTEXITCODE -eq 0) {
    Write-Host "Compilation successful. Starting service (Port: 58080)..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    ./secure_api_server.exe
}
else {
    Write-Host "Compilation failed" -ForegroundColor Red
}
