#!/bin/bash
# ───────────────────────────────────────────────
# ONYX Vulnerability Scanner Installer (One-liner)
# Author: zvlrxq-onyx
# GitHub: https://github.com/zvlrxq-onyx/onyx-scanner
# ───────────────────────────────────────────────

INSTALL_DIR="$HOME/onyx-scanner"

echo "🔹 Installing ONYX Vulnerability Scanner..."

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "📁 ONYX directory already exists, updating..."
    git -C "$INSTALL_DIR" pull
else
    git clone https://github.com/zvlrxq-onyx/onyx-scanner.git "$INSTALL_DIR"
fi

# Setup virtual environment
cd "$INSTALL_DIR" || exit
python3 -m venv venv

# Activate venv and install dependencies
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found, installing default dependencies..."
    pip install requests beautifulsoup4 tqdm colorama rich
fi

# Create launcher script
ONYX_BIN="/usr/local/bin/onyx"
sudo tee $ONYX_BIN > /dev/null <<EOF
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
python "$INSTALL_DIR/main.py" "\$@"
EOF
sudo chmod +x $ONYX_BIN

echo "✅ ONYX installed successfully!"
echo "🚀 Run with: onyx"
