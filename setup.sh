#!/usr/bin/env bash
# setup.sh - instalasi otomatis XBOT di Termux / Linux / macOS
set -e

echo "=== XBOT setup ==="

# 1. Detect Termux
if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
    echo "[*] Termux terdeteksi"
    pkg update -y
    pkg install -y python python-dev rust git
else
    echo "[*] Linux/macOS detected"
    # butuh python3 + pip + git
    if ! command -v python3 >/dev/null; then
        echo "Install python3 dulu"; exit 1
    fi
fi

# 2. venv
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 3. upgrade pip
pip install --upgrade pip

# 4. install deps
#   curl_cffi butuh rust di Termux -> sudah install rust di atas
pip install -r requirements.txt

echo ""
echo "=== INSTALL SELESAI ==="
echo "Aktifkan venv:  source .venv/bin/activate"
echo "Tambah akun:    python xbot.py add \"user:password\""
echo "Login:          python xbot.py login --username user"
echo "Cek:            python xbot.py test"
echo ""
echo "Baca README.md untuk detail."
