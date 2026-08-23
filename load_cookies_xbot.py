#!/usr/bin/env python3
"""
LOAD COOKIES -> xbot state.
Ambil file cookies JSON (dari grab_cookies_interactive.py) lalu:
  1. Konversi ke dict {name: value} (format twikit load_cookies)
  2. Masukkan ke accounts.json sebagai akun dengan cookies siap pakai
Setelah ini xbot.py bisa langsung post/like/retweet TANPA login ulang.

Usage:
  source .venv/bin/activate
  python3 load_cookies_xbot.py Agent_Opet cookies_Agent_Opet.json
"""
import sys, json
from pathlib import Path

STATE = Path("/root/xbot/accounts.json")

def main():
    if len(sys.argv) < 3:
        print("Usage: load_cookies_xbot.py <username> <cookies.json>"); return
    user, ckfile = sys.argv[1], sys.argv[2]
    cookies = json.loads(Path(ckfile).read_text())
    # twikit load_cookies butuh dict name->value
    ck = {c["name"]: c["value"] for c in cookies}
    if "ct0" not in ck or "auth_token" not in ck:
        print("[!] WARNING: ct0/auth_token gak ada di cookies. Login mungkin gak valid.")
    st = json.loads(STATE.read_text()) if STATE.exists() else {"accounts": []}
    found = False
    for a in st["accounts"]:
        if a["username"] == user:
            a["cookies"] = ck; found = True
    if not found:
        st["accounts"].append({"username": user, "auth_info_1": user,
                               "auth_info_2": None, "password": "", "cookies": ck})
    STATE.write_text(json.dumps(st, indent=2))
    print(f"[OK] {user} dimasukkan ke xbot state dengan {len(ck)} cookies")
    print(f"     ct0: {'ADA' if 'ct0' in ck else 'TIDAK'} | auth_token: {'ADA' if 'auth_token' in ck else 'TIDAK'}")

main()
