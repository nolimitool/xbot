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

async def get_client(acc):
    c = Client("en-US")
    if acc.get("cookies"):
        c.load_cookies(acc["cookies"])
    else:
        await c.login(auth_info_1=acc["auth_info_1"],
                      auth_info_2=acc.get("auth_info_2"),
                      password=acc["password"])
    return c

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
                client = await get_client(a)
            except Exception as e:
                print(f"[X] {a['username']} login gagal: {e}")
                continue
            try:
                if action == "post":
                    tw = await client.create_tweet(text=t)
                    print(f"[OK] {a['username']}: POST -> {tw.id}")
                elif action == "reply":
                    tw = await client.create_tweet(text=t, reply_to=tweet_id)
                    print(f"[OK] {a['username']}: REPLY -> {tw.id}")
                elif action == "like":
                    await client.favorite_tweet(tweet_id)
                    print(f"[OK] {a['username']}: LIKE {tweet_id}")
                elif action == "retweet":
                    await client.retweet(tweet_id)
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

    args = p.parse_args()
    if args.cmd == "add": asyncio.run(cmd_add(args))
    elif args.cmd == "login": asyncio.run(cmd_login(args))
    elif args.cmd == "test": asyncio.run(cmd_test(args))
    else: asyncio.run(dispatch(args))

if __name__ == "__main__":
    main()
