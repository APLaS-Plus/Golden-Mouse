# Enable strict error handling
$ErrorActionPreference = "Stop"

Write-Host "Initializing module..."
go mod tidy

# Create dist directory if not exists
if (!(Test-Path "dist")) {
    New-Item -ItemType Directory -Force -Path "dist" | Out-Null
}

Write-Host "Building secure_setup..."
go build -o dist/secure_setup.exe ./cmd/secure_setup

Write-Host "Building check_connectivity..."
go build -o dist/check_connectivity.exe ./cmd/check_connectivity

Write-Host "Running setup with -replace..."
./dist/secure_setup.exe -replace

Write-Host "Running connectivity check..."
./dist/check_connectivity.exe "自检测试"

Write-Host "Done."
