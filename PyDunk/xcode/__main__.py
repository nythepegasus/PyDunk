import os
import json
from pprint import pp
from getpass import getpass

from . import XcodeSession
from ..auth.models import Anisette


adsid = os.environ.get("APPLE_DSID")
if not adsid: adsid = input("Apple DSID: ")
token = os.environ.get("APPLE_XCODE_TOKEN")
if not token: token = getpass("'com.apple.gs.xcode.auth' token: ")
ani = Anisette()
ani._session.verify = False
x = XcodeSession.from_dsid_token_anisette(adsid, token)
c = x.fetch_capabilities()
