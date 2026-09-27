"""§15 input opcodes: aread (read), read_char, tokenise, encode_text,
input_stream. Tokenising itself is in vm/lexer.py (§13)."""
from __future__ import annotations

from zforge.common.text import encode_dictionary_word
from zforge.vm.lexer import Dictionary, tokenise
from zforge.vm.screen.base import KEY_NEWLINE


def op_aread(vm, text_buffer, parse_buffer=0, time=0, routine=0):
    """§15 read / aread (VAR:228, v5 form):

      text buffer:  byte 0 = max chars, byte 1 = chars typed, text from byte 2
                    (lower-cased, NO terminator stored)
      parse buffer: if non-zero, tokenised like @tokenise (§13)
      result:       the terminating character (13 for Enter)

    Timed input (time/routine) is not advertised in Flags 1, so we ignore it.
    """
    # Read the buffer format: max chars and chars already present
    max_chars = vm.mem.read_byte(text_buffer)
    already = vm.mem.read_byte(text_buffer + 1)      # v5: chars left from before
    text = vm.screen.read_line(max_chars - already)
    vm.streams.echo_input(text)
    codes = [c for c in vm.to_zscii(text.lower()) if c != ord("?") or "?" in text]
    codes = codes[:max_chars - already]
    # Store the characters in the buffer after the existing text
    for i, code in enumerate(codes):
        vm.mem.write_byte(text_buffer + 2 + already + i, code)
    vm.mem.write_byte(text_buffer + 1, already + len(codes))
    # If a parse buffer was given, tokenise the text into it
    if parse_buffer:
        tokenise(vm.mem, vm.alphabets, text_buffer, parse_buffer, vm.dictionary)
    vm.store_result(KEY_NEWLINE)


def op_read_char(vm, device=1, time=0, routine=0):
    """§15 read_char (VAR:246): wait for one key, store its ZSCII code."""
    vm.store_result(vm.screen.read_key())


def op_tokenise(vm, text_buffer, parse_buffer, dictionary=0, flag=0):
    """§15 tokenise (VAR:251): lexically analyse text into parse_buffer,
    using the main dictionary or the one at `dictionary`. If flag is set,
    unrecognised words leave their parse-buffer slots untouched."""
    dic = Dictionary.load(vm.mem, dictionary) if dictionary else vm.dictionary
    tokenise(vm.mem, vm.alphabets, text_buffer, parse_buffer, dic, skip_unknown=bool(flag))


def op_encode_text(vm, zscii_text, length, start, coded_text):
    """§15 encode_text (VAR:252): dictionary-encode `length` chars of
    zscii_text (from `start`) into 6 bytes at coded_text."""
    codes = [vm.mem.read_byte(zscii_text + start + i) for i in range(length)]
    for i, b in enumerate(encode_dictionary_word(codes, vm.alphabets)):
        vm.mem.write_byte(coded_text + i, b)


def op_input_stream(vm, number):
    """§15 input_stream (VAR:244): 0 = keyboard, 1 = command file.
    zforge takes command files via `--script` instead, so this is a no-op."""
    vm.warn("input_stream ignored (use --script)")
