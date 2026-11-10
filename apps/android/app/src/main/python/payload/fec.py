import hashlib


class FecCodec:
    """Replica-tagged FEC. Each shard carries its replica index in the
    header so verification is position-independent, and majority vote
    requires strict > half (tie is rejected)."""

    MAGIC = b"FEC1"
    HEADER_LEN = 4 + 1 + 32  # magic + replica_index + sha256

    def __init__(self, replication: int = 3) -> None:
        if replication < 3:
            raise ValueError("replication must be >= 3 for majority vote")
        self.replication = replication

    def _header(self, replica_idx: int, body: bytes) -> bytes:
        digest = hashlib.sha256(body + bytes([replica_idx])).digest()
        return self.MAGIC + bytes([replica_idx]) + digest

    def encode(self, data: bytes) -> list[bytes]:
        shards: list[bytes] = []
        for i in range(self.replication):
            shards.append(self._header(i, data) + data)
        return shards

    def decode(self, shards: list[bytes]) -> bytes | None:
        if not shards:
            return None
        candidates: dict[bytes, int] = {}
        seen_replicas: set[int] = set()
        for shard in shards:
            if len(shard) < self.HEADER_LEN:
                continue
            if shard[:4] != self.MAGIC:
                continue
            replica_idx = shard[4]
            body = shard[self.HEADER_LEN:]
            expected = hashlib.sha256(body + bytes([replica_idx])).digest()
            if shard[5:self.HEADER_LEN] != expected:
                continue
            if replica_idx in seen_replicas:
                continue
            seen_replicas.add(replica_idx)
            candidates[body] = candidates.get(body, 0) + 1

        if not candidates:
            return None
        winner, count = max(candidates.items(), key=lambda kv: kv[1])
        # strict majority of *declared* replicas: count * 2 > replication
        if count * 2 <= self.replication:
            return None
        return winner
