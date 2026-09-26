"""§3 How text and characters are encoded.

Layers, from the bottom up:
  * ZSCII        the Z-machine's character set (§3.8): 32-126 are ASCII,
                 13 is newline, 155-251 are "extra characters" mapped to
                 Unicode by a translation table (§3.8.5).
  * z-characters 5-bit values packed three to a 16-bit word; the top bit of
                 the word marks the end of the string (§3.2).
  * alphabets    z-chars 6..31 index one of three alphabets A0/A1/A2
                 (§3.5). In v5, z-chars 4 and 5 shift the NEXT character
                 only into A1 / A2 (§3.2.3). z-char 0 is a space.
                 z-chars 1..3 introduce an abbreviation (§3.3).
                 A2 z-char 6 starts a 10-bit ZSCII escape (§3.4),
                 A2 z-char 7 is newline.
"""
from __future__ import annotations

from dataclasses import dataclass

# §3.5.3 default alphabet table (v2+)
DEFAULT_A0 = "abcdefghijklmnopqrstuvwxyz"
DEFAULT_A1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_A2 = " \n0123456789.,!?_#'\"/\\-:()"   # positions 6 and 7 are special

# §3.8.5.3 Table 1: default Unicode translations for ZSCII 155..223
DEFAULT_UNICODE_EXTRAS = ("äöüÄÖÜß»«ëïÿËÏáéíóúýÁÉÍÓÚÝàèìòùÀÈÌÒÙâêîôûÂÊÎÔÛåÅøØãñõÃÑÕæÆçÇþðÞÐ£œŒ¡¿")
FIRST_EXTRA_ZSCII = 155

ZSCII_NEWLINE = 13
ZCHAR_SHIFT_A1 = 4
ZCHAR_SHIFT_A2 = 5
ZCHAR_ESCAPE = 6            # in A2: next two z-chars form a 10-bit ZSCII code
ZCHAR_PAD = 5               # used to pad the final word (§3.7)
DICT_ZCHARS_V5 = 9          # §13.3: v4+ dictionary words hold 9 z-chars (6 bytes)


@dataclass
class Alphabets:
    """The three alphabets as ZSCII codes (26 each)."""
    a0: list[int]
    a1: list[int]
    a2: list[int]

    @classmethod
    def default(cls) -> "Alphabets":
        def codes(s: str) -> list[int]:
            return [ZSCII_NEWLINE if c == "\n" else ord(c) for c in s]
        return cls(codes(DEFAULT_A0), codes(DEFAULT_A1), codes(DEFAULT_A2))

    @classmethod
    def from_table(cls, table: bytes) -> "Alphabets":
        """§3.5.5 a 78-byte custom alphabet table (header 0x34)."""
        a = cls([table[i] for i in range(26)], [table[26 + i] for i in range(26)],
                [table[52 + i] for i in range(26)])
        a.a2[1] = ZSCII_NEWLINE   # §3.5.5.1: A2 z-char 7 is always newline
        return a

    def find(self, zscii: int) -> tuple[int, int] | None:
        """Return (alphabet number, z-char) that prints this ZSCII code."""
        for number, table in enumerate((self.a0, self.a1, self.a2)):
            for index, code in enumerate(table):
                if number == 2 and index < 2:
                    continue          # A2 positions 6/7 are escape/newline
                if code == zscii:
                    return number, index + 6
        return None


class UnicodeTable:
    """§3.8.5 mapping between ZSCII 155..251 and Unicode."""

    def __init__(self, extras: str = DEFAULT_UNICODE_EXTRAS):
        self.to_unicode = {FIRST_EXTRA_ZSCII + i: ch for i, ch in enumerate(extras)}
        self.to_zscii = {ch: code for code, ch in self.to_unicode.items()}

    def zscii_to_str(self, code: int) -> str:
        if code == ZSCII_NEWLINE:
            return "\n"
        if 32 <= code <= 126:
            return chr(code)
        if code in self.to_unicode:
            return self.to_unicode[code]
        if code == 0:
            return ""
        return "?"                  # §3.8.5.4.3: no letter-form -> '?'

    def char_to_zscii(self, ch: str) -> int | None:
        if ch == "\n":
            return ZSCII_NEWLINE
        if 32 <= ord(ch) <= 126:
            return ord(ch)
        return self.to_zscii.get(ch)


# ---------------------------------------------------------------------------
# Decoding
# ---------------------------------------------------------------------------
def unpack_zchars(read_word, address: int) -> tuple[list[int], int]:
    """Read 16-bit words until one has its top bit set (§3.2).
    Returns (z-chars, address just after the string)."""
    zchars: list[int] = []
    while True:
        w = read_word(address)
        address += 2
        zchars += [(w >> 10) & 0x1F, (w >> 5) & 0x1F, w & 0x1F]
        if w & 0x8000:
            return zchars, address


def decode_zchars(zchars: list[int], alphabets: Alphabets, unicode: UnicodeTable,
                  abbreviation=None) -> str:
    """Turn a list of z-chars into text.

    `abbreviation(index)` returns the decoded text of abbreviation `index`
    (0..95) or is None when abbreviations are not allowed (inside an
    abbreviation, §3.3.1 - they must not nest).
    """
    out: list[str] = []
    alphabet = 0            # v5: shifts last for ONE character (§3.2.3)
    i = 0
    while i < len(zchars):
        z = zchars[i]
        if alphabet == 2 and z == ZCHAR_ESCAPE:
            # §3.4 10-bit ZSCII: next two z-chars are the top and bottom 5 bits
            if i + 2 < len(zchars):
                code = (zchars[i + 1] << 5) | zchars[i + 2]
                out.append(unicode.zscii_to_str(code))
            i += 3
            alphabet = 0
            continue
        if z == 0:
            out.append(" ")
        elif z in (1, 2, 3):
            if i + 1 < len(zchars) and abbreviation is not None:
                out.append(abbreviation(32 * (z - 1) + zchars[i + 1]))   # §3.3
            i += 2
            alphabet = 0
            continue
        elif z == ZCHAR_SHIFT_A1:
            alphabet = 1
            i += 1
            continue
        elif z == ZCHAR_SHIFT_A2:
            alphabet = 2
            i += 1
            continue
        else:
            table = (alphabets.a0, alphabets.a1, alphabets.a2)[alphabet]
            out.append(unicode.zscii_to_str(table[z - 6]))
        alphabet = 0
        i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# Encoding (used by the assembler, the compiler, @encode_text and @tokenise)
# ---------------------------------------------------------------------------
def zscii_to_zchars(code: int, alphabets: Alphabets) -> list[int]:
    """The z-chars that print ONE ZSCII character."""
    if code == 32:
        return [0]
    found = alphabets.find(code)
    if found is not None:
        number, zchar = found
        if number == 0:
            return [zchar]
        return [ZCHAR_SHIFT_A1 if number == 1 else ZCHAR_SHIFT_A2, zchar]
    if code == ZSCII_NEWLINE:
        return [ZCHAR_SHIFT_A2, 7]
    # §3.4 10-bit escape: shift to A2, z-char 6, then high 5 bits, low 5 bits
    return [ZCHAR_SHIFT_A2, ZCHAR_ESCAPE, (code >> 5) & 0x1F, code & 0x1F]


def text_to_zscii(text: str, unicode: UnicodeTable) -> list[int]:
    codes = []
    for ch in text:
        code = unicode.char_to_zscii(ch)
        codes.append(code if code is not None else ord("?"))
    return codes


def pack_zchars(zchars: list[int]) -> bytes:
    """Pack z-chars three to a word, padding with 5s and setting the end bit."""
    zchars = list(zchars) or [ZCHAR_PAD]
    while len(zchars) % 3:
        zchars.append(ZCHAR_PAD)
    out = bytearray()
    for i in range(0, len(zchars), 3):
        w = (zchars[i] << 10) | (zchars[i + 1] << 5) | zchars[i + 2]
        if i + 3 == len(zchars):
            w |= 0x8000
        out += bytes([(w >> 8) & 0xFF, w & 0xFF])
    return bytes(out)


def encode_string(text: str, alphabets: Alphabets | None = None,
                  unicode: UnicodeTable | None = None) -> bytes:
    """Encode any text as a complete z-string (no abbreviations used)."""
    alphabets = alphabets or Alphabets.default()
    unicode = unicode or UnicodeTable()
    zchars: list[int] = []
    for code in text_to_zscii(text, unicode):
        zchars += zscii_to_zchars(code, alphabets)
    return pack_zchars(zchars)


def encode_dictionary_word(zscii_codes: list[int], alphabets: Alphabets | None = None,
                           nzchars: int = DICT_ZCHARS_V5) -> bytes:
    """§13.3 / §15 encode_text: a word as exactly `nzchars` z-chars (6 bytes
    in v5), truncated or padded with 5s; the end bit is on the last word.
    Input is lower-cased ZSCII (the caller lower-cases)."""
    alphabets = alphabets or Alphabets.default()
    zchars: list[int] = []
    for code in zscii_codes:
        zchars += zscii_to_zchars(code, alphabets)
    zchars = (zchars + [ZCHAR_PAD] * nzchars)[:nzchars]
    return pack_zchars(zchars)
