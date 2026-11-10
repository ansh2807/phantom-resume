# channel/submission/filename_charset.py
class FilenameCharsetChannel:
    name = "filename_charset"
    SEPARATORS = ["__", "--", "..", "-_-"]

    def encode_name(self, stem: str, ext: str, symbol: int) -> str:
        sep = self.SEPARATORS[symbol & 0x03]
        return f"{stem}{sep}cv{ext}"

    def decode_name(self, filename: str) -> int:
        for idx, sep in enumerate(self.SEPARATORS):
            if f"{sep}cv" in filename:
                return idx
        return 0
