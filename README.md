# XBOT — Auto Post / Comment / Like / Retweet Multi-Akun X (Twitter)

Tool otomasi X/Twitter untuk **banyak akun sekaligus**:
- **POST** tweet
- **REPLY / KOMENTAR** ke tweet tertentu
- **LIKE** tweet
- **RETWEET** tweet

Engine: **twikit** (login otomatis via user:pass, cookies disimpan sendiri).
Gak perlu devtools. Gak perlu ambil `auth_token`/`ct0` manual (kecuali mau pakai
mode cookies — lihat bawah).

> 🔧 **Catatan teknis:** twikit versi terbaru (2.3.3) rusak sejak X ubah format
> webpack Maret 2026 (`Couldn't get KEY_BYTE indices`). Tool ini sudah sertakan
> `twikit_patches.py` yang **otomatis fix** bug itu (set `key`/`key_bytes`/`animation_key`
> default + bypass `init` home-page fetch) biar `generate_transaction_id()` jalan
> tanpa error.
>
> **curl_cffi (TLS impersonate Chrome):** di Termux ARM64 + Python 3.14 **gak bisa**
> (wheel build buat 3.13 → `libpython3.13.so` hilang; rebuild source → crash NDK
> symbol). Jadi `twikit_patches.py` **skip curl_cffi graceful** dan pakai `httpx` biasa.
> Di desktop Linux/macOS x86_64 curl_cffi biasanya jalan (TLS lebih mirip Chrome).
>
> **Bug cookies (PENTING):** `twikit.load_cookies()` butuh **path file**, bukan dict.
> State xbot menyimpan cookies sebagai **dict** `{name: value}`, jadi `xbot.py`
> memakai `client.set_cookies(dict)` (bukan `load_cookies(dict)` yang crash). Ini
> sudah dibenerin — jalur cookies (satu-satunya yang tembus kalau IP lu ke-block)
> sekarang jalan.

---

## 📱 INSTAL DI TERMUX (Android)

Buka aplikasi **Termux**, lalu jalankan:

```bash
# 1. Install git + clone source, lalu masuk folder
pkg install -y git
git clone https://github.com/nolimitool/xbot.git
cd xbot

# 2. Auto-setup (install python, rust, openssl, venv, dependencies)
bash setup.sh
```

`setup.sh` akan:
- `pkg update` + install `python`, `python-dev`, `rust`, `openssl`, `pkg-config`, `git`
- buat virtual env `.venv`
- `pip install -r requirements.txt` (twikit + curl_cffi)

Setelah selesai, **setiap buka Termux baru**, aktifkan venv dulu:
```bash
cd xbot && source .venv/bin/activate
```

> 💡 **curl_cffi butuh Rust + OpenSSL** buat compile di Termux. `setup.sh` sudah
> install keduanya. Kalau compile tetap gagal:
> ```bash
> pkg install -y rust openssl pkg-config
> source .venv/bin/activate
> pip install --force-reinstall --no-cache-dir curl_cffi
> ```

---

## 🐧 INSTAL DI LINUX / macOS

```bash
git clone https://github.com/nolimitool/xbot.git
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

Kalau akun pakai 2FA email:
```bash
python xbot.py add "user:email@mail.com:password"
python xbot.py login --username user
```

### Cara B — Pakai cookies (kalau login tetap gagal / IP ke-block)
1. Login di browser HP (Chrome/Firefox).
2. Pakai ekstensi **Cookie-Editor** → export JSON.
3. Simpan jadi `cookies_Agent_Opet.json`, lalu:
```bash
python load_cookies_xbot.py Agent_Opet cookies_Agent_Opet.json
python xbot.py test   # harusnya ct0 + auth_token = ADA
```

### RESET session kalau cookies expired (X tolak)
```bash
# flush cache runtime saja (cookies tetap, client dibuat ulang next aksi)
python xbot.py clear

# flush + hapus cookies dari state (harus login ulang / load cookies segar)
python xbot.py clear --cookies
```

### Set proxy default per akun (biar login & aksi pakai IP sama)
```bash
python xbot.py proxy --all "http://user:pass@host:port"
python xbot.py proxy --username Agent_Opet "http://user:pass@host:port"
```

---

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

## 📁 STRUKTUR TOOL

```
xbot/
├── xbot.py                     # bot utama (post/reply/like/retweet)
├── twikit_patches.py           # fix otomatis twikit (KEY_BYTE + curl_cffi TLS)
├── load_cookies_xbot.py        # masukkan cookies ke state
├── grab_cookies_interactive.py # ambil cookies via browser (desktop/Linux)
├── requirements.txt
├── setup.sh                    # auto-install Termux/Linux
└── accounts.json               # state akun + cookies (auto-generated)
```

---

## 🔧 TROUBLESHOOTING

| Masalah | Solusi |
|---------|--------|
| `ModuleNotFoundError: twikit` | `source .venv/bin/activate` lalu `pip install -r requirements.txt` |
| `Couldn't get KEY_BYTE indices` | Sudah di-fix otomatis `twikit_patches.py`. Pastikan file itu ada di folder yang sama dengan `xbot.py`. |
| Login `403 Forbidden` / Cloudflare block | IP lu ke-block. Pakai `--proxy` residensial, atau cara cookies (lihat atas). |
| `curl_cffi` gagal load di Termux (`libpython3.so not found` / NDK symbol) | **Normal di Termux ARM64 + Py3.14.** xbot otomatis skip curl_cffi & pakai `httpx` biasa (lihat `[info] curl_cffi gak aktif`). Gak perlu rebuild. Kalau mau TLS-Chrome, jalanin di desktop Linux x86_64. |
| Aksi gagal `TypeError: expected str, bytes or os.PathLike` pas load cookies | Sudah dibenerin: `xbot.py` pakai `set_cookies(dict)`, bukan `load_cookies(dict)`. Pastikan `twikit_patches.py` + `xbot.py` versi terbaru. |
| `X-Client-Transaction` / `generate_transaction_id` error | Sudah di-fix `twikit_patches.py` (set `animation_key` + bypass `init`). Pastikan file ada di folder sama. |
| Tweet URL gak dikenali | Pakai format `https://x.com/user/status/1234567890` atau langsung ID numerik |
| `command not found: python` | Di beberapa distro pakai `python3` — ganti `python` jadi `python3` |

---

## ⚠️ CATATAN
- `accounts.json` menyimpan **username + cookies** di lokal. Jangan share file ini.
- Cookies bisa expired → kalau aksi gagal, `login --username` lagi atau pakai cookies segar.
- Delay acak otomatis (+0–40%) biar gak ke-detect pola.
- Gunakan sesuai TOS platform & aturan yang berlaku di wilayah masing-masing.
