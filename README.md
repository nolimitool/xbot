# XBOT — Auto Post / Comment / Like / Retweet Multi-Akun X (Twitter)

Tool otomasi X/Twitter untuk **banyak akun sekaligus**:
- **POST** tweet
- **REPLY / KOMENTAR** ke tweet tertentu
- **LIKE** tweet
- **RETWEET** tweet

Engine: **twikit** (login otomatis via user:pass, cookies disimpan sendiri).
Gak perlu devtools. Gak perlu ambil `auth_token`/`ct0` manual (kecuali mau pakai
mode cookies — lihat bawah).

---

## 📱 INSTAL DI TERMUX (Android)

Buka aplikasi **Termux**, lalu jalankan:

```bash
# 1. Clone repo
pkg install -y git
git clone <URL_REPO_LU> xbot
cd xbot

# 2. Auto-setup (install python, rust, venv, dependencies)
bash setup.sh
```

`setup.sh` akan:
- `pkg update` + install `python`, `python-dev`, `rust`, `git`
- buat virtual env `.venv`
- `pip install -r requirements.txt` (twikit + curl_cffi)

Setelah selesai, **setiap buka Termux baru**, aktifkan venv dulu:
```bash
cd xbot && source .venv/bin/activate
```

> 💡 **curl_cffi butuh Rust** buat compile. `setup.sh` sudah install `rust`
> lewat `pkg`. Kalau install manual gagal di compile, jalankan
> `pkg install rust` lalu `pip install curl_cffi` lagi.

---

## 🐧 INSTAL DI LINUX / macOS

```bash
git clone <URL_REPO_LU> xbot
cd xbot
bash setup.sh
source .venv/bin/activate
```

---

## 🔑 TAMBAH & LOGIN AKUN

### Cara A — Login otomatis (REKOMENDASI, gak perlu devtools)
Karena lu jalanin di **Termux = IP seluler/WiFi rumah** (residensial), X biasanya
**GAK block** → login langsung tembus.

```bash
# Tambah akun (format: user:password  atau  user:email:password)
python xbot.py add "Agent_Opet:AgentOpet416"

# Login (cookies tersimpan otomatis)
python xbot.py login --username Agent_Opet

# Cek status
python xbot.py test
```

Kalau ada akun pakai 2FA email:
```bash
python xbot.py add "user:email@mail.com:password"
python xbot.py login --username user
```

### Cara B — Pakai cookies (kalau login tetap gagal)
Kalau suatu saat IP lu ke-block, pakai cookies dari browser:
1. Login di browser HP (Chrome/Firefox).
2. Pakai ekstensi **Cookie-Editor** → export JSON.
3. Simpan jadi `cookies_Agent_Opet.json`, lalu:
```bash
python load_cookies_xbot.py Agent_Opet cookies_Agent_Opet.json
python xbot.py test   # harusnya ct0 + auth_token = ADA
```

---

## 🚀 PENGGUNAAN

Semua aksi support `--accounts` (pilih akun) dan `--delay` (jeda anti-detect).

### POST tweet ke semua akun
```bash
python xbot.py post "Halo dari Termux!" --accounts all --delay 20
```

### POST ke akun tertentu
```bash
python xbot.py post "Halo!" --accounts Agent_Opet,user2
```

### REPLY / KOMENTAR ke tweet
```bash
python xbot.py reply "https://x.com/nama/status/1234567890" "Ini komentar bot"
```

### LIKE tweet
```bash
python xbot.py like "https://x.com/nama/status/1234567890"
```

### RETWEET
```bash
python xbot.py retweet "https://x.com/nama/status/1234567890"
```

---

## ⚙️ PARAMETER

| Flag | Default | Arti |
|------|---------|------|
| `--accounts` | `all` | `all` atau `user1,user2` (pilih akun) |
| `--delay` | 20 (post/reply) / 10 (like/rt) | detik jeda antar-aksi per akun |
| `--rounds` | 1 | ulang aksi N kali (auto tambah `#N`) |
| `--proxy` | none | `http://user:pass@host:port` (kalau IP ke-block) |
| `--dry` | off | simulasi, gak nembak X (cek alur) |

Contoh pakai proxy residensial:
```bash
python xbot.py login --username Agent_Opet --proxy "http://user:pass@host:port"
```

---

## 🧪 MODE --dry (CEK ALUR TANPA API)

```bash
python xbot.py post "Tes" --dry
python xbot.py reply "https://x.com/a/status/123" "Tes" --dry
```
Output contoh:
```
=== ROUND 1/1 ===
[DRY] Agent_Opet: post -> Halo dari Termux!
```

---

## 📁 STRUKTUR REPO

```
xbot/
├── xbot.py                    # bot utama (post/reply/like/retweet)
├── twikit_patches.py          # fix otomatis twikit (KEY_BYTE + curl_cffi TLS)
├── load_cookies_xbot.py       # masukkan cookies ke state
├── grab_cookies_interactive.py# ambil cookies via browser (desktop)
├── requirements.txt
├── setup.sh                   # auto-install Termux/Linux
├── accounts/                  # (opsional) template
└── accounts.json              # state akun + cookies (auto-generated)
```

---

## 🔧 TROUBLESHOOTING

| Masalah | Solusi |
|---------|--------|
| `ModuleNotFoundError: twikit` | `source .venv/bin/activate` lalu `pip install -r requirements.txt` |
| `Couldn't get KEY_BYTE indices` | Sudah di-fix otomatis oleh `twikit_patches.py`. Kalau masih muncul, pastikan `twikit_patches.py` ada di folder yg sama. |
| Login `403 Forbidden` / Cloudflare block | IP lu (Termux) kemungkinan ke-block. Pakai `--proxy` residensial, atau cara cookies (lihat atas). |
| `curl_cffi` gagal compile di Termux | `pkg install rust` lalu `pip install --force-reinstall curl_cffi` |
| Tweet URL gak dikenali | Pakai format `https://x.com/user/status/1234567890` atau langsung ID numerik |

---

## ⚠️ CATATAN
- `accounts.json` menyimpan **username + cookies** di lokal. Jangan share file ini.
- Cookies bisa expired → kalau aksi gagal, `login --username` lagi atau pakai cookies segar.
- Delay acak otomatis (+0–40%) biar gak ke-detect pola.
- Gunakan sesuai TOS platform & aturan yang berlaku di wilayah masing-masing.
