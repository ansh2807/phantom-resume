import os
from pathlib import Path


class TimestampDeltaChannel:
    """Encodes payload bytes as whole-millisecond positions/gaps between
    sorted mtimes. Immune to NTFS 100-ns rounding because the smallest
    meaningful unit is 4 ms per byte step — 40,000x coarser than the
    filesystem granularity.

    Encoding (N files encode N bytes):
        m[0] = BASE_MS + payload[0] * GAP_STEP
        m[i] = m[i-1] + GAP_BASE + payload[i] * GAP_STEP   for i >= 1
    where GAP_BASE = 1000 ms, GAP_STEP = 4 ms.
    """

    name = "timestamp_delta"
    BASE_MS = 1_700_000_000_000
    GAP_BASE = 1000
    GAP_STEP = 4

    def inject(self, bundle: list[Path], payload: bytes) -> list[Path]:
        if not bundle:
            return bundle
        cumulative_ms = self.BASE_MS
        for i, p in enumerate(bundle):
            byte_val = payload[i] if i < len(payload) else 0
            if i == 0:
                ms = self.BASE_MS + byte_val * self.GAP_STEP
            else:
                cumulative_ms += self.GAP_BASE + byte_val * self.GAP_STEP
                ms = cumulative_ms
            # ensure first file also participates in the gap chain
            if i == 0:
                cumulative_ms = ms
            ns = ms * 1_000_000
            os.utime(p, ns=(ns, ns))
        return bundle

    def extract(self, bundle: list[Path]) -> bytes | None:
        if not bundle:
            return None
        pairs = []
        for p in bundle:
            ms = int(os.stat(p).st_mtime_ns) // 1_000_000
            pairs.append((ms, p))
        pairs.sort()
        out = bytearray()
        # first byte from absolute position
        first_rel = pairs[0][0] - self.BASE_MS
        first_byte = round(first_rel / self.GAP_STEP)
        if first_byte < 0 or first_byte > 0xFF:
            return None
        out.append(first_byte)
        # remaining bytes from gaps
        prev_ms = pairs[0][0]
        for ms, _ in pairs[1:]:
            gap = ms - prev_ms
            rel = gap - self.GAP_BASE
            byte_val = round(rel / self.GAP_STEP)
            if byte_val < 0 or byte_val > 0xFF:
                return None
            out.append(byte_val)
            prev_ms = ms
        while out and out[-1] == 0:
            out.pop()
        return bytes(out) if out else None
