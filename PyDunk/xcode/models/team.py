import json
from enum import Enum
import plistlib as plist
from urllib.parse import urlencode

from ..auth import XcodeAuth
from .base import XBaseRequest
from .device import Device
from .app import AppID

from requests import Session
    

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
    ):
        self.name = name
        self.identifier = identifier
        self.kind = kind

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r}, {self.identifier!r}, {self.kind!r})"

    @classmethod
    def from_api(cls, data: dict):
        return cls(
            data['name'],
            data['teamId'],
            TeamKind.from_api(data),
        )

    @classmethod
    def list_from_api(cls, data: dict):
        return [cls.from_api(t) for t in data['teams']]


class XTeamsRequest(XBaseRequest):
    URL = XBaseRequest.QH_URL + "listTeams.action"

    def fetch(self, session: Session | None = None) -> list[Team]:
        if session is None: session = self.session
        return Team.list_from_api(plist.loads(session.send(session.prepare_request(self)).text.encode('ascii')))


class Dev:
    def __init__(self, name: str, identifier: str):
        self.name = name
        self.identifier = identifier


"""
deviceNames=SUB+-+iiiii2004&deviceNumbers=00008112-0014781E0EDBA01E&devicePlatforms=ios&register=single&teamId=EU74F4WL9R
"""

class XQHValidateDevicesRequest(XBaseRequest):
    URL = XBaseRequest.QH_URL.replace("/services/", "/services-account/") + "account/device/validateDevices.action"

    def __init__(self, auth: XcodeAuth, team: Team, device: Dev, session: Session | None = None):
        self.team = team
        self.device = device
        super().__init__(auth, session)
        self.headers.update(self.URLENCODED_HEADERS)
        self.body = self._body

    @property
    def _body(self):
        return urlencode({
            'deviceNames': self.device.name,
            'deviceNumbers': self.device.identifier,
            'devicePlatforms': 'ios',
            'register': 'single',
            'teamId': self.team.identifier
        })

    def fetch(self, session: Session | None = None):
        if session is None: session = self.session
        return session.send(session.prepare_request(self))


class XQHiOSDeviceLimitsRequest(XBaseRequest):
    URL = XBaseRequest.QH_URL.replace("/services/", "/services-account/") + "account/ios/device/listDevices.action"

    def __init__(self, auth: XcodeAuth, team: Team, session: Session | None = None):
        self.team = team
        super().__init__(auth, session)
        self.headers.update(self.URLENCODED_HEADERS)
        self.body = self._body

    @property
    def _body(self):
        return urlencode({
            "includeRemovedDevices": True,
            "includeAvailability": True,
            "pageSize": 200,
            "pageNumber": 1,
            "sort": "status=asc",
            "teamId": self.team.identifier,
        })

    def fetch(self, session: Session | None = None):
        if session is None: session = self.session
        return session.send(session.prepare_request(self))


class XQHMacDeviceLimitsRequest(XBaseRequest):
    URL = XBaseRequest.QH_URL.replace("/services/", "/services-account/") + "account/mac/device/listDevices.action"

    def __init__(self, auth: XcodeAuth, team: Team, session: Session | None = None):
        self.team = team
        super().__init__(auth, session)
        self.headers.update(self.URLENCODED_HEADERS)
        self.body = self._body

    @property
    def _body(self):
        return urlencode({
            "includeRemovedDevices": True,
            "includeAvailability": True,
            "pageSize": 200,
            "pageNumber": 1,
            "sort": "status=asc",
            "teamId": self.team.identifier,
        })

    def fetch(self, session: Session | None = None):
        if session is None: session = self.session
        return session.send(session.prepare_request(self))


class XDevicesRequest(XBaseRequest):
    URL = XBaseRequest.V1_URL + "devices"

    def __init__(self, auth: XcodeAuth, team: Team, session: Session | None = None):
        self.team = team
        super().__init__(auth, session)
        self.headers.update(self.JSON_HEADERS)
        self.body = self._body

    @property
    def _body(self) -> str:
        return json.dumps({'teamId': self.team.identifier}, separators=(",", ":"))

    def fetch(self, session: Session | None = None) -> list[Device]:
        if session is None: session = self.session
        self.headers.update({"X-HTTP-Method-Override": "GET"})
        return Device.list_from_api(session.send(session.prepare_request(self)).json()['data'])


class XProfilesRequest(XBaseRequest):
    URL = XBaseRequest.V1_URL + "profiles"

    def __init__(self, auth: XcodeAuth, team: Team, session: Session | None = None):
        self.team = team
        super().__init__(auth, session)
        self.headers.update(self.JSON_HEADERS)
        self.body = self._body

    @property
    def _body(self) -> str:
        return json.dumps({'teamId': self.team.identifier}, separators=(",", ":"))

    def fetch(self, session: Session | None = None):
        if session is None: session = self.session
        self.headers.update({"X-HTTP-Method-Override": "GET"})
        return session.send(session.prepare_request(self)).json()


class XCapabilitiesRequest(XBaseRequest):
    URL = XBaseRequest.V1_URL + "capabilities"

    def __init__(self, auth: XcodeAuth, team: Team, session: Session | None = None):
        self.team = team
        super().__init__(auth, session)
        self.headers.update(self.JSON_HEADERS)
        self.body = self._body

    @property
    def _body(self) -> str:
        return json.dumps({'teamId': self.team.identifier}, separators=(",", ":"))

    def fetch(self, session: Session | None = None):
        if session is None: session = self.session
        self.headers.update({"X-HTTP-Method-Override": "GET"})
        return session.send(session.prepare_request(self)).json()


class XQHAppIDRequest(XBaseRequest):
    URL = XBaseRequest.QH_URL + "ios/listAppIds.action"

    def __init__(self, auth: XcodeAuth, team: Team, session: Session | None = None):
        self.team = team
        super().__init__(auth, session)
        self.headers.update(self.PLIST_HEADERS)
        self.body = self._body

    @property
    def _body(self) -> bytes:
        return plist.dumps({'teamId': self.team.identifier})

    def fetch(self, session: Session | None = None):
        if session is None: session = self.session
        self.headers.update({"X-HTTP-Method-Override": "GET"})
        d = session.send(session.prepare_request(self))
        try:
            return AppID.list_from_api(plist.loads(d.text))
        except KeyError:
            print(d.text)
            return d


class XV1AppIDRequest(XBaseRequest):
    URL = XBaseRequest.V1_URL + "profiles"

    def __init__(self, auth: XcodeAuth, team: Team, session: Session | None = None):
        self.team = team
        super().__init__(auth, session)
        self.body = self._body

    @property
    def _body(self) -> str:
        return json.dumps({'teamId': self.team.identifier}, separators=(",", ":"))
    
    def fetch(self, session: Session | None = None):
        if session is None: session = self.session
        self.headers.update({"X-HTTP-Method-Override": "GET"})
        return session.send(session.prepare_request(self))

