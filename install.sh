#!/usr/bin/env bash

set -e

echo "[+] Installing ONYX Vulnerability Scanner"

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "[-] Python3 not found. Please install Python 3.9+"
  exit 1
fi

# Clone repo
INSTALL_DIR="$HOME/.onyx"
if [ -d "$INSTALL_DIR" ]; then
  echo "[!] ONYX already exists at $INSTALL_DIR"
else
  git clone https://github.com/zvlrxq-onyx/onyx-scanner.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install python deps
pip install --upgrade pip
pip install -r requirements.txt

# Make executable
chmod +x main.py

# Create launcher
cat <<EOF > onyx
#!/usr/bin/env bash
source "$INSTALL_DIR/venv/bin/activate"
python "$INSTALL_DIR/main.py"
EOF

chmod +x onyx

# Install globally
mkdir -p ~/.local/bin
cp onyx ~/.local/bin/

# PATH check
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
  echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
fi

echo ""
echo "[✓] ONYX installed successfully!"
echo "[✓] Restart terminal or run: source ~/.bashrc"
echo "[✓] Run tool using: onyx"
