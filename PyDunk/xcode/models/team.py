from enum import Enum

from ...common import SessionProvider
from .auth import XcodeAuth
from .account import Account
from .device import Device


class TeamKind(Enum):
    UNKNOWN      = 0
    FREE         = 1
    INDIVIDUAL   = 2
    ORGANIZATION = 3

    @classmethod
    def from_str(cls, s: str):
        if s == "Company/Organization": return cls.ORGANIZATION
        elif s == "Individial": return cls.INDIVIDUAL
        elif s == "free": return cls.FREE
        return cls.UNKNOWN

    @classmethod
    def from_api(cls, data: dict):
        if data['type'] == "Company/Organization": return cls.ORGANIZATION
        elif data['type'] == "Individual":
            memberships = data['memberships']
            if len(memberships) == 1 and 'free' in memberships[0]['name'].lower():
                return cls.FREE
            return cls.INDIVIDUAL
        return cls.UNKNOWN


class Team:
    def __init__(
        self,
        name: str,
        identifier: str,
        kind: TeamKind,
        account: Account
    ):
        self.name = name
        self.identifier = identifier
        self.kind = kind
        self.account = account

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r}, {self.identifier!r}, {self.kind!r}, {self.account!r})"

    @classmethod
    def from_api_with_account(cls, account: Account, data: dict):
        return cls(
            data['name'],
            data['teamId'],
            TeamKind.from_api(data),
            account
        )

