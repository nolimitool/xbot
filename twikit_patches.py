"""Runtime patches untuk twikit agar jalan di X terbaru (2026) TANPA utak-atik
site-packages secara manual.
  1. Fix get_indices/init di twikit.x_client_transaction (X hapus ondemand.s).
  2. Opsional: ganti httpx transport dengan curl_cffi (impersonate Chrome).
     Di Termux ARM64 Python 3.14, curl_cffi GAGAL load (NDK/libpython mismatch)
     -> kita SKIP silent, pakai httpx biasa. Login tetap jalan asal IP residensial
     gak di-block Cloudflare.

Dipanggil sekali di awal xbot.py (SEBELUM import twikit.Client).
"""
import re


def apply_keybyte_fix():
    """X (Maret 2026) sudah hapus ondemand.s dari HTML/JS -> regex gak match.
    Kita bypass: get_indices return default, init skip home-page fetch."""
    try:
        from twikit.x_client_transaction import transaction as T

        async def _fake_get_indices(self, home_page_response, session, headers):
            return 1, list(range(2, 18))

        async def _fake_init(self, session, headers):
            self.DEFAULT_ROW_INDEX = 1
            self.DEFAULT_KEY_BYTES_INDICES = list(range(2, 18))
            import base64
            self.key = base64.b64encode(b"obfiowerehiring0123456789abcdef").decode()
            self.key_bytes = list(base64.b64decode(self.key))
            self.animation_key = "00000000000000000000000000000000"

        T.ClientTransaction.get_indices = _fake_get_indices
        T.ClientTransaction.init = _fake_init
    except Exception as e:
        print(f"[warn] keybyte fix: {e}")


def apply_curl_cffi_transport():
    """Coba pasang curl_cffi TLS-Chrome. Kalau gak bisa (Termux ARM64), SKIP."""
    try:
        import curl_cffi  # import ini bakal raise kalau .so rusak
        # smoke test
        from curl_cffi.requests import AsyncSession
        _ = AsyncSession(impersonate="chrome")
    except Exception as e:
        # Termux: .so rusak / NDK mismatch -> skip, pakai httpx biasa
        print(f"[info] curl_cffi gak aktif (pakai httpx biasa): {e}")
        return

    try:
        import httpx
        if getattr(httpx.AsyncClient, "_xbot_patched", False):
            return

        class CurlCffiTransport(httpx.AsyncBaseTransport):
            def __init__(self, impersonate="chrome", verify=False, proxy=None):
                self.impersonate = impersonate
                self.verify = verify
                self.proxy = proxy
                self._session = None

            def _get(self):
                if self._session is None:
                    self._session = AsyncSession(impersonate=self.impersonate,
                                                  verify=self.verify, proxy=self.proxy)
                return self._session

            async def handle_async_request(self, request):
                s = self._get()
                content = request.content
                if isinstance(content, bytes) and len(content) == 0:
                    content = None
                resp = await s.request(method=request.method, url=str(request.url),
                                       headers=dict(request.headers), data=content,
                                       allow_redirects=True, timeout=30)
                return httpx.Response(status_code=resp.status_code,
                                     headers=dict(resp.headers), content=resp.content,
                                     request=request)

            async def aclose(self):
                if self._session is not None:
                    await self._session.close()

        _orig_init = httpx.AsyncClient.__init__

        def _new_init(self, *a, **kw):
            transport = kw.pop("transport", None)
            proxy = kw.get("proxy")
            if transport is None:
                kw["transport"] = CurlCffiTransport(impersonate="chrome", proxy=proxy)
            return _orig_init(self, *a, **kw)

        httpx.AsyncClient.__init__ = _new_init
        httpx.AsyncClient._xbot_patched = True
        print("[ok] curl_cffi TLS-Chrome aktif")
    except Exception as e:
        print(f"[info] curl_cffi transport gak aktif: {e}")


def patch_all():
    apply_keybyte_fix()
    apply_curl_cffi_transport()
