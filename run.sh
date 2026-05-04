#!/bin/bash

echo "Checking system dependencies..."

# wg
if ! command -v wg &> /dev/null; then
    echo "❌ WireGuard or wg-quick are not installed"
    echo "Install them with: sudo pacman -S wireguard wireguard-tools"
    exit 1
fi

if ! command -v nmcli &> /dev/null; then
    echo "❌ NetworkManager is not installed"
    echo "Install: ssudo pacman -S networkmanager"
    exit 1
fi

if ! nmcli general status &> /dev/null; then
    echo "❌ NetworkManager is not running"
    echo "Start it: sudo systemctl enable --now NetworkManager"
    exit 1
fi

# python
if ! command -v python &> /dev/null; then
    echo "❌ Python is missing"
    exit 1
fi

echo "✅ All dependencies OK"

export PYTHONPATH=$(pwd)/src
python src/desktop/main.py

