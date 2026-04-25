#!/bin/bash

echo "Checking system dependencies..."

# wg
if ! command -v wg &> /dev/null; then
    echo "❌ WireGuard or wg-quick are not installed"
    echo "Install them with: sudo pacman -S wireguard wireguard-tools"
    exit 1
fi

# python
if ! command -v python &> /dev/null; then
    echo "❌ Python is missing"
    exit 1
fi

echo "✅ All dependencies OK"

python src/desktop/main.py
