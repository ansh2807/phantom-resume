import hashlib
import secrets
from time import time

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


class AtsKeyedCipher:
    """Key = sha256(passphrase | ats | bucket_idx). AAD binds the
    declared bucket so header tampering invalidates the tag."""

    def __init__(self, operator_passphrase: bytes, bucket_hours: int = 168) -> None:
        if len(operator_passphrase) < 12:
            raise ValueError("passphrase must be at least 12 bytes")
        self._pass = operator_passphrase
        self._bucket_seconds = bucket_hours * 3600

    def _derive(self, ats: str, bucket_idx: int) -> bytes:
        material = b"|".join([
            self._pass,
            ats.encode(),
            bucket_idx.to_bytes(8, "big"),
        ])
        return hashlib.sha256(material).digest()

    def _aad(self, ats: str, bucket_idx: int) -> bytes:
        return ats.encode() + b"|" + bucket_idx.to_bytes(8, "big")

    def encrypt(self, ats: str, plaintext: bytes) -> bytes:
        bucket_idx = int(time()) // self._bucket_seconds
        key = self._derive(ats, bucket_idx)
        nonce = secrets.token_bytes(12)
        ct = ChaCha20Poly1305(key).encrypt(
            nonce, plaintext, self._aad(ats, bucket_idx)
        )
        return bucket_idx.to_bytes(8, "big") + nonce + ct

    def decrypt(self, ats: str, blob: bytes) -> bytes | None:
        if len(blob) < 20:
            return None
        header_bucket = int.from_bytes(blob[:8], "big")
        nonce, ct = blob[8:20], blob[20:]
        key = self._derive(ats, header_bucket)
        try:
            return ChaCha20Poly1305(key).decrypt(
                nonce, ct, self._aad(ats, header_bucket)
            )
        except Exception:
            return None
