"""§3: Z-string encoding/decoding round-trips, including A2 escapes and the
default Unicode table."""
import random

from zforge.common.text import (Alphabets, UnicodeTable, decode_zchars, encode_dictionary_word,
                                encode_string, text_to_zscii, unpack_zchars)


def decode(data: bytes) -> str:
    words = lambda a: (data[a] << 8) | data[a + 1]
    zchars, end = unpack_zchars(words, 0)
    assert end == len(data)
    return decode_zchars(zchars, Alphabets.default(), UnicodeTable(), None)


def test_round_trip_simple_and_tricky():
    for text in ["", "a", "Hello, world!", "line\nbreak", "@{}~ tilde", "Grüße, é à"]:
        assert decode(encode_string(text)) == text


def test_round_trip_random_printable():
    rng = random.Random(5)
    alphabet = [chr(c) for c in range(32, 127)] + list("\näöüßé")
    for _ in range(200):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        assert decode(encode_string(text)) == text


def test_dictionary_word_is_6_bytes_9_zchars_padded():
    # §3.7: v4+ dictionary words are 9 z-chars; pad with 5s, end bit on the last word
    w = encode_dictionary_word(text_to_zscii("lamp", UnicodeTable()))
    assert len(w) == 6 and w[4] & 0x80
    long = encode_dictionary_word(text_to_zscii("abcdefghijkl", UnicodeTable()))
    short = encode_dictionary_word(text_to_zscii("abcdefghi", UnicodeTable()))
    assert long == short                    # truncated to 9 z-chars


def test_default_unicode_table_edges():
    u = UnicodeTable()
    assert u.zscii_to_str(155) == "ä" and u.zscii_to_str(223) == "¿"
    assert u.char_to_zscii("ä") == 155
