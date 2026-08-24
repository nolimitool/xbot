#!/usr/bin/env python3
"""
XBOT - Auto post / comment (reply) / like / retweet multi-akun X (Twitter)
=========================================================================
Engine: twikit (https://github.com/NoaHimesaka/twikit)
- Login OTOMATIS via user:pass -> cookies disimpan otomatis (load_cookies/
  save_cookies). GAK PERLU devtools / ambil auth_token manual.
- Aksi: post, reply (komentar), like, retweet.
- Multi-akun dengan rotasi + delay acak anti-detect.
- Mode --dry: simulasi tanpa nembak X.
- State akun disimpan di accounts.json (lokal).

AKUN: masukkan user:pass (atau user:email:pass) di accounts.json,
lalu `xbot.py login` untuk login sekali. Cookies tersimpan otomatis.
"""
import argparse, asyncio, json, random, re, sys, time
from pathlib import Path

# PATCH dulu SEBELUM import twikit (supaya regex + transport kepasang
# sebelum module x_client_transaction / httpx di-load).
try:
    import twikit_patches
    twikit_patches.patch_all()
except Exception as e:
    print(f"[warn] patch twikit gagal: {e}")

try:
    from twikit import Client
except ImportError:
    sys.exit("Jalankan: pip install -r requirements.txt (di dalam venv)")

STATE = Path(__file__).resolve().parent / "accounts.json"
TWEET_RE = re.compile(r"(?:status/|/)(?P<id>\d{10,})")

def parse_tweet_id(url_or_id):
    if str(url_or_id).isdigit():
        return str(url_or_id)
    m = TWEET_RE.search(url_or_id)
    return m.group("id") if m else None

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"accounts": []}

def save_state(st):
    STATE.write_text(json.dumps(st, indent=2))

def find_acc(st, username):
    for a in st["accounts"]:
        if a["username"] == username:
            return a
    return None

async def do_login(st, username, auth_info_1, auth_info_2, password, proxy=None):
    c = Client("en-US", proxy=proxy)
    await c.login(
        auth_info_1=auth_info_1,
        auth_info_2=auth_info_2,
        password=password,
    )
    cookies = c.get_cookies()
    return cookies

async def cmd_login(args):
    st = load_state()
    if args.all:
        targets = st["accounts"]
    else:
        a = find_acc(st, args.username)
        if not a:
            print(f"Akun {args.username} gak ada di state. Tambah dulu."); return
        targets = [a]
    for acc in targets:
        print(f"[+] Login {acc['username']} via proxy={args.proxy} ...")
        try:
            ck = await do_login(st, acc["username"], acc["auth_info_1"],
                                acc.get("auth_info_2"), acc["password"], args.proxy)
            acc["cookies"] = ck
            if args.proxy:
                acc["proxy"] = args.proxy
            save_state(st)
            print(f"    OK cookies tersimpan ({len(ck)} item)")
        except Exception as e:
            print(f"    GAGAL: {type(e).__name__}: {e}")

async def cmd_add(args):
    st = load_state()
    parts = args.account.split(":")
    if len(parts) == 2:
        u, p = parts
        a1, a2 = u, None
    elif len(parts) == 3:
        u, e, p = parts
        a1, a2 = u, e
    else:
        print("Format: user:pass  atau  user:email:pass"); return
    if find_acc(st, u):
        print(f"Akun {u} sudah ada."); return
    st["accounts"].append({"username": u, "auth_info_1": a1,
                           "auth_info_2": a2, "password": p, "cookies": None})
    save_state(st)
    print(f"[+] Akun {u} ditambah. Jalankan: xbot.py login --username {u}")

async def cmd_test(args):
    st = load_state()
    if not st["accounts"]:
        print("Belum ada akun."); return
    for a in st["accounts"]:
        has = "✓ cookies" if a.get("cookies") else "✗ belum login"
        print(f"  {a['username']} ({has})")

_CLIENTS = {}  # cache per-akun supaya session reuse (gak recreate tiap aksi)

async def cmd_clear(args):
    """Hapus cache client runtime + (opsional) cookies dari state.
    Dipakai kalau session expired / X tolak cookies lama."""
    global _CLIENTS
    _CLIENTS = {}
    if args.cookies:
        st = load_state()
        for a in st["accounts"]:
            a["cookies"] = None
        save_state(st)
        print("[OK] Semua cookies di-reset dari state.")
    else:
        print("[OK] Cache client runtime di-flush (cookies tetap tersimpan).")


async def cmd_proxy(args):
    """Set proxy default untuk satu/ semua akun di state."""
    st = load_state()
    targets = st["accounts"] if args.all else [a for a in st["accounts"] if a["username"] == args.username]
    if not targets:
        print("Akun gak ketemu."); return
    for a in targets:
        a["proxy"] = args.proxy
    save_state(st)
    print(f"[OK] Proxy {args.proxy} diset ke {len(targets)} akun.")


async def get_client(acc):
    """Ambil client yg SUDAH login.
    - Kalau ada cookies (dict dari load_cookies_xbot), pakai set_cookies(dict).
      NOTE: twikit.load_cookies() butuh PATH string, bukan dict -> kita pakai
      set_cookies(dict) yang memang nerima {name: value}.
    - Kalau gak ada cookies, login user:pass (sering ke-block di IP Indo).
    - Proxy ikut dibawa biar session konsisten dengan waktu login.
    """
    uname = acc["username"]
    if uname in _CLIENTS and _CLIENTS[uname] is not None:
        return _CLIENTS[uname]
    proxy = acc.get("proxy")
    c = Client("en-US", proxy=proxy)
    if acc.get("cookies"):
        # cookies disimpan sbg dict {name: value} (format get_cookies/set_cookies)
        c.set_cookies(acc["cookies"])
    else:
        await c.login(auth_info_1=acc["auth_info_1"],
                      auth_info_2=acc.get("auth_info_2"),
                      password=acc["password"])
    _CLIENTS[uname] = c
    return c

async def refresh_client(acc):
    """Paksa buat ulang client (dipakai kalau session expired/invalid)."""
    _CLIENTS.pop(acc["username"], None)
    return await get_client(acc)

async def safe_action(fn, acc, max_retries=3):
    """Jalankan aksi X dengan retry + backoff. Rotate proxy kalau disediakan."""
    last: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            client = await get_client(acc)
            return await fn(client)
        except Exception as e:
            last = e
            msg = str(e)
            # Session invalid / cookies expired -> buang cache, login ulang next try
            if any(k in msg for k in ("Unauthorized", "401", "auth_token", "ct0",
                                      "Could not find", "Invalid", "guest")):
                await refresh_client(acc)
            if attempt < max_retries:
                back = min(30, 2 ** attempt + random.uniform(0, 2))
                print(f"    [retry {attempt}] {acc['username']}: {type(e).__name__} -> tunggu {back:.1f}s")
                await asyncio.sleep(back)
    if last is None:
        raise RuntimeError("safe_action: no attempt executed (max_retries must be >=1)")
    raise last

async def run_action(st, action, text, tweet_id, filt, dry, delay, rounds):
    accs = st["accounts"]
    if filt and filt != "all":
        wanted = set(filt.split(","))
        accs = [a for a in accs if a["username"] in wanted]
    if not accs:
        print("Tidak ada akun cocok."); return
    for r in range(1, rounds + 1):
        print(f"\n=== ROUND {r}/{rounds} ===")
        for a in accs:
            t = text
            if rounds > 1 and action in ("post", "reply"):
                t = f"{text} #{r}"
            if dry:
                print(f"[DRY] {a['username']}: {action} -> {t or tweet_id}")
                continue
            try:
                if action == "post":
                    tw = await safe_action(lambda cl: cl.create_tweet(text=t), a)
                    print(f"[OK] {a['username']}: POST -> {tw.id}")
                elif action == "reply":
                    tw = await safe_action(lambda cl: cl.create_tweet(text=t, reply_to=tweet_id), a)
                    print(f"[OK] {a['username']}: REPLY -> {tw.id}")
                elif action == "like":
                    await safe_action(lambda cl: cl.favorite_tweet(tweet_id), a)
                    print(f"[OK] {a['username']}: LIKE {tweet_id}")
                elif action == "retweet":
                    await safe_action(lambda cl: cl.retweet(tweet_id), a)
                    print(f"[OK] {a['username']}: RETWEET {tweet_id}")
            except Exception as e:
                print(f"[FAIL] {a['username']}: {type(e).__name__}: {e}")
            if delay:
                d = delay + random.uniform(0, delay * 0.4)
                await asyncio.sleep(d)

async def dispatch(args):
    st = load_state()
    dry = args.dry
    if args.cmd == "post":
        await run_action(st, "post", args.text, None, args.accounts, dry, args.delay, args.rounds)
    elif args.cmd == "reply":
        tid = parse_tweet_id(args.tweet)
        if not tid: print("Tweet URL/ID gak valid."); return
        await run_action(st, "reply", args.text, tid, args.accounts, dry, args.delay, args.rounds)
    elif args.cmd == "like":
        tid = parse_tweet_id(args.tweet)
        if not tid: print("Tweet URL/ID gak valid."); return
        await run_action(st, "like", None, tid, args.accounts, dry, args.delay, args.rounds)
    elif args.cmd == "retweet":
        tid = parse_tweet_id(args.tweet)
        if not tid: print("Tweet URL/ID gak valid."); return
        await run_action(st, "retweet", None, tid, args.accounts, dry, args.delay, args.rounds)

def main():
    p = argparse.ArgumentParser(description="XBOT - auto post/comment/like/retweet multi-akun")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="Tambah akun (user:pass atau user:email:pass)")
    pa.add_argument("account")

    pl = sub.add_parser("login", help="Login akun (simpan cookies otomatis)")
    pl.add_argument("--username", default=None)
    pl.add_argument("--all", action="store_true", help="login semua akun")
    pl.add_argument("--proxy", default=None, help="http/socks5 proxy url")

    pt = sub.add_parser("test", help="Lihat daftar akun + status login")

    pp = sub.add_parser("post", help="Post tweet")
    pp.add_argument("text")
    pp.add_argument("--accounts", default="all")
    pp.add_argument("--delay", type=float, default=20)
    pp.add_argument("--rounds", type=int, default=1)
    pp.add_argument("--dry", action="store_true")

    pr = sub.add_parser("reply", help="Komentar/reply ke tweet")
    pr.add_argument("tweet")
    pr.add_argument("text")
    pr.add_argument("--accounts", default="all")
    pr.add_argument("--delay", type=float, default=20)
    pr.add_argument("--rounds", type=int, default=1)
    pr.add_argument("--dry", action="store_true")

    pli = sub.add_parser("like", help="Like tweet")
    pli.add_argument("tweet")
    pli.add_argument("--accounts", default="all")
    pli.add_argument("--delay", type=float, default=10)
    pli.add_argument("--rounds", type=int, default=1)
    pli.add_argument("--dry", action="store_true")

    prt = sub.add_parser("retweet", help="Retweet")
    prt.add_argument("tweet")
    prt.add_argument("--accounts", default="all")
    prt.add_argument("--delay", type=float, default=10)
    prt.add_argument("--rounds", type=int, default=1)
    prt.add_argument("--dry", action="store_true")

    pc = sub.add_parser("clear", help="Flush cache / reset cookies (kalau session expired)")
    pc.add_argument("--cookies", action="store_true", help="juga hapus cookies dari state")
    pc.add_argument("--all", action="store_true")

    pp2 = sub.add_parser("proxy", help="Set proxy default untuk akun")
    pp2.add_argument("--username", default=None)
    pp2.add_argument("--all", action="store_true")
    pp2.add_argument("proxy")

    args = p.parse_args()
    if args.cmd == "add": asyncio.run(cmd_add(args))
    elif args.cmd == "login": asyncio.run(cmd_login(args))
    elif args.cmd == "test": asyncio.run(cmd_test(args))
    elif args.cmd == "clear": asyncio.run(cmd_clear(args))
    elif args.cmd == "proxy": asyncio.run(cmd_proxy(args))
    else: asyncio.run(dispatch(args))

if __name__ == "__main__":
    main()
