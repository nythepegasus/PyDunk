from .account import Account
from .auth import XcodeAuth
from .device import Device
from .team import Team
from ...common import SessionProvider


class XSDevices(SessionProvider):
    _BASE = "devices"

    def __init__(
        self,
        team: Team,
        auth: XcodeAuth,
    ):
        super().__init__()
        self._auth = auth
        self._team = team
        self._session = self._auth._session

        self._devices: list[Device] | None = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self._team!r})"

    @property
    def _BASE_URL(self) -> str:
        return self._auth.SERVICES_BASE_URL + self._BASE
    
    @property
    def _body(self) -> dict[str, str]:
        return {"teamId": self._team.identifier}

    def _headers(self, extra: dict | None = None) -> dict[str, str]:
        return ({} if extra is None else extra) | self._auth.headers

    @property
    def _get_headers(self) -> dict[str, str]:
        return self._headers({"X-HTTP-Method-Override": "GET"})

    def refresh_devices(self) -> list[Device]:
        resp = self._dict_json_request(self._BASE_URL, self._body, self._get_headers)
        #pp(resp)
        self._devices = [Device.from_api(d) for d in resp['data']]
        return self._devices

    @property
    def devices(self) -> list[Device]:
        if self._devices is None: self._devices = self.refresh_devices()
        return self._devices


class XSTeam:
    def __init__(
        self,
        team: Team,
        auth: XcodeAuth,
    ):
        self.team = team
        self.identifier = self.team.identifier
        self._auth = auth
        self._devices = None
        self.xdevices = XSDevices(self.team, self._auth)


    def __repr__(self):
        return f"{self.__class__.__name__}({self.team!r})"

    @property
    def devices(self) -> list[Device]:
        if self._devices is None: self._devices = self.xdevices.refresh_devices()
        return self._devices

    def refresh_devices(self) -> list[Device]:
        self._devices = self.xdevices.refresh_devices()
        return self._devices


class XSTeams(SessionProvider):
    _BASE = "listTeams.action"

    def __init__(
        self,
        account: Account,
        auth: XcodeAuth,
    ):
        super().__init__()
        self._auth = auth
        self._account = account
        self._session = self._auth._session

        self._teams = None
        self._team = None
    
    def _request(self):
        return self._dict_plist_request(self._BASE_URL, self._auth.body, self._auth.headers)

    def __getitem__(self, item: int | str) -> XSTeam:
        if isinstance(item, int): return self.teams[item]
        elif isinstance(item, str): 
            try:
                return [t for t in self.teams if t.team.identifier == item][0]
            except IndexError:
                raise KeyError(f"Team ID {item!r} was not found in {self.__class__.__name__}!")
        else: raise ValueError(f"{type(item)} is not expected int or str!")

    @property
    def _BASE_URL(self):
        return self._auth.BASE_URL + self._BASE

    def refresh_teams(self) -> list[XSTeam]:
        self._teams = [XSTeam(Team.from_api_with_account(self._account, t), self._auth) for t in self._request()['teams']]
        self._team = next(iter(self._teams))
        return self._teams

    @property
    def teams(self) -> list[XSTeam]:
        if self._teams: return self._teams
        return self.refresh_teams()

    @property
    def team(self) -> XSTeam:
        if self._team: return self._team
        return self.refresh_teams()[0]



