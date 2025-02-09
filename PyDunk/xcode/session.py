import json
from enum import Enum
from pprint import pp
import plistlib as plist
from uuid import uuid4

from ..common import SessionProvider
from ..auth.models import Anisette, GSAuthToken, GSAuthTokens
from .models.auth import XcodeAuth
from .models import Account, AppID, AppGroup, Device, Team
from .models.xs import  XSTeams, XSTeam, XSDevices


class ProfileIncludeKind(Enum):
    """
    (
        'appConsentBundleId',
        'appGroups',
        'bundleId',
        'capability',
        'certificates',
        'cloudContainers',
        'identityMerchantIds',
        'macBundleId',
        'merchantIds',
        'parentBundleId',
        'relatedAppConsentBundleIds'
    )
    """
    BUNDLE = "bundleId"
    CERTIFICATES = "certificates"
    DEVICES = "devices"
    BUNDLE_CAPABILITIES = BUNDLE + "bundleIdCapabilities"
    BUNDLE_MACAPPID = BUNDLE_CAPABILITIES + "macBundleId"
    BUNDLE_APPGROUPS = BUNDLE_CAPABILITIES + "appGroups"
    BUNDLE_CLOUDCONTAINERS = BUNDLE_CAPABILITIES + "cloudContainers"
    BUNDLE_CAPABILITY = BUNDLE_CAPABILITIES + "capability"
    BUNDLE_MERCHANTID = BUNDLE_CAPABILITIES + "merchantIds"
    BUNDLE_IDENTITYMERCHANTID = BUNDLE_CAPABILITIES + "identityMerchantIds"

class ProfileIncludeFilter:
    K = ProfileIncludeKind
    _D = [K.BUNDLE, K.CERTIFICATES, K.DEVICES]
    _DC = [K.BUNDLE, K.CERTIFICATES, K.DEVICES, K.BUNDLE_CAPABILITIES, K.BUNDLE_MACAPPID, K.BUNDLE_APPGROUPS, K.BUNDLE_CLOUDCONTAINERS]

    def __init__(self, params: list[K]):
        self.params = params

    def __str__(self):
        return ",".join(p.value for p in self.params)

    def __repr__(self):
        return str(self)

    @classmethod
    def default(cls) -> str:
        return str(cls(cls._D))

    @classmethod
    def entitlements(cls) -> str:
        return str(cls(cls._D))


class CertificateFieldKind(Enum):
    TYPE_ID = "certificateTypeId"
    TYPE_NAME = "certificateTypeName"
    SERIAL_NUMBER = "serialNumber"
    MACHINE_ID = "machineId"
    MACHINE_NAME = "machineName"
    REQUESTED = "requestedDate"
    EXPIRATION = "expirationDate"
    STATUS = "status"
    CONTENT = "certificateContent"


class CertificateFieldFilter:
    K = CertificateFieldKind
    _D = [K.TYPE_ID, K.TYPE_NAME, K.SERIAL_NUMBER, K.MACHINE_ID, K.MACHINE_NAME, K.REQUESTED, K.EXPIRATION, K.STATUS, K.CONTENT]

    def __init__(self, params: list[K]):
        self.params = params

    def __str__(self):
        return ",".join(p.value for p in self.params)

    @classmethod
    def default(cls) -> str:
        return str(cls(cls._D))



"""
               Devices      \
Capabilities - AppID        |- Profile
               Certificates /
"""



class XcodeSession(SessionProvider):
    def __init__(
        self,
        auth: XcodeAuth,
    ):
        super().__init__()
        self._auth = auth
        self._auth._session.verify = False
        self._session = self._auth._session

        self._account = None
        self._teams = None
        self.refresh_account()
        self._team_devices = {}

    @classmethod
    def from_dsid_token_anisette(
        cls,
        dsid: str,
        auth_token: str | GSAuthToken,
        anisette: Anisette | None = None,
    ):
        return cls(XcodeAuth(dsid, auth_token, anisette))

    def __repr__(self):
        return f"XcodeSession({self._auth})"

    @property
    def xteams(self) -> XSTeams:
        if self._teams is None: self._teams = XSTeams(self.account, self._auth)
        return self._teams

    @property
    def team(self) -> XSTeam:
        return self.xteams.team

    @property
    def teams(self) -> list[XSTeam]:
        return self.xteams.teams

    @property
    def _base_body(self) -> dict:
        return self._auth.body | {"teamId": self.team.identifier} if self._account is not None else {}

    #def _json_request_with_url(self, url: str, body: dict | None = None) -> dict:
    #    headers = self._auth.base_headers | self._base_json_headers | {
    #        "X-HTTP-Method-Override": "GET",
    #    }
    #    if body:
    #        return self._session.post(url, data=json.dumps(body).replace(" ", ""), headers=headers).json()
    #    return self._session.post(url, headers=headers).json()

    def refresh_account(self) -> Account:
        self._account = self._fetch_account()
        return self._account

    @property
    def account(self) -> Account:
        if self._account is None: self._account = self.refresh_account()
        return self._account

    @account.setter
    def account(self, new: Account):
        self._account = new

    def _fetch_account(self) -> Account:
        resp = self._dict_plist_request(
                    self._auth.BASE_URL + "viewDeveloper.action",
                    self._base_body,
                    headers=self._auth.headers,
               )
        #pp(resp)
        return Account.from_api(resp['developer'])

    def xdevices(self, team: XSTeam | None = None) -> XSDevices:
        if team is None: team = self.team
        if team.identifier not in self._team_devices: 
            self._team_devices[team.identifier] = XSDevices(team.team, self._auth)
        return self._team_devices[team.identifier]

    def devices(self, team: XSTeam | None = None) -> list[Device]:
        if team is None: team = self.team
        if team.identifier not in self._team_devices: 
            self._team_devices[team.identifier] = XSDevices(team.team, self._auth)
        return self._team_devices[team.identifier].devices

    def refresh_devices(self, team: XSTeam | None = None) -> list[Device]:
        if team is None: team = self.team
        if team.identifier not in self._team_devices:
            self._team_devices[team.identifier] = XSDevices(team.team, self._auth)
        return self._team_devices[team.identifier].refresh_devices()

    #def refresh_team(self) -> Team:
    #    self.team = self._fetch_team()
    #    return self.team

    #@property
    #def team(self) -> Team:
    #    if self._team is None: self._team = self._fetch_team()
    #    return self._team

    #@team.setter
    #def team(self, new: Team):
    #    self._team = new

    #def _fetch_team(self) -> Team:
    #    return Team.from_api_with_account(
    #        self.account,
    #        self._plist_request_with_url(self._BASE_URL + "listTeams.action")['teams'][0]
    #    )

    #def refresh_devices(self):
    #    return self._fetch_devices_for_team()

    #@property
    #def devices(self):
    #    if len(self._devices) == 0: self._devices = self.refresh_devices()
    #    return self._devices

    #def _fetch_devices_for_team(self):
    #    url = self._BASE_URL + "ios/listDevices.action"
    #    return [Device.from_api(d) for d in self._plist_request_with_url(url)['devices']]

    #def refresh_app_ids(self):
    #    return self._fetch_app_ids()

    #@property
    #def app_ids(self) -> list[AppID]:
    #    if len(self._app_ids) == 0: return self.refresh_app_ids()
    #    return self._app_ids

    #def _fetch_app_ids(self):
    #    url = self._BASE_URL + "ios/listAppIds.action"
    #    app_ids = self._plist_request_with_url(url, {"teamId": self.team.identifier})
    #    self._app_ids = [AppID.from_api(d) for d in app_ids['appIds']]
    #    return self._app_ids

    #def refresh_app_groups(self):
    #    return self._fetch_app_groups_for_team()

    #@property
    #def app_groups(self) -> list[AppGroup]:
    #    if len(self._app_groups) == 0: return self.refresh_app_groups()
    #    return self._app_groups

    #def _fetch_app_groups_for_team(self) -> list[AppGroup]:
    #    self._app_groups = [AppGroup.from_api(g) for g in self._plist_request_with_url(self._BASE_URL + "ios/listApplicationGroups.action")['applicationGroupList']]
    #    return self._app_groups

    #def fetch_all_profiles_for_team(self):
    #    return self._json_request_with_url(
    #        self._SERVICES_BASE_URL + "profiles",
    #        {
    #            "urlEncodedQueryParams": f"teamId={self.team.identifier}&include=bundleId,certificates,devices&limit=200"
    #        }
    #    )

    def fetch_capabilities(self):
        return self._dict_json_request(
            self._auth.SERVICES_BASE_URL + "capabilities",
            self._base_body | {"urlEncodedQueryParams":""},
            self._auth.headers | {"X-HTTP-Method-Override": "GET"}
        )

