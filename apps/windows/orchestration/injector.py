from pathlib import Path
import hashlib

from payload.fec import FecCodec
from payload.encrypt import AtsKeyedCipher
from payload.split import ChannelShareSplit
from output.manifest import RunManifest, OutputMode, ChannelVerification
from persistence.forensic.silent_failure import SilentFailure
from channel.base import SubmissionEvent


class ResumeInjector:
    def __init__(
        self,
        channels,
        semantic_channels,
        multi_artifact_channels,
        submission_channels,
        mode: OutputMode,
        lang: str,
        ats: str,
        passphrase: bytes,
    ) -> None:
        self.channels = channels
        self.semantic_channels = semantic_channels
        self.multi_artifact_channels = multi_artifact_channels
        self.submission_channels = submission_channels
        self.mode = mode
        self.lang = lang
        self.ats = ats
        self.cipher = AtsKeyedCipher(passphrase)

    def inject_bundle(
        self,
        bundle: list[Path],
        payload: bytes,
        manifest_out: Path | None = None,
    ) -> RunManifest:
        if not bundle:
            raise ValueError("empty bundle")

        encrypted = self.cipher.encrypt(self.ats, payload)
        fec_shards = FecCodec().encode(encrypted)
        n = max(len(self.channels), 3)
        splitter = ChannelShareSplit(k=min(3, n), n=n)
        chunked_shares = splitter.split_chunked(fec_shards[0])

        manifest = RunManifest(
            input_bundle=[str(p) for p in bundle],
            output_mode=self.mode.value,
            ats_target=self.ats,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            payload_bits=len(payload) * 8,
            shamir_k=splitter.k,
            chunks=len(chunked_shares),
            channels_requested=[c.name for c in self.channels],
            reference_order=[p.name for p in bundle],
        )

        for i, channel in enumerate(self.channels):
            if i >= len(chunked_shares[0]):
                break
            combined = splitter.combine_for_channel(chunked_shares, i)
            wrapped = SilentFailure.wrap(channel.inject)
            result = wrapped(bundle, combined)
            recovered = b""
            if result is not None:
                manifest.channels_survived.append(channel.name)
                recovered = combined
            manifest.verifier[channel.name] = ChannelVerification(
                channel=channel.name,
                survived=result is not None,
                bytes_recovered=len(recovered),
                corruption=0.0 if result is not None else 1.0,
                bits_recovered=len(recovered) * 8,
            )

        for ma in self.multi_artifact_channels:
            wrapped = SilentFailure.wrap(ma.inject)
            res = wrapped(bundle, fec_shards[1])
            survived = res is not None
            if survived:
                manifest.channels_survived.append(ma.name)
            manifest.verifier[ma.name] = ChannelVerification(
                channel=ma.name,
                survived=survived,
                bytes_recovered=len(fec_shards[1]) if survived else 0,
                corruption=0.0 if survived else 1.0,
                bits_recovered=(len(fec_shards[1]) * 8) if survived else 0,
            )

        if self.semantic_channels:
            any_doc = bundle[0]
            try:
                text = any_doc.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            for sc in self.semantic_channels:
                wrapped = SilentFailure.wrap(sc.inject)
                out = wrapped(text, fec_shards[2] if len(fec_shards) > 2 else fec_shards[0])
                survived = out is not None and out != text
                if survived:
                    manifest.channels_survived.append(sc.name)
                manifest.verifier[sc.name] = ChannelVerification(
                    channel=sc.name,
                    survived=survived,
                    bytes_recovered=len(fec_shards[2]) if survived and len(fec_shards) > 2 else 0,
                    corruption=0.0 if survived else 1.0,
                    bits_recovered=0,
                )

        if manifest_out is not None:
            manifest.write(manifest_out)

        return manifest

    def inject_submission(
        self, event: SubmissionEvent, payload: bytes
    ) -> SubmissionEvent:
        result = event
        for ch in self.submission_channels:
            wrapped = SilentFailure.wrap(ch.inject)
            maybe = wrapped(result, payload)
            if maybe is not None:
                result = maybe
        return result
