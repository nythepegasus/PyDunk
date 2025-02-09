from datetime import datetime


class GSAuthToken:
    def __init__(
        self,
        name: str,
        token: str,
        duration: int,
        expiry: datetime,
        creation: datetime | None = None,
    ):
        self.name = name
        self.token = token
        self.duration = duration
        self.creation = creation
        self.expiry = expiry

    def __repr__(self):
        return f"GSAuthToken({self.name!r}, {self.duration}, '{self.creation}', '{self.expiry}')"

    @classmethod
    def from_api(cls, name: str, data: dict) -> "GSAuthToken":
        return cls(
            name,
            data['token'],
            data['duration'],
            datetime.fromtimestamp(data['expiry'] / 1e3),
            datetime.fromtimestamp(data['cts'] / 1e3) if 'cts' in data else datetime.now(),
        )


class GSAuthTokens:
    def __init__(self, data: dict):
        self._data = data
        self.tokens = [GSAuthToken.from_api(token, attributes) for token, attributes in data.items()]
