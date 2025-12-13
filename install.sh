#!/bin/bash

set -e

echo "🔹 Installing ONYX Vulnerability Scanner..."

INSTALL_DIR="$HOME/onyx-scanner"

# Clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    echo "📁 ONYX directory already exists, updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    git clone https://github.com/zvlrxq-onyx/onyx-scanner.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Python check
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install Python first."
    exit 1
fi

# Virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Create launcher
sudo ln -sf "$INSTALL_DIR/main.py" /usr/local/bin/onyx
sudo chmod +x /usr/local/bin/onyx

echo "✅ ONYX installed successfully!"
echo "🚀 Run with: onyx"
