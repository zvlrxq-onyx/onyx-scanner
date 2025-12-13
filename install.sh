#!/bin/bash
# ONYX Installer Script

echo "🔹 Installing ONYX Vulnerability Scanner..."

# Clone the repo
git clone https://github.com/zvlrxq-onyx/onyx-scanner.git ~/onyx-scanner

# Go to folder
cd ~/onyx-scanner || exit

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make main.py executable
chmod +x main.py

# Add a command 'onyx' to PATH
echo 'alias onyx="~/onyx-scanner/venv/bin/python ~/onyx-scanner/main.py"' >> ~/.bashrc
source ~/.bashrc

echo "✅ ONYX installed! Type 'onyx' to run it."
