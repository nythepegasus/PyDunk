import plistlib as plist
from uuid import uuid4

from ..auth.models.anisette import Anisette
from ..auth.models.gstokens import GSAuthToken

from requests.auth import AuthBase


class XcodeAuth(AuthBase):
    def __init__(
        self,
        dsid: str,
        token: str | GSAuthToken,
        anisette: Anisette | None = None,
    ):
        self.dsid = dsid
        self.token = token.token if isinstance(token, GSAuthToken) else token
        self.anisette = Anisette() if anisette is None else anisette
        self._session = self.anisette._session

    def __repr__(self):
        return f"{self.__class__.__name__}(" + \
               f"{self.dsid!r}, " + \
               f"{self.token!r}, " + \
               f"{self.anisette!r})"

    def __call__(self, r):
        r.headers.update(self.headers)
        return r

    @property
    def headers(self) -> dict[str, str]:
        return self.anisette.headers | {
            "User-Agent": "Xcode",
            "Accept-Language": "en-us",
            "X-Apple-I-Identity-Id": self.dsid,
            "X-Apple-GS-Token": self.token,
        }

    @property
    def body(self) -> dict[str, str]:
        return {
            "clientId": "XABBG36SBA",
            "protocolVersion": "A1234",
            "requestId": str(uuid4()),
        }

    @property
    def plist_body(self) -> bytes:
        return plist.dumps(self.body)

