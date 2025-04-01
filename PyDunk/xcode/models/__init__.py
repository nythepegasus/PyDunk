import plistlib as plist

from ...auth.models import GSAuthToken, Anisette
from ..auth import XcodeAuth
from .account import Account, XAccountRequest
from .team import Team, XTeamsRequest

from requests import Session



class XcodeSession(Session):
    def __init__(
        self,
        auth: XcodeAuth,
    ):
        super().__init__()
        self.auth = auth
        self.verify = False

        self._account = None
        self._teams = []

    @classmethod
    def from_dsid_token(
        cls, 
        dsid: str,
        token: str | GSAuthToken,
        anisette: Anisette | None = None,
    ):
        return cls(XcodeAuth(dsid, token, anisette))

    @property
    def account(self):
        if self._account is None: self._account = self.refresh_account()
        return self._account

    def refresh_account(self):
        return Account.from_api(
            plist.loads(self.send(self.prepare_request(XAccountRequest(self.auth))).text)['developer']
        )

    @property
    def teams(self):
        if len(self._teams) == 0: self._teams = self.refresh_teams()
        return self._teams

    def refresh_teams(self):
        return Team.list_from_api(plist.loads(self.send(self.prepare_request(XTeamsRequest(self.auth))).text))


