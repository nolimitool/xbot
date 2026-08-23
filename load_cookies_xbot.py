#!/usr/bin/env python3
"""
LOAD COOKIES -> xbot state (BEST FIX buat Termux yg ke-block Cloudflare).

Cara paling reliable di Termux:
  1. Login X di browser HP (Chrome/Firefox).
  2. Pasang ekstensi "Cookie-Editor" (add-on FF / extension Chrome).
  3. Klik ikon -> Export -> "Export as JSON" (dapat array [{name,value,...}]).
  4. Simpan jadi cookies_Agent_Opet.json, lalu:

     python load_cookies_xbot.py Agent_Opet cookies_Agent_Opet.json

  5. Cek:  python xbot.py test
  6. Pakai: python xbot.py post "Halo!" --accounts Agent_Opet

Support 3 format export:
  - Cookie-Editor:  [{"name":"ct0","value":"...",...}, ...]
  - dict flat:      {"ct0":"...","auth_token":"..."}
  - wrapped:        {"cookies": {"ct0":"...", ...}}

Setelah cookies masuk, xbot PAKAI cookies tsb (gak perlu login ulang,
gak perlu twikit.login yang sering ke-block Cloudflare).
"""
import sys, json
from pathlib import Path

STATE = Path(__file__).resolve().parent / "accounts.json"

def parse_cookies(raw):
    # format Cookie-Editor: list of {name, value}
    if isinstance(raw, list):
        return {c["name"]: c["value"] for c in raw if "name" in c and "value" in c}
    if isinstance(raw, dict):
        # wrapped {"cookies": {...}} atau sudah flat dict
        if "cookies" in raw and isinstance(raw["cookies"], dict):
            return raw["cookies"]
        return raw
    raise ValueError("format cookies gak dikenali")

def main():
    if len(sys.argv) < 3:
        print("Usage: load_cookies_xbot.py <username> <cookies.json>")
        return
    user, ckfile = sys.argv[1], sys.argv[2]
    raw = json.loads(Path(ckfile).read_text())
    ck = parse_cookies(raw)
    if "ct0" not in ck or "auth_token" not in ck:
        print("[!] WARNING: ct0/auth_token gak ada di cookies. X bakal tolak.")
        print("    Pastikan export dari session YANG SUDAH LOGIN ke x.com.")
        return
    st = json.loads(STATE.read_text()) if STATE.exists() else {"accounts": []}
    found = False
    for a in st["accounts"]:
        if a["username"] == user:
            a["cookies"] = ck; found = True
    if not found:
        st["accounts"].append({"username": user, "auth_info_1": user,
                               "auth_info_2": None, "password": "", "cookies": ck})
    STATE.write_text(json.dumps(st, indent=2))
    print(f"[OK] {user} -> {len(ck)} cookies ke xbot state")
    print(f"     ct0: ADA | auth_token: ADA")

if __name__ == "__main__":
    main()
