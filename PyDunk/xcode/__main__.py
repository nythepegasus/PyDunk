import os
from pprint import pp

from .auth import XcodeAuth, Anisette
from .models.account import XAccountRequest
from .models.team import XTeamsRequest, XQHAppIDRequest, XV1AppIDRequest, XQHiOSDeviceLimitsRequest, XQHMacDeviceLimitsRequest, XCapabilitiesRequest, XQHValidateDevicesRequest, Dev, XDevicesRequest, XProfilesRequest

from requests import Session

x = XcodeAuth(
    os.environ["APPLE_DSID"],
    os.environ["APPLE_XCODE_TOKEN"],
    Anisette(os.environ["APPLE_ANISETTE"], serial=os.environ["APPLE_SERIAL"])
)

nsd = Dev("tukacat", "00008130-00162CCA30E1401C")
s = Session()
s.verify = False

ar = XAccountRequest(x, s)
a = ar.fetch()
tr = XTeamsRequest(x, s)
t = tr.fetch()
ar = XQHAppIDRequest(x, t[0], s)
a = ar.fetch()
lir = XQHiOSDeviceLimitsRequest(x, t[0], s)
li = lir.fetch()
lmr = XQHMacDeviceLimitsRequest(x, t[0], s)
lm = lmr.fetch()
car = XCapabilitiesRequest(x, t[0], s)
ca = car.fetch()
dr = XDevicesRequest(x, t[0], s)
d = dr.fetch()
dvr = XQHValidateDevicesRequest(x, t[1], nsd, s)
dv = dvr.fetch()
pr = XProfilesRequest(x, t[0], s)
p = pr.fetch()
if len(t) > 1:
    oar = XQHAppIDRequest(x, t[1], s)
    oa = oar.fetch()
    odr = XDevicesRequest(x, t[1], s)
    od = odr.fetch()
    opr = XProfilesRequest(x, t[0], s)
    op = opr.fetch()

