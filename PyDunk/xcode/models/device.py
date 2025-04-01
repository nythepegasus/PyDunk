from enum import Enum

import arrow


class DeviceKind(Enum):
    UNKNOWN = 0
    IPHONE  = 1
    IPAD    = 2
    TVOS    = 3
    WATCH   = 4

    @classmethod
    def from_str(cls, s: str):
        if s == "iphone": return cls.IPHONE
        elif s == "ipad": return cls.IPAD
        elif s == "tvOS": return cls.TVOS
        elif s == "watch": return cls.WATCH
        return cls.UNKNOWN


class Device:
    """
dict_keys(['addedDate', 'name', 'deviceClass', 'model', 'udid', 'platform', 'responseId', 'status'])
    """
    def __init__(
        self,
        device_id: str,
        name: str,
        udid: str,
        added: arrow.Arrow,
        status: bool,
        platform: str,
        device_class: str,
        model: str,
    ):
        self.device_id = device_id
        self.name = name
        self.udid = udid
        self.added = added
        self.platform = platform
        self.device_class = device_class
        self.model = model
        self.status = status

    def __repr__(self):
        return f"{self.__class__.__name__}(" + \
               f"{self.device_id!r}, "       + \
               (f"{self.name!r}, " if 'SUB' not in self.name else f"'REDACTED', ")            + \
               (f"{self.udid!r}, " if 'SUB' not in self.name else f"'REDACTED', ")            + \
               f"{self.added!r}, "           + \
               f"{self.status!r}, "          + \
               f"{self.platform!r}, "        + \
               f"{self.device_class!r}, "    + \
               f"{self.model!r}"             + \
               ")"

    @classmethod
    def from_api(cls, data: dict):
        return cls(
            data['id'],
            data['attributes']['name'],
            data['attributes']['udid'],
            arrow.get(data['attributes']['addedDate']),
            data['attributes']['status'],
            data['attributes']['platform'],
            data['attributes']['deviceClass'],
            data['attributes']['model'],
        )

    @classmethod
    def list_from_api(cls, data: list[dict]) -> "list[Device]":
        return [cls.from_api(d) for d in data]


