import hmac
import json
from pprint import pp
import plistlib as plist
from functools import lru_cache
from hashlib import sha256
from base64 import b64encode

from .utils import encrypt_password, decrypt_gcm, decrypt_cbc
from .models import IDMSAuthToken, GSAuthToken, GSAuthTokens, XcodeAuthToken
from ..utils.anisette import Anisette

from httpx import Auth, Client, Request
from srp import User, SHA256, NG_2048


class GSUserAuth(Auth):
    def __init__(
        self,
        email: str,
        password: str,
        anisette: Anisette,
    ):
        self.email = email
        self.password = password
        self.anisette = anisette

    def __repr__(self):
        return f"{self.__class__.__name__}({self.email})"

    @property
    def _base_headers(self):
        return {
            "User-Agent": "akd/1.0 CFNetwork/978.0.7 Darwin/18.7.0",
        }

    def sync_auth_flow(self, request: Request):
        request.headers.update(self.anisette.headers | self._base_headers)
        yield request

    async def async_auth_flow(self, request: Request):
        request.headers.update(self.anisette.headers | self._base_headers)
        yield request


class GSAuthSync(Client):
    BASE_URL = "https://gsa.apple.com/"

    def __init__(self, auth: GSUserAuth):
        self._auth = auth
        self.anisette = auth.anisette
        super().__init__(base_url=self.BASE_URL, auth=self._auth, verify=False)

    @property
    def _base_body(self):
        return {
            "Header": { "Version": "1.0.1" },
            "Request": { "cpd": self.anisette.cpd }
        }

    def _base_body_with(self, params: dict):
        r = self._base_body
        r["Request"] |= params
        return r

    def _auth_request(self, params: dict) -> dict:
        return plist.loads(self.post('/grandslam/GsService2', headers={"Content-Type": "text/x-xml-plist", "Accept": "*/*"}, content=plist.dumps(self._base_body_with(params)), timeout=5).content)["Response"]

    def _check_error(self, r: dict) -> bool:
        status = r["Status"] if "Status" in r else r
        if status["ec"] != 0:
            print(f"Error {status['ec']}: {status['em']}")
            return True
        return False

    @lru_cache()
    def login(self, sms: bool = False):
        usr = User(self._auth.email, bytes(), hash_alg=SHA256, ng_type=NG_2048)
        _, A = usr.start_authentication()
        init = self._auth_request({
            "A2k": A,
            "ps": ["s2k", "s2k_fo"],
            "u": self._auth.email,
            "o": "init",
        })
        if self._check_error(init): raise ValueError("init Response returned error!")
        if init["sp"] != "s2k": raise ValueError(f"This implementation currently only supports \"s2k\" not {init['sp']!r}!")

        usr.p = encrypt_password(self._auth.password, init["s"], init["i"]) # type: ignore
        M = usr.process_challenge(init["s"], init["B"])
        if M is None: raise ValueError(f"Failed to process challenge for {self._auth.email}!")

        complete = self._auth_request({
            "c": init["c"],
            "M1": M,
            "u": self._auth.email,
            "o": "complete",
        })
        if self._check_error(complete): raise ValueError("complete Response returned error!")
        usr.verify_session(complete["M2"])
        if not usr.authenticated: raise ValueError("Failed to verify session!")
        spd = plist.loads(plist.PLISTHEADER + decrypt_cbc(usr, complete["spd"])) # type: ignore

        def auth_sms(token: str):
            headers = {
                "X-Apple-Identity-Token": token,
                "X-Apple-App-Info": "com.apple.gs.xcode.auth",
                "X-Xcode-Version": "16.0 (16A242d}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            }
            # old was self.put('/auth/verify/phone/', headers=headers, timeout=5)
            if (auth := self.get('/auth', headers=headers, timeout=5)).is_error: raise ValueError(auth.content)
            code = int(input("2FA Code: "))
            body = json.dumps({"phoneNumber": {"id": 1}, "securityCode": {"code": f"{code:06}"}, "mode": "sms"}, separators=(',', ':'))
            return self.post('/auth/verify/phone/securitycode', headers=headers, content=body, timeout=5)

        def auth_trusted(token: str):
            headers = {
                "X-Apple-Identity-Token": token,
            }
            self.get('/auth/verify/trusteddevice', headers=headers, timeout=5)
            code = int(input("2FA Code: "))
            headers['security-code'] = f"{code:06}"
            return self.get('/grandslam/GsService2/validate', headers=headers, timeout=5)

        auth_type = complete["Status"]["au"] if "au" in complete["Status"] else "authenticated"
        if auth_type == "authenticated":
            # we're authenticated!
            return spd
        elif auth_type == "trustedDeviceSecondaryAuth":
            # This means we can either use a trusted device or SMS
            # if the user specified SMS we can use that here
            auth = auth_sms if sms else auth_trusted
        elif auth_type == "secondaryAuth":
            # user doesn't have a proper trusted device, forced SMS
            auth = auth_sms
        else:
            raise ValueError(f"Unknown authentication value {auth_type}!")
        # X-Apple-Identity-Token
        token = b64encode(f"{spd['adsid']}:{spd['GsIdmsToken']}".encode()).decode()
        if (auth_r := auth(token)).is_error: raise ValueError(f"{'SMS' if auth == auth_sms else 'Trusted'} 2FA code verification failed! {auth_r}")
        # if we've fell through here, that means our device is trusted now
        # another round of authentication will return tokens above
        return self.login(sms)

    def _make_checksum(self, app: str, session_key: bytes, dsid: str) -> bytes | None:
        hmac_ctx = hmac.new(session_key.encode() if isinstance(session_key, str) else session_key, digestmod=sha256)
        for s in ["apptokens", dsid, app]: hmac_ctx.update(s.encode())
        return hmac_ctx.digest()

    def _fetch_app_token(self, idms: IDMSAuthToken, app: str) -> GSAuthToken:
        if 'com.apple.gs.' not in app: app = 'com.apple.gs.' + app
        checksum = self._make_checksum(app, idms.sk, idms.adsid)
        get_token = self._auth_request({
            "app": [app],
            "c": idms.c,
            "checksum": checksum,
            "cpd": self.anisette.cpd,
            "o": "apptokens",
            "t": idms.token,
            "u": idms.adsid,
        })
        if self._check_error(get_token): raise ValueError(get_token)
        token = decrypt_gcm(get_token['et'], idms.sk)
        if token is None: raise ValueError(get_token)
        return GSAuthTokens(plist.loads(plist.PLISTHEADER + token)['t']).tokens[0] # type: ignore

    def fetch_xcode_token(self) -> XcodeAuthToken:
        idms = IDMSAuthToken.from_spd(self.login())
        return XcodeAuthToken(self._fetch_app_token(idms, "xcode.auth").token, idms.adsid)

    def fetch_idms_token(self, idms: IDMSAuthToken | None = None) -> IDMSAuthToken:
        if idms is None: return IDMSAuthToken.from_spd(self.login())
        return IDMSAuthToken(self._fetch_app_token(idms, 'idms.auth').token, idms.adsid, idms.sk, idms.c)

