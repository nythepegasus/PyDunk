from base64 import b64encode
from locale import getlocale
from uuid import UUID, uuid4
from datetime import datetime, UTC

from ...common import SessionProvider

from requests import Session


class Anisette(SessionProvider):
    """
    Anisette is required for authenticating with GrandSlam
    as well as communicating with most of Apple's APIs.

    Generally we have servers that aid in making this data for us.
    """
    
    def __init__(
        self,
        url: str = "https://ani.sidestore.io",
        serial: str | None = None,
        user: UUID | None = None,
        device: UUID | None = None,
        session: Session | None = None,
    ):
        super().__init__(session)

        self.url = url
        self._serial = serial

        self.user_id = str(user).upper() \
                       if user is UUID \
                       else str(uuid4()).upper()
        self.device_id = str(device).upper() \
                         if device is UUID \
                         else str(uuid4()).upper()

        self._data = None
        self._last = None

    def __repr__(self):
        return f"Anisette({self.url!r}{", " + "'" + self._serial + "'" if self._serial is not None else ""})"

    def _get_data(self) -> dict:
        self._data = self._session.get(self.url, verify=False).json()
        self._last = datetime.now()
        return self._data

    @property
    def last(self) -> datetime:
        if self._last is None: self._data = self._get_data()
        return self._last or datetime.now()

    @property
    def data(self) -> dict[str, str]:
        if self._data is None or (datetime.now().timestamp() - self.last.timestamp()) > 30: return self._get_data()
        return self._data

    @property
    def timestamp(self) -> str:
        return datetime.strftime(self.last, '%Y-%m-%dT%H:%M:%SZ') or self.data['X-Apple-I-Client-Time']

    @property
    def timezone(self) -> str:
        return datetime.now(UTC).astimezone().tzname() or "EST"

    @property
    def locale(self):
        return getlocale()[0] or "en_US"

    @property
    def otp(self) -> str:
        return self.data['X-Apple-I-MD']

    @property
    def local_user(self):
        return b64encode(self.user_id.encode()).decode()

    @property
    def machine(self) -> str:
        return self.data['X-Apple-I-MD-M']

    @property
    def router(self) -> str:
        return "17106176"

    @property
    def serial(self) -> str:
        return self._serial or self.data['X-Apple-I-SRL-NO']

    @serial.setter
    def serial(self, new: str):
        self._serial = new

    def build_client(self, device: str, app: str) -> str:
        os = "Windows" if device == "PC" else "macOS"
        ov = "6.2(0,0);9200" if device == "PC" else "15.2;24C5089c"
        bu = "com.apple."
        bu += "dt.Xcode" if app == "Xcode" else "iCloud"
        av = "3594.4.19" if app == "Xcode" else "7.21"

        akbundle = "com.apple.AuthKit"
        if os == "Windows": akbundle += "Win"
        akversion = "1"

        return f"<{device}> <{os};{ov}> <{akbundle}/{akversion} ({bu}/{av})>"

    @property
    def client(self):
        return self.build_client("MacPro5,1", "Xcode")

    def headers(self, client: bool = False) -> dict[str, str]:
        h = {
            "X-Apple-I-Client-Time": self.timestamp,
            "X-Apple-I-TimeZone": self.timezone,
            "loc": self.locale,
            "X-Apple-Locale": self.locale,
            "X-Apple-I-MD": self.otp,
            "X-Apple-I-MD-LU": self.local_user,
            "X-Apple-I-MD-M": self.machine,
            "X-Apple-I-MD-RINFO": self.router,
            "X-Mme-Device-Id": self.local_user,
            "X-Apple-I-SRL-NO": self.serial
        }
        if client:
            h |= {
                "X-Mme-Client-Info": self.client,
                "X-Apple-App-Info": "com.apple.gs.xcode.auth",
                "X-Xcode-Version": "16.0 (16A242d}"
            }
        return h

    @property
    def cpd(self) -> dict[str, str]:
        cpd = {
            "bootstrap": True,
            "icscrec": True,
            "pbe": False,
            "prkgen": True,
            "svct": "iCloud"
        }
        return cpd | self.headers()

