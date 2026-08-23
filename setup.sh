#!/usr/bin/env bash
# setup.sh - instalasi otomatis XBOT di Termux / Linux / macOS
set -e

echo "=== XBOT setup ==="

# 1. Detect Termux
if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
    echo "[*] Termux terdeteksi"
    pkg update -y
    # python-dev di Termux sudah include di paket 'python' -> jangan install python-dev
    pkg install -y python rust openssl pkg-config git libxml2 libxslt
else
    echo "[*] Linux/macOS detected"
    if ! command -v python3 >/dev/null; then
        echo "Install python3 dulu"; exit 1
    fi
    # Linux butuh python-dev + build tools buat compile curl_cffi
    if command -v apt-get >/dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y python3-dev python3-venv build-essential libssl-dev pkg-config rustc
    elif command -v dnf >/dev/null; then
        sudo dnf install -y python3-devel openssl-devel pkgconfig rust
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
#   curl_cffi butuh rust + openssl di Termux/Linux -> sudah di-install di atas
pip install -r requirements.txt

echo ""
echo "=== INSTALL SELESAI ==="
echo "Aktifkan venv:  source .venv/bin/activate"
echo "Tambah akun:    python xbot.py add \"user:password\""
echo "Login:          python xbot.py login --username user"
echo "Cek:            python xbot.py test"
echo ""
echo "Baca README.md untuk detail."
