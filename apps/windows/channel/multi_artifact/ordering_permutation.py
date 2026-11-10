import itertools
from math import factorial, log2
from pathlib import Path


class OrderingPermutationChannel:
    """Bundle order encodes bits. N files -> log2(N!) bits.
    `inject` produces a permuted bundle; `extract` requires the
    original reference order to reverse the permutation."""

    name = "ordering_permutation"
    min_files = 3

    def __init__(self, max_files: int = 6) -> None:
        self.max_files = max_files

    def _capacity(self, n: int) -> int:
        return int(log2(factorial(n)))

    def inject(self, bundle: list[Path], payload: bytes) -> list[Path]:
        n = min(len(bundle), self.max_files)
        if n < self.min_files:
            return bundle
        bits = int.from_bytes(payload, "big") if payload else 0
        cap = self._capacity(n)
        idx = bits % (2 ** cap)
        perms = list(itertools.permutations(range(n)))
        chosen = perms[idx]
        return [bundle[i] for i in chosen] + bundle[n:]

    def extract(
        self, bundle: list[Path], reference_order: list[str]
    ) -> bytes | None:
        if len(bundle) < self.min_files:
            return None
        n = min(len(bundle), self.max_files)
        names = [p.name for p in bundle[:n]]
        ref = [r for r in reference_order if r in names]
        if len(ref) != n:
            return None
        # Forward permutation: position k holds ref[stored_perm[k]]
        stored_perm = tuple(ref.index(names[k]) for k in range(n))
        perms = list(itertools.permutations(range(n)))
        if stored_perm not in perms:
            return None
        idx = perms.index(stored_perm)
        if idx >= 2 ** self._capacity(n):
            return None
        return idx.to_bytes((idx.bit_length() + 7) // 8 or 1, "big")
