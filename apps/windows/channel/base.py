from typing import Protocol
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SubmissionEvent:
    filename: str
    submitted_at_utc: str
    sequence: int
    ats: str


class SemanticChannel(Protocol):
    name: str
    def inject(self, text: str, payload: bytes) -> str: ...
    def extract(self, text: str) -> bytes | None: ...
    def capacity_bits(self, text: str) -> int: ...


class MultiArtifactChannel(Protocol):
    name: str
    def inject(self, bundle: list[Path], payload: bytes) -> list[Path]: ...
    def extract(self, bundle: list[Path]) -> bytes | None: ...


class SubmissionChannel(Protocol):
    name: str
    def inject(self, event: SubmissionEvent, payload: bytes) -> SubmissionEvent: ...
    def extract(self, events: list[SubmissionEvent]) -> bytes | None: ...
