import hashlib


class PrivateCodebook:
    def __init__(self, seed: bytes) -> None:
        self._seed = seed

    @classmethod
    def derive(
        cls, ats: str, operator: str, probe_history: list[str]
    ) -> "PrivateCodebook":
        material = b"|".join([
            ats.encode(),
            operator.encode(),
            b"|".join(p.encode() for p in probe_history),
        ])
        return cls(hashlib.sha256(material).digest())

    def channel_id(self, channel_name: str) -> str:
        h = hashlib.sha256(self._seed + channel_name.encode()).hexdigest()
        return h[:16]
