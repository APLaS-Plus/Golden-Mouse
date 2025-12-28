#!/bin/bash
set -e

echo "Compiling API Server..."
go build -o secure_api_server cmd/api_server/main.go

echo "Starting service on port 58080..."
echo "Press Ctrl+C to stop"
./secure_api_server
