from dataclasses import dataclass, field, asdict
from pathlib import Path
import json


@dataclass
class AtsProfile:
    schema_version: int = 1
    name: str = ""
    extractors: dict[str, str] = field(default_factory=dict)
    reliabilities: dict[str, float] = field(default_factory=dict)
    model_fingerprint: str | None = None
    detection_profile: dict[str, float] = field(default_factory=dict)
    variants: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "AtsProfile":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )

    def weight(self, channel: str) -> float:
        return self.reliabilities.get(channel, 0.0)
