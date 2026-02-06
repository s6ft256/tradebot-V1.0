from __future__ import annotations

import base64

from cryptography.fernet import Fernet


class KeyEncryptor:
    def __init__(self, *, fernet_key_b64: str):
        self._fernet = Fernet(fernet_key_b64.encode("utf-8"))

    @staticmethod
    def generate_key_b64() -> str:
        return Fernet.generate_key().decode("utf-8")

    def encrypt_to_b64(self, plaintext: str) -> str:
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return base64.b64encode(token).decode("utf-8")

    def decrypt_from_b64(self, ciphertext_b64: str) -> str:
        token = base64.b64decode(ciphertext_b64.encode("utf-8"))
        return self._fernet.decrypt(token).decode("utf-8")
