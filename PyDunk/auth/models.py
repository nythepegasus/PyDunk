from datetime import datetime


class GSAuthToken:
    "A generic token container class for objects returned by GrandSlam"
    def __init__(
        self,
        name: str,
        token: str,
        duration: int,
        creation: datetime | None = None,
        expiry: datetime | None = None,
    ):
        self.name = name
        self.token = token
        self.duration = duration
        self.creation = creation if creation else datetime.now()
        self.expiry = expiry if expiry else datetime.fromtimestamp(self.creation.timestamp() + duration)

    @property
    def _base_repr(self):
        return f"'{self.creation:%Y-%m-%dT%H:%m:%SZ}', '{self.expiry:%Y-%m-%dT%H:%m:%SZ}', {self.duration}, {self.name!r}"

    def __repr__(self):
        return f"GSAuthToken({self._base_repr})"

    @classmethod
    def from_api(cls, name: str, data: dict) -> "GSAuthToken":
        return cls(
            name,
            data['token'],
            data['duration'],
            datetime.fromtimestamp(data['cts'] / 1e3) if 'cts' in data else None,
            datetime.fromtimestamp(data['expiry'] / 1e3) if 'expiry' in data else None,
        )


class GSAuthTokens:
    "A container for multiple generic tokens."
    def __init__(self, data: dict):
        self._data = data
        self.tokens = [GSAuthToken.from_api(token, attributes) for token, attributes in data.items()]

    def __repr__(self):
        return f"GSAuthTokens({self.tokens!r})"

    def __getitem__(self, i: str | int) -> GSAuthToken | None:
        if isinstance(i, int): return self.tokens[i] if i <= len(self.tokens) else None
        return next((t for t in self.tokens if i in t.name or i == t.name), None)


class IDMSAuthToken(GSAuthToken):
    "A container for the idms.auth token that allows you to query/refresh other tokens."
    def __init__(
        self,
        token: str,
        adsid: str,
        sk: bytes,
        c: str,
    ):
        super().__init__('com.apple.gs.idms.auth', token, 3600)
        self.adsid = adsid
        self.sk    = sk
        self.c     = c

    def __repr__(self):
        return f"IDMSAuthToken({self._base_repr}, {self.adsid!r})"

    @classmethod
    def from_spd(cls, data):
        return cls(data['GsIdmsToken'], data['adsid'], data['sk'], data['c'])


class XcodeAuthToken(GSAuthToken):
    "A container for the xcode.auth token that allows you to query to the Xcode APIs."
    def __init__(self, token: str, adsid: str):
        super().__init__('com.apple.gs.xcode.auth', token, 31536000)
        self.adsid = adsid
    
    def __repr__(self):
        return f"XcodeAuthToken({self._base_repr}, {self.adsid!r})"


