import secrets

# 2^1279 - 1, a Mersenne prime. Holds 159 full bytes (1272 bits).
PRIME = (1 << 1279) - 1
MAX_CHUNK = 159
VALUE_LEN = 160  # 1280 bits serialization for the residue
SHARE_LEN = 1 + VALUE_LEN  # 1 byte x-index + 160 bytes value


class ChannelShareSplit:
    """K-of-N Shamir over GF(PRIME) with length-aware shares.

    Every share carries its x-index; every *set* of shares carries the
    plaintext length implicitly via a length-prefixed first chunk.
    Chunks are <= 159 bytes so every residue fits PRIME.
    """

    LEN_PREFIX = 4  # 4-byte big-endian total length

    def __init__(self, k: int, n: int) -> None:
        if not (1 <= k <= n):
            raise ValueError("need 1 <= k <= n")
        self.k, self.n = k, n

    # ---- single-chunk primitives -------------------------------------

    def _split_value(self, secret: bytes) -> list[bytes]:
        if len(secret) > MAX_CHUNK:
            raise ValueError(
                f"chunk too large: {len(secret)} > {MAX_CHUNK}"
            )
        num = int.from_bytes(secret, "big") if secret else 0
        if num >= PRIME:
            raise ValueError("chunk residue out of range")
        coeffs = [num] + [secrets.randbelow(PRIME) for _ in range(self.k - 1)]
        shares = []
        for x in range(1, self.n + 1):
            y = 0
            for c in reversed(coeffs):
                y = (y * x + c) % PRIME
            shares.append(bytes([x]) + y.to_bytes(VALUE_LEN, "big"))
        return shares

    def _recombine_value(self, shares: list[bytes]) -> int:
        if len(shares) < self.k:
            raise ValueError("not enough shares")
        pts = []
        seen = set()
        for s in shares:
            if len(s) != SHARE_LEN:
                raise ValueError("bad share length")
            xi = s[0]
            if xi == 0 or xi in seen:
                raise ValueError("bad or duplicate share index")
            seen.add(xi)
            yi = int.from_bytes(s[1:], "big")
            if yi >= PRIME:
                raise ValueError("share value out of range")
            pts.append((xi, yi))

        secret = 0
        for i, (xi, yi) in enumerate(pts):
            num, den = 1, 1
            for j, (xj, _) in enumerate(pts):
                if i == j:
                    continue
                num = (num * xj) % PRIME
                den = (den * (xj - xi)) % PRIME
            term = yi * num * pow(den, PRIME - 2, PRIME)
            secret = (secret + term) % PRIME
        return secret

    # ---- public single-chunk API (test-friendly) ---------------------

    def split(self, secret: bytes) -> list[bytes]:
        """Split exactly one chunk (<= 159 bytes)."""
        return self._split_value(secret)

    def recombine(self, shares: list[bytes], length: int | None = None) -> bytes:
        """Recombine one chunk. If length is None, the natural
        (minimal) byte length is returned, preserving no leading
        zeros — use split_chunked()/recombine_chunked() for full
        length preservation."""
        num = self._recombine_value(shares)
        if length is None:
            length = (num.bit_length() + 7) // 8 or 1
        if length > VALUE_LEN:
            raise ValueError("length exceeds VALUE_LEN")
        return num.to_bytes(length, "big")

    # ---- chunked API (preserves exact length incl. leading zeros) ----

    def split_chunked(self, secret: bytes) -> list[list[bytes]]:
        prefixed = len(secret).to_bytes(self.LEN_PREFIX, "big") + secret
        # pad to multiple of MAX_CHUNK with zeros
        pad = (-len(prefixed)) % MAX_CHUNK
        padded = prefixed + b"\x00" * pad
        chunks = [
            padded[i:i + MAX_CHUNK]
            for i in range(0, len(padded), MAX_CHUNK)
        ]
        return [self._split_value(c) for c in chunks]

    def recombine_chunked(self, chunk_shares: list[list[bytes]]) -> bytes:
        if not chunk_shares:
            raise ValueError("no chunks")
        chunk_count = len(chunk_shares)
        # each chunk's real content is the right-aligned tail of the residue
        widths = [
            self._recombine_value(shares).to_bytes(MAX_CHUNK, "big")
            for shares in chunk_shares
        ]
        # for chunks 0..N-2, the real content is `widths[i]` exactly
        # for the last chunk, real content is `widths[-1][-real_last_len:]`
        # but we don't know real_last_len without the length prefix...
        # so: concatenate ALL of widths[-1] too (padding is zeros), then
        # slice by length prefix
        prefixed_padded = b"".join(widths)  # N * MAX_CHUNK bytes, tail-padded
        if len(prefixed_padded) < self.LEN_PREFIX:
            raise ValueError("too short")
        total_len = int.from_bytes(prefixed_padded[:self.LEN_PREFIX], "big")
        if total_len > len(prefixed_padded) - self.LEN_PREFIX:
            raise ValueError("declared length exceeds recovered buffer")
        return prefixed_padded[self.LEN_PREFIX:self.LEN_PREFIX + total_len]

    def combine_for_channel(
        self, chunked_shares: list[list[bytes]], channel_idx: int
    ) -> bytes:
        """Produce the single blob a given channel receives."""
        if channel_idx >= self.n:
            raise ValueError("channel index out of range")
        return b"".join(chunk[channel_idx] for chunk in chunked_shares)


    def split_combined_blob(
        self, combined: bytes, chunk_count: int
    ) -> list[bytes]:
        """Split a channel's combined blob back into per-chunk shares."""
        expected = chunk_count * SHARE_LEN
        if len(combined) != expected:
            raise ValueError(
                f"combined blob length {len(combined)} != {expected}"
            )
        return [
            combined[i * SHARE_LEN:(i + 1) * SHARE_LEN]
            for i in range(chunk_count)
        ]
