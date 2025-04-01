import plistlib as plist

from ..auth import XcodeAuth
from .base import XBaseRequest

from requests import Session


class Account:
    def __init__(
        self,
        email: str,
        status: str,
        lfirst: str,
        llast: str,
        first: str,
        last: str,
        developer_id: str,
        person_id: int,
    ):
        self.email = email
        self.status = status
        self.lfirst = lfirst
        self.llast = llast
        self.first = first
        self.last = last
        self.developer_id = developer_id
        self.person_id = person_id

    def __repr__(self):
        return f"{self.__class__.__name__}({self.email!r}, {self.status!r}, {self.person_id!r}, {self.first!r}, {self.last!r})"

    @property
    def name(self):
        return f"{self.first} {self.last}"

    @classmethod
    def from_api(cls, data: dict):
        return cls(
            data['email'],
            data['developerStatus'],
            data['firstName'],
            data['lastName'],
            data['dsFirstName'] if isinstance(data['dsFirstName'], str) else data['firstName'],
            data['dsLastName'] if isinstance(data['dsLastName'], str) else data['lastName'],
            data['developerId'],
            data['personId'],
        )


class XAccountRequest(XBaseRequest):
    URL = XBaseRequest.QH_URL + "viewDeveloper.action"

    def fetch(self, session: Session | None = None) -> Account:
        if session is None: session = self.session
        return Account.from_api(plist.loads(session.send(session.prepare_request(self)).text)['developer'])
