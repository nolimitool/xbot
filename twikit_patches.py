"""Runtime patches untuk twikit agar jalan di X terbaru (2026) TANPA utak-atik
site-packages secara manual.
  1. Fix regex KEY_BYTE di twikit.x_client_transaction (X ubah webpack format).
  2. Ganti httpx transport dengan curl_cffi (impersonate Chrome) supaya gak
     di-detect TLS datacenter oleh Cloudflare.
Dipanggil sekali di awal xbot.py.
"""
import re

def apply_keybyte_fix():
    """X (Maret 2026) sudah hapus ondemand.s dari HTML/JS -> regex gak match.
    Kita bypass: get_indices return default, init skip home-page fetch."""
    try:
        from twikit.x_client_transaction import transaction as T

        async def _fake_get_indices(self, home_page_response, session, headers):
            # default dari twikit (row_index=1, key_bytes=[2,3,...])
            return 1, list(range(2, 18))

        async def _fake_init(self, session, headers):
            # skip fetch home page (butuh regex yg udah gak ada)
            self.DEFAULT_ROW_INDEX = 1
            self.DEFAULT_KEY_BYTES_INDICES = list(range(2, 18))
            # key dummy (base64 32 bytes) biar get_key_bytes gak crash
            import base64
            self.key = base64.b64encode(b"obfiowerehiring0123456789abcdef").decode()
            self.key_bytes = list(base64.b64decode(self.key))
            self.animation_key = "00000000000000000000000000000000"

        T.ClientTransaction.get_indices = _fake_get_indices
        T.ClientTransaction.init = _fake_init
    except Exception as e:
        print(f"[warn] keybyte fix: {e}")

def apply_curl_cffi_transport():
    try:
        import httpx
        from curl_cffi.requests import AsyncSession
        # cek sudah dipatch?
        if getattr(httpx.AsyncClient, "_xbot_patched", False):
            return
        _orig_init = httpx.AsyncClient.__init__

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

        def _new_init(self, *a, **kw):
            transport = kw.pop("transport", None)
            proxy = kw.get("proxy")
            if transport is None:
                kw["transport"] = CurlCffiTransport(impersonate="chrome", proxy=proxy)
            return _orig_init(self, *a, **kw)

        httpx.AsyncClient.__init__ = _new_init
        httpx.AsyncClient._xbot_patched = True
    except Exception as e:
        print(f"[warn] curl_cffi transport gagal dipasang: {e}")

def patch_all():
    apply_keybyte_fix()
    apply_curl_cffi_transport()
