import json
import plistlib as plist
from typing import Callable
from datetime import datetime
from functools import lru_cache, cached_property

from ..auth import GSAuthSync
from .auth import XcodeAuth
from .models import Account

from anisettev3 import AnisetteV3SyncClient as AniV3Sync, AnisetteV3AsyncClient as AniV3Async
from httpx import Client, Response


class QHDevice:
    def __init__(
        self,
        device_id: str,
        name: str,
        device_number: str,
        device_class: str,
        device_platform: str,
        status: str,
        model: str | None = None,
        expiration: datetime | None = None,
    ):
        self.device_id       = device_id
        self.name            = name
        self.device_number   = device_number
        self.device_class    = device_class
        self.device_platform = device_platform
        self.status          = status
        self.model           = model
        self.expiration      = expiration

    def __repr__(self):
        return f"{self.__class__.__name__}({self.device_id!r}, {self.device_number!r}, {self.status!r}, {self.name!r}{', ' + repr(self.expiration) if self.expiration else ''})"

    @classmethod
    def from_api(cls, d: dict):
        return cls(
            d['deviceId'],
            d['name'],
            d['deviceNumber'],
            d['deviceClass'],
            d['devicePlatform'],
            d['status'],
            d['model'] if 'model' in d else None,
            d['expirationDate'] if 'expirationDate' in d else None,
        )

# dict_keys(['appIdId', 'name', 'appIdPlatform', 'prefix', 'identifier', 'isWildCard', 'isDuplicate', 'features', 'enabledFeatures', 'isDevPushEnabled', 'isProdPushEnabled', 'associatedApplicationGroupsCount', 'associatedCloudContainersCount', 'associatedIdentifiersCount'])
class QHAppID:
    def __init__(
        self,
        app_id: str,
        name: str,
        platform: str,
        prefix: str,
        identifier: str,
        wildcard: bool,
        duplicate: bool,
        features,
        enabled_features,
        dev_push_enabled: bool,
        prod_push_enabled: bool,
        associated_app_groups: int,
        associated_cloud_countainers: int,
        associated_identifiers: int,
        expiration: datetime | None = None,
    ):
        self.app_id                      = app_id
        self.name                        = name
        self.platform                    = platform
        self.prefix                      = prefix
        self.identifier                  = identifier
        self.wildcard                    = wildcard
        self.duplicate                   = duplicate
        self.features                    = features
        self.enabled_features            = enabled_features
        self.dev_push_enabled            = dev_push_enabled
        self.prod_push_enabled           = prod_push_enabled
        self.associated_app_groups       = associated_app_groups
        self.associated_cloud_containers = associated_cloud_countainers
        self.associated_identifiers      = associated_identifiers
        self.expiration                  = expiration

    def __repr__(self):
        return f"{self.__class__.__name__}({self.app_id!r}, {self.platform!r}, {self.identifier!r}, {self.name!r}{', ' + repr(self.expiration) if self.expiration else ''})"

    @classmethod
    def from_api(cls, d: dict):
        return cls(
            d['appIdId'],
            d['name'],
            d['appIdPlatform'],
            d['prefix'],
            d['identifier'],
            d['isWildCard'],
            d['isDuplicate'],
            d['features'],
            d['enabledFeatures'] if 'enabledFeatures' in d else [],
            d['isDevPushEnabled'],
            d['isProdPushEnabled'],
            d['associatedApplicationGroupsCount'],
            d['associatedCloudContainersCount'],
            d['associatedIdentifiersCount'],
            d['expirationDate'] if 'expirationDate' in d else None,
        )


# dict_keys(['applicationGroup', 'name', 'status', 'prefix', 'identifier'])
class QHApplicationGroup:
    def __init__(
        self,
        group: str,
        name: str,
        status: str,
        prefix: str,
        identifier: str,
    ):
        self.group      = group
        self.name       = name
        self.status     = status
        self.prefix     = prefix
        self.identifier = identifier

    def __repr__(self):
        return f"{self.__class__.__name__}({self.group!r}, {self.prefix!r}, {self.status!r}, {self.identifier!r}, {self.name!r})"

    @classmethod
    def from_api(cls, d: dict):
        return cls(
            d["applicationGroup"],
            d["name"],
            d["status"],
            d["prefix"],
            d["identifier"],
        )


# dict_keys(['status', 'name', 'teamId', 'type', 'extendedTeamAttributes', 'memberships', 'currentTeamMember', 'dateCreated', 'xcodeFreeOnly', 'teamProvisioningSettings'])
class Team:
    def __init__(
        self,
        team_id: str,
        name: str,
        status: str,
        kind: str,
        extended_attributes,
        memberships,
        current_member,
        created: datetime,
        xcode_free_only: bool,
        provisioning_settings: dict[str, bool],
        x = None,
    ):
        self.team_id               = team_id
        self.name                  = name
        self.status                = status
        self.kind                  = kind
        self.extended_attributes   = extended_attributes
        self.memberships           = memberships
        self.current_member        = current_member
        self.created               = created
        self.xcode_free_only       = xcode_free_only
        self.provisioning_settings = provisioning_settings
        self._x = x

    def __repr__(self):
        return f"{self.__class__.__name__}({self.team_id!r}, {self.kind!r}, {self.status!r}, {self.name!r})"

    @classmethod
    def from_api(cls, d: dict, x = None):
        return cls(
            d["teamId"],
            d["name"],
            d["status"],
            d["type"],
            d["extendedTeamAttributes"],
            d["memberships"],
            d["currentTeamMember"],
            d["dateCreated"],
            d["xcodeFreeOnly"],
            d["teamProvisioningSettings"],
            x,
        )

    @cached_property
    def app_ids(self) -> list[QHAppID] | None:
        return self._x.app_ids(self) if self._x else None

    @cached_property
    def capabilities(self) -> dict | None:
        return self._x.capabilities(self) if self._x else None

    @cached_property
    def devices(self) -> list[QHDevice] | None:
        return self._x.devices(self) if self._x else None

    @cached_property
    def qh_app_groups(self) -> list[QHApplicationGroup] | None:
        return self._x.qh_app_groups(self) if self._x else None

    @cached_property
    def profiles(self) -> dict | None:
        return self._x.profiles(self) if self._x else None

class XcodeAPIException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class XcodeAPI:
    def __init__(self, auth: XcodeAuth, **kwargs):
        if auth.anisette is AniV3Async:
            raise ValueError("This class does not support async!")
        self._auth = auth
        self._client = Client(auth=self._auth, headers=auth._base_headers, base_url="https://developerservices2.apple.com", **kwargs)

    def _check_r(self, r: Response) -> Response:
        if r.is_success: return r
        raise XcodeAPIException(r.reason_phrase)

    def _r(self, url: str, method: str = "POST", content: bytes | None = None, headers: dict | None = None, proc_func: Callable[[bytes], dict] | None = None) -> Response | dict:
        if headers is None: headers = {}
        if content is None: ret = self._check_r(self._client.request(method, url, headers=headers, timeout=5))
        else: ret = self._check_r(self._client.request(method, url, content=content, headers=headers, timeout=5))
        return ret if proc_func is None else proc_func(ret.content)

    def _pr(self, url: str, method: str = "POST", content: dict | None = None, headers: dict | None = None) -> dict:
        if headers is None: headers = {}
        if content is not None: headers |= {"Accept": "text/x-xml-plist", "Content-Type": "text/x-xml-plist"}
        return self._r(url, method, plist.dumps(content) if content else None, headers, plist.loads) # type: ignore
        
    def _jr(self, url: str, method: str = "GET", content: dict | None = None, headers: dict | None = None) -> dict:
        if headers is None: headers = {"Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json", "X-HTTP-Method-Override": method}
        else: headers |= {"Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json", "X-HTTP-Method-Override": method}
        if content is None: return self._r(url, "POST", headers=headers, proc_func=json.loads) # type: ignore
        return self._r(url, "POST", content=json.dumps(content, separators=(",", ":")).encode(), headers=headers, proc_func=json.loads) # type: ignore

    @classmethod
    def from_gsauth(cls, gs: GSAuthSync, *args, **kwargs):
        return cls(XcodeAuth.from_token(gs.fetch_xcode_token(), gs.anisette), *args, **kwargs)

    @cached_property
    def account(self) -> Account:
        return Account.from_api(self._pr("/services/QH65B2/viewDeveloper.action")["developer"])

    @cached_property
    def teams(self) -> list[Team]:
        return [Team.from_api(t, self) for t in self._pr("/services/QH65B2/listTeams.action")['teams']]

    @lru_cache()
    def app_ids(self, team: Team) -> list[QHAppID]:
        return [QHAppID.from_api(a) for a in self._pr(
            "/services/QH65B2/ios/listAppIds.action",
            content={"teamId": team.team_id},
            )['appIds']]

    @lru_cache()
    def qh_app_groups(self, team: Team) -> list[QHApplicationGroup]:
        return [QHApplicationGroup.from_api(g) for g in self._pr(
            '/services/QH65B2/ios/listApplicationGroups.action',
            content={"teamId": team.team_id},
        )['applicationGroupList']]

    @lru_cache()
    def devices(self, team: Team) -> list[QHDevice]:
        return [QHDevice.from_api(d) for d in self._pr(
            "/services/QH65B2/ios/listDevices.action",
            content={"teamId": team.team_id},
        )['devices']]

    @lru_cache()
    def v1_app_ids(self, team: Team):
        return self._jr(
            '/services/v1/bundleIds',
            content={'teamId': team.team_id}
        )

    @lru_cache()
    def capabilities(self, team: Team):
        return self._jr(
            '/services/v1/capabilities',
            content={'teamId': team.team_id}
        )

    @lru_cache()
    def v1_devices(self, team: Team):
        return self._jr(
            '/services/v1/devices',
            content={'teamId': team.team_id}
        )

    @lru_cache()
    def profiles(self, team: Team):
        return self._jr(
            '/services/v1/profiles',
            content={'teamId': team.team_id}
        )

    def __repr__(self):
        return f"XcodeAPI({self._auth!r})"

