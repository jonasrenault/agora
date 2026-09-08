import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from agora.api.models import EncryptedValue


def encrypt(plain_text: str, password: str) -> EncryptedValue:
    salt = get_random_bytes(16)
    # Derive a 32-byte key (AES-256) from password
    key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode("utf-8"))

    return EncryptedValue(
        salt=base64.b64encode(salt).decode("utf-8"),
        nonce=base64.b64encode(cipher.nonce).decode("utf-8"),
        tag=base64.b64encode(tag).decode("utf-8"),
        ciphertext=base64.b64encode(ciphertext).decode("utf-8"),
    )


def decrypt(encrypted_value: EncryptedValue, password: str):
    salt = base64.b64decode(encrypted_value.salt)
    nonce = base64.b64decode(encrypted_value.nonce)
    tag = base64.b64decode(encrypted_value.tag)
    ciphertext = base64.b64decode(encrypted_value.ciphertext)

    key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
