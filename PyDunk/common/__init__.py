
from requests.auth import AuthBase
from requests import Session, Request


class PDSession(Session):
    def __init__(self, auth, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(auth, AuthBase): raise ValueError(f"Expected AuthBase, got {auth!r} instead!")
        self.auth = auth
    
    def sendr(self, r: Request):
        return super().send(self.prepare_request(r))

    def req(self, r: Request):
        return self.prepare_request(r)
