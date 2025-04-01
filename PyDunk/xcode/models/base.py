
from ..auth import XcodeAuth

from requests import Session, Request


class XBaseRequest(Request):
    QH_URL = "https://developerservices2.apple.com/services/QH65B2/"
    V1_URL = "https://developerservices2.apple.com/services/v1/"

    URL = QH_URL + "viewDeveloper.action"
    
    def __init__(self, auth: XcodeAuth, session: Session | None = None):
        self.auth = auth
        self.session = session if session is not None else Session()
        self.session.auth = self.auth
        super().__init__('POST', self.URL, data=self._body, headers=auth.headers)

    PLIST_HEADERS = {
        "Accept": "text/x-xml-plist",
        "Content-Type": "text/x-xml-plist",
    }

    JSON_HEADERS = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }

    URLENCODED_HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    @property
    def _body(self) -> str | bytes:
        return self.auth.plist_body

    def plist_headers(self, extra: dict[str, str]) -> dict[str, str]:
        return extra | self.PLIST_HEADERS

    def json_headers(self, extra: dict[str, str]) -> dict[str, str]:
        return extra | self.JSON_HEADERS

    def urlencoded_headers(self, extra: dict[str, str]) -> dict[str, str]:
        return extra | self.URLENCODED_HEADERS

