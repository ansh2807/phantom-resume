from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class EncodedPayload:
    channel_shares: dict[str, bytes]
    checksum: bytes
    signature: bytes | None
    codebook_id: str


class PayloadCodec(Protocol):
    def encode(
        self, payload: bytes, channels: list[str], ats: str
    ) -> EncodedPayload: ...

    def decode(
        self, shares: dict[str, bytes], ats: str
    ) -> bytes | None: ...
