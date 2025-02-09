from pprint import pp

from .auth import GSAuth
from .auth.models.anisette import Anisette
from .auth.models import GSAuthToken, GSAuthTokens
from .xcode.models import XcodeAuth
from .xcode import XcodeSession

from requests import Response


def main() -> tuple[GSAuth, XcodeAuth | tuple]:
    import os
    from getpass import getpass
    username = os.environ.get("APPLE_ID")
    if not username: username = input("Apple ID: ")
    password = os.environ.get("APPLE_ID_PASSWORD")
    if not password: password = getpass("Password: ")
    serial = os.environ.get("APPLE_SERIAL")
    ani = Anisette(serial=serial)
    auth = GSAuth(ani)
    return (auth, auth.fetch_xcode_token(username, password))


m = main()
a = m[0]
def parse_tokens(data: dict):
    for k, v in data.items():
        print(f"{k}: {v['expiry']}\n{v['token']}")

#tokens = 
#parse_tokens(tokens)

if isinstance(m[1], XcodeAuth):
    x = XcodeSession(m[1])
