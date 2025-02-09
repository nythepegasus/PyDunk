import json
import plistlib
from pprint import pp
from uuid import uuid4

from requests import Session
from requests.exceptions import JSONDecodeError


class SessionProvider:
    def __init__(self, session: Session | None = None):
        self.__session = session

    @property
    def _session(self) -> Session:
        if self.__session is None: self.__session = Session()
        return self.__session

    @_session.setter
    def _session(self, new: Session):
        if not isinstance(new, Session): raise ValueError(f"{type(new)} is not of type Session!")
        self.__session = new

    @staticmethod
    def _plist_from(data: str | bytes, prepend_header: bool = False) -> dict:
        if not prepend_header: return plistlib.loads(data.encode()) if isinstance(data, str) else plistlib.loads(data)
        return plistlib.loads(plistlib.PLISTHEADER + data.encode()) if isinstance(data, str) else plistlib.loads(plistlib.PLISTHEADER + data)

    @staticmethod
    def _plist_to_bytes(data: dict) -> bytes:
        return plistlib.dumps(data)

    @staticmethod
    def _stripped_json(data: dict) -> str:
        return json.dumps(data).replace(" ", "")

    @property
    def _base_json_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    def _json_headers(self, extra: dict | None = None) -> dict:
        return ({} if extra is None else extra) | self._base_json_headers

    def _dict_json_request(self, base_url: str, json: dict | None = None, headers: dict[str, str] | None = None, params: dict[str, str] | None = None) -> dict:
        if json is None: 
            r = self._session.post(url=base_url, params=params or {}, headers=self._json_headers(headers))
            try: return r.json()
            except JSONDecodeError: 
                if r.ok and r.content == b'': return {}
                return r
        r = self._session.post(url=base_url, params=params or {}, headers=self._json_headers(headers), data=self._stripped_json(json))
        try: return r.json()
        except JSONDecodeError: 
            if r.ok and r.content == b'': return {}
            return r

    def _bytes_json_request(self, base_url: str, data: bytes | None = None, headers: dict[str, str] | None = None, params: dict[str, str] | None = None) -> dict:
        if data is None: return self._session.post(url=base_url, params=params or {}, headers=self._json_headers(headers)).json()
        return self._session.post(url=base_url, params=params or {}, headers=self._json_headers(headers), data=data).json()

    @property
    def _base_plist_headers(self) -> dict[str, str]:
        return {
            "Accept": "text/x-xml-plist",
            "Content-Type": "text/x-xml-plist",
        }

    def _plist_headers(self, extra: dict | None = None) -> dict[str, str]:
        return ({} if extra is None else extra) | self._base_plist_headers

    def _dict_plist_request(self, base_url: str, plist: dict, headers: dict[str, str] | None = None, params: dict[str, str] | None = None) -> dict:
        params = params or {}
        plist |= {
            "requestId": str(uuid4()).upper(),
        }
        resp = self._session.post(url=base_url, params=params, headers=self._plist_headers(headers), data=self._plist_to_bytes(plist))
        if not resp.ok:
            raise ValueError(f"{resp.status_code} was returned:\n{resp.content.decode()}")
        try:
            return self._plist_from(resp.content)
        except plistlib.InvalidFileException:
            raise ValueError(f"Invalid plist returned:\n{resp.content.decode()}")
        except Exception as e:
            pp(resp)
            raise e
