#!/usr/bin/env python3
"""
GRAB COOKIES INTERAKTIF - ambil ct0 + auth_token TANPA devtools.
Cara: skrip buka browser (headless shell), lu login manual di halaman itu,
lalu tekan Enter di terminal -> skrip baca semua cookies (termasuk ct0 &
auth_token) dan simpan ke file JSON. Tinggal kasih ke xbot.

Jalankan:
  source .venv/bin/activate
  python3 grab_cookies_interactive.py Agent_Opet

Lalu di browser yang muncul:
  1. Login dengan user/pass lu
  2. Kalau ada verifikasi (email/HP), selesaikan
  3. Pastikan sudah masuk ke home x.com
  4. Balik ke terminal, tekan ENTER

Cookies (ct0, auth_token, dll) akan disimpan ke cookies_<user>.json
"""
import sys, json, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = lambda u: f"/root/xbot/cookies_{u}.json"

async def main():
    if len(sys.argv) < 2:
        print("Usage: grab_cookies_interactive.py <username>"); return
    user = sys.argv[1]
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US")
        pg = await ctx.new_page()
        print("[*] Membuka x.com/login ... login manual di sana.")
        await pg.goto("https://x.com/login", wait_until="domcontentloaded", timeout=60000)
        print("[*] Setelah login + verifikasi selesai, tekan ENTER di terminal ini.")
        input("    (tekannya setelah yakin SUDAH MASUK ke x.com) >>> ")
        cookies = await ctx.cookies()
        # Convert ke dict {name: value} biar kompatibel langsung dengan
        # twikit set_cookies(dict) / load_cookies_xbot.py format state.
        ck_dict = {c["name"]: c["value"] for c in cookies}
        ct0 = ck_dict.get("ct0")
        auth = ck_dict.get("auth_token")
        Path(OUT(user)).write_text(json.dumps(ck_dict, indent=2))
        print(f"[OK] Cookies disimpan -> {OUT(user)}")
        print(f"     ct0     : {'ADA' if ct0 else 'TIDAK ADA'}")
        print(f"     auth_token: {'ADA' if auth else 'TIDAK ADA'}")
        print(f"     total   : {len(cookies)} cookies")
        await b.close()

asyncio.run(main())
