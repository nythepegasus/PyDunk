import hmac
from hashlib import sha256

from srp import User, rfc5054_enable, no_username_in_x
from pbkdf2 import PBKDF2
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.padding import PKCS7 as padPKCS7


rfc5054_enable()
no_username_in_x()

def encrypt_password(password: str, salt: bytes, iterations: int) -> bytes:
    p = sha256(password.encode("utf-8")).digest()
    return PBKDF2(p, salt, iterations, sha256).read(32)

def create_session_key(usr: User, name: str) -> bytes:
    k = usr.get_session_key()
    if k is None: raise ValueError("Expected a session key from User object!")
    return hmac.new(k, name.encode(), sha256).digest()

def decrypt_cbc(usr: User, data: bytes) -> bytes:
    extra_data_key = create_session_key(usr, "extra data key:")
    extra_data_iv  = create_session_key(usr, "extra data iv:")
    extra_data_iv  = extra_data_iv[:16]

    cipher = Cipher(AES(extra_data_key), CBC(extra_data_iv))
    decryptor = cipher.decryptor()
    data = decryptor.update(data) + decryptor.finalize()
    padder = padPKCS7(128).unpadder()
    return padder.update(data) + padder.finalize()

def decrypt_gcm(data: bytes, session_key: bytes) -> bytes | None:
    if not session_key or len(data) < 35: return
    version_size, iv_size, tag_size = 3, 16, 16
    decrypted_size = len(data) - (version_size + iv_size + tag_size)
    if decrypted_size <= 0: return
    version = data[:version_size]
    iv = data[version_size:version_size + iv_size]
    cipher = data[version_size + iv_size:-tag_size]
    tag = data[-tag_size:]
    try: return AESGCM(session_key).decrypt(iv, cipher + tag, version)
    except: return

