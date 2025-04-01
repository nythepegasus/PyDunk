from enum import Enum
from pprint import pp
from datetime import datetime


class Entitlement(Enum):
    APPLICATION_IDENTIFIER           = "application-identifier"
    KEYCHAIN_ACCESS_GROUPS           = "keychain-access-groups"
    APP_GROUPS                       = "com.apple.security.application-groups"
    GET_TASK_ALLOW                   = "get-task-allow"
    INCREASED_MEMORY_LIMIT           = "com.apple.developer.kernel.increased-memory-limit"
    TEAM_IDENTIFIER                  = "com.apple.developer.team-identifier"
    INTER_APP_AUDIO                  = "inter-app-audio"
    INCREASED_DEBUGGING_MEMORY_LIMIT = "com.apple.developer.kernel.increased-debugging-memory-limit"
    EXTENDED_VIRTUAL_ADDRESSING      = "com.apple.developer.kernel.extended-virtual-addressing"

    def is_free(self):
        return self in [self.INTER_APP_AUDIO, self.GET_TASK_ALLOW, self.INCREASED_MEMORY_LIMIT,
                        self.TEAM_IDENTIFIER, self.KEYCHAIN_ACCESS_GROUPS, self.APPLICATION_IDENTIFIER]


class Capability(Enum):
    INCREASED_MEMORY_LIMIT           = "INCREASED_MEMORY_LIMIT"
    INCREASED_DEBUGGING_MEMORY_LIMIT = "INCREASED_MEMORY_DEBUGGING"
    EXTENDED_VIRTUAL_ADDRESSING      = "EXTENDED_VIRTUAL_ADDRESSING"


class Feature(Enum):
    GAMECENTER      = "gameCenter"
    APP_GROUPS      = "APG3427HIY"
    INTER_APP_AUDIO = "IAD53UNK2F"

    @classmethod
    def from_entitlement(cls, e: Entitlement) -> "Feature | Entitlement":
        if e is Entitlement.APP_GROUPS: return cls.APP_GROUPS
        elif e is Entitlement.INTER_APP_AUDIO: return cls.INTER_APP_AUDIO
        return e


class AppID:
    def __init__(
        self,
        name: str,
        identifier: str,
        bundle: str,
        expiration: datetime | None,
        features: dict,
    ):
        self.name = name
        self.identifier = identifier
        self.bundle = bundle
        self.expiration = expiration
        self.features = features

    def __repr__(self):
        return f"AppID({self.identifier!r}, {self.name!r}, {self.bundle!r}, {self.expiration}, {self.features})"

    @classmethod
    def from_api(cls, data: dict):
        #pp(data)
        name = data['name']
        identifier = data['appIdId']
        bundle = data['identifier']
        all_features = data['features']
        enabled_features = data['enabledFeatures'] if 'enabledFeatures' in data else []
        features = {feature: all_features[feature] for feature in enabled_features}
        expiration = data['expirationDate'] if 'expirationDate' in data else None
        return cls(name, identifier, bundle, expiration, features)
    
    @classmethod
    def list_from_api(cls, data: dict):
        return [cls.from_api(d) for d in data['appIds']]


class AppGroup:
    def __init__(
        self,
        group_identifier: str,
        name: str,
        status: str,
        prefix: str,
        identifier: str
    ):
        self.group_identifier = group_identifier
        self.name = name
        self.status = status
        self.prefix = prefix
        self.identifier = identifier

    def __repr__(self):
        return f"AppGroup({self.group_identifier!r}, {self.name!r}, {self.status!r}, " \
               f"{self.prefix!r}, {self.identifier!r})"

    @classmethod
    def from_api(cls, data: dict):
        return cls(
            data['applicationGroup'],
            data['name'],
            data['status'],
            data['prefix'],
            data['identifier']
        )

