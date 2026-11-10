from dataclasses import replace
from datetime import datetime, timedelta, timezone

from channel.base import SubmissionEvent


class TimingMinuteChannel:
    """Encodes one symbol (2 bits) per event as the minute-of-hour
    quadrant of `submitted_at_utc`. Symbol 0..3 maps to minute target
    0, 15, 30, 45 respectively. `inject` schedules the event to the
    next future time in the target quadrant; `extract` reads the
    quadrant back."""

    name = "timing_minute"

    def inject(self, event: SubmissionEvent, payload: bytes) -> SubmissionEvent:
        if not payload:
            return event
        symbol = payload[0] & 0x03
        target_minute = symbol * 15
        now = datetime.now(timezone.utc)
        current_minute = now.minute
        current_second = now.second
        # minutes to advance to the target quadrant
        advance = (target_minute - (current_minute % 60)) % 60
        # pick a second inside the quadrant (mid-quadrant, e.g. :07)
        # so we're unambiguously inside [target_minute, target_minute+15)
        target_second = 7
        if advance == 0 and current_second >= target_second:
            # we're already in the quadrant but past the sample second;
            # advance a full hour to land safely in the next occurrence
            advance = 60
        scheduled = (
            now.replace(second=target_second, microsecond=0)
            + timedelta(minutes=advance)
        )
        return replace(event, submitted_at_utc=scheduled.isoformat())

    def extract(self, events: list[SubmissionEvent]) -> bytes | None:
        if not events:
            return None
        out = bytearray()
        for ev in events:
            dt = datetime.fromisoformat(ev.submitted_at_utc)
            quadrant = dt.minute // 15
            out.append(quadrant & 0x03)
        return bytes(out)
