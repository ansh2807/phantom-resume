import hashlib


class DecoyGenerator:
    def __init__(self, operator_seed: bytes) -> None:
        self._seed = operator_seed

    def decoy_for(self, ats: str, run_id: str) -> tuple[bytes, bytes]:
        key = hashlib.sha256(
            self._seed + ats.encode() + run_id.encode()
        ).digest()
        fake_plain = b"candidate_ref:" + key[:8].hex().encode()
        fake_key = hashlib.sha256(key + b"decoy").digest()
        return fake_plain, fake_key
