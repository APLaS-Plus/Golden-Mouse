#!/bin/bash
set -e

echo "Initializing module..."
go mod tidy

# Create dist directory if not exists
mkdir -p dist

echo "Building secure_setup..."
go build -o dist/secure_setup ./cmd/secure_setup

echo "Building check_connectivity..."
go build -o dist/check_connectivity ./cmd/check_connectivity

echo "Running setup with -replace..."
./dist/secure_setup -replace

echo "Running connectivity check..."
./dist/check_connectivity "自检测试"

echo "Done."
