from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json
import uuid


class OutputMode(str, Enum):
    DIRECT_PDF = "direct_pdf"
    RENDERED_PDF = "rendered_pdf"
    DOCX = "docx"


@dataclass
class ChannelVerification:
    channel: str
    survived: bool
    bytes_recovered: int
    corruption: float
    bits_recovered: int

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "ChannelVerification":
        return cls(
            channel=data.get("channel", name),
            survived=bool(data.get("survived", False)),
            bytes_recovered=int(data.get("bytes_recovered", 0)),
            corruption=float(data.get("corruption", 0.0)),
            bits_recovered=int(data.get("bits_recovered", 0)),
        )


@dataclass
class RunManifest:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    input_bundle: list[str] = field(default_factory=list)
    output_mode: str = OutputMode.DOCX.value
    channels_requested: list[str] = field(default_factory=list)
    channels_survived: list[str] = field(default_factory=list)
    payload_sha256: str = ""
    payload_bits: int = 0
    ats_target: str | None = None
    reference_order: list[str] = field(default_factory=list)
    payload_codec_id: str = ""
    shamir_k: int = 0
    chunks: int = 1
    decoys_emitted: int = 0
    attention_plan: dict | None = None
    verifier: dict[str, ChannelVerification] = field(default_factory=dict)

    def write(self, path: Path) -> None:
        payload = asdict(self)
        payload["verifier"] = {
            k: {
                "channel": v.channel,
                "survived": v.survived,
                "bytes_recovered": v.bytes_recovered,
                "corruption": v.corruption,
                "bits_recovered": v.bits_recovered,
            }
            for k, v in self.verifier.items()
        }
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "RunManifest":
        raw = json.loads(path.read_text(encoding="utf-8"))
        verifier_raw = raw.pop("verifier", {})
        manifest = cls(**raw)
        manifest.verifier = {
            name: ChannelVerification.from_dict(name, data)
            for name, data in verifier_raw.items()
        }
        return manifest
