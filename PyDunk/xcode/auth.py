from ..auth.models import XcodeAuthToken
from ..utils.anisette import Anisette

from httpx import Auth, Request

class XcodeAuth(Auth):
    def __init__(self, adsid: str, token: str, anisette: Anisette):
        self.adsid    = adsid
        self.token    = token
        self.anisette = anisette

    def __repr__(self):
        return f"XcodeAuth({self.adsid!r})"

    @classmethod
    def from_token(cls, token: XcodeAuthToken, anisette: Anisette):
        return cls(token.adsid, token.token, anisette)

    @property
    def _base_headers(self):
        return {
            "User-Agent": "Xcode",
            "X-Apple-I-Identity-Id": self.adsid,
            "X-Apple-GS-Token": self.token,
            "X-Apple-App-Info": "com.apple.gs.xcode.auth",
            "X-Xcode-Version": "16.0 (16A242d}",
        }

    @property
    def _headers(self):
        return self.anisette.headers | self._base_headers

    def sync_auth_flow(self, request: Request):
        request.headers.update(self._headers)
        yield request

    async def async_auth_flow(self, request: Request):
        request.headers.update(self._headers)
        yield request


